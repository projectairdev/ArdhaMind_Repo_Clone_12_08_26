/**
 * ArdhaMind Frontend Lint Rule: Plausible Market Data Fallback Scanner
 * 
 * Intent:
 * "fallback values must never be plausible market data — always null/undefined so the UI can render an explicit awaiting-data state."
 * 
 * Flags for review any `??` or `||` fallback whose right-hand side is a numeric,
 * date, or percentage literal that looks like plausible market data.
 * 
 * Exits with code 0 by default (flags for review rather than auto-failing),
 * or non-zero when run with --strict.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import ts from 'typescript';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SRC_DIR = path.resolve(__dirname, '../src');
const STRICT_MODE = process.argv.includes('--strict');

// Patterns for plausible market data strings
const DATE_PATTERN = /^\d{4}[-/]\d{2}[-/]\d{2}|\b\d{2}[-/]\d{2}[-/]\d{4}\b/;
const PERCENT_PATTERN = /^[+-]?\d+(?:\.\d+)?%/;
const FORMATTED_PRICE_PATTERN = /^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$/;
const DECIMAL_NUM_STRING_PATTERN = /^[+-]?\d+\.\d+$/;
const COMPOSITE_MARKET_STRING_PATTERN = /[+-]?\d+(?:\.\d+)?\s*\([+-]?\d+(?:\.\d+)?%\)/; // e.g. "+68.20 (+0.28%)"

interface FlaggedIssue {
  file: string;
  line: number;
  col: number;
  operator: string;
  rhsCode: string;
  fullSnippet: string;
  reason: string;
}

function isPlausibleMarketDataNumeric(val: number): { isMarketData: boolean; reason?: string } {
  // Integers that are 0, 1, -1, or typical UI bounds (e.g. index 0, length 0, 2, etc.) might be UI constants,
  // but let's check for market index levels (e.g. >= 100 strikes/spots like 24000, 24300, 24180, 24520)
  // or floating point / decimals (e.g. 24080.40, 10.68, 0.48, 68.20, 24287.65)
  if (!Number.isInteger(val)) {
    return {
      isMarketData: true,
      reason: `Decimal float numeric literal (${val}) looks like market price/percentage/ratio`
    };
  }

  // Strike prices / Nifty spot prices / OI counts >= 100
  if (val >= 100 || val <= -100) {
    return {
      isMarketData: true,
      reason: `Large numeric literal (${val}) looks like plausible spot/strike/level/count`
    };
  }

  return { isMarketData: false };
}

function isPlausibleMarketDataString(str: string): { isMarketData: boolean; reason?: string } {
  const trimmed = str.trim();
  if (!trimmed) return { isMarketData: false };

  if (DATE_PATTERN.test(trimmed)) {
    return { isMarketData: true, reason: `Date literal string ("${trimmed}")` };
  }

  if (PERCENT_PATTERN.test(trimmed)) {
    return { isMarketData: true, reason: `Percentage literal string ("${trimmed}")` };
  }

  if (COMPOSITE_MARKET_STRING_PATTERN.test(trimmed)) {
    return { isMarketData: true, reason: `Composite price/change string ("${trimmed}")` };
  }

  if (FORMATTED_PRICE_PATTERN.test(trimmed)) {
    return { isMarketData: true, reason: `Formatted currency/price string ("${trimmed}")` };
  }

  if (DECIMAL_NUM_STRING_PATTERN.test(trimmed)) {
    return { isMarketData: true, reason: `Decimal numeric string ("${trimmed}")` };
  }

  // Check if string is a numeric strike like "24000", "24500"
  const parsed = Number(trimmed.replace(/,/g, ''));
  if (!isNaN(parsed) && (parsed >= 100 || !Number.isInteger(parsed))) {
    return { isMarketData: true, reason: `Numeric string resembling market data ("${trimmed}")` };
  }

  return { isMarketData: false };
}

function evaluateRhsNode(node: ts.Node, sourceFile: ts.SourceFile): { isMarketData: boolean; reason?: string } {
  // Numeric literal
  if (ts.isNumericLiteral(node)) {
    const numVal = parseFloat(node.text);
    return isPlausibleMarketDataNumeric(numVal);
  }

  // Negative numeric literal (e.g. -10.5)
  if (ts.isPrefixUnaryExpression(node) && node.operator === ts.SyntaxKind.MinusToken && ts.isNumericLiteral(node.operand)) {
    const numVal = -parseFloat((node.operand as ts.NumericLiteral).text);
    return isPlausibleMarketDataNumeric(numVal);
  }

  // String literal
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
    return isPlausibleMarketDataString(node.text);
  }

  // Template expression, e.g. `${...} (+0.28%)` or containing static string parts that look like market data
  if (ts.isTemplateExpression(node)) {
    const headText = node.head.text;
    const checkHead = isPlausibleMarketDataString(headText);
    if (checkHead.isMarketData) return checkHead;

    for (const span of node.templateSpans) {
      const spanText = span.literal.text;
      const checkSpan = isPlausibleMarketDataString(spanText);
      if (checkSpan.isMarketData) return checkSpan;
    }
  }

  return { isMarketData: false };
}

function scanFile(filePath: string): FlaggedIssue[] {
  const content = fs.readFileSync(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(
    filePath,
    content,
    ts.ScriptTarget.Latest,
    true
  );

  const issues: FlaggedIssue[] = [];

  function visit(node: ts.Node) {
    if (ts.isBinaryExpression(node)) {
      const op = node.operatorToken;
      const isNullish = op.kind === ts.SyntaxKind.QuestionQuestionToken;
      const isOr = op.kind === ts.SyntaxKind.BarBarToken;

      if (isNullish || isOr) {
        const opSymbol = isNullish ? '??' : '||';
        const evaluation = evaluateRhsNode(node.right, sourceFile);

        if (evaluation.isMarketData) {
          const { line, character } = sourceFile.getLineAndCharacterOfPosition(op.getStart(sourceFile));
          const fullSnippet = node.getText(sourceFile);
          const rhsCode = node.right.getText(sourceFile);

          issues.push({
            file: path.relative(path.resolve(__dirname, '..'), filePath),
            line: line + 1,
            col: character + 1,
            operator: opSymbol,
            rhsCode,
            fullSnippet: fullSnippet.length > 80 ? fullSnippet.substring(0, 77) + '...' : fullSnippet,
            reason: evaluation.reason || 'Plausible market data fallback'
          });
        }
      }
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return issues;
}

function getAllSourceFiles(dir: string): string[] {
  let files: string[] = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== 'node_modules' && entry.name !== 'dist' && entry.name !== '.git' && entry.name !== '__pycache__') {
        files = files.concat(getAllSourceFiles(fullPath));
      }
    } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx') || entry.name.endsWith('.js') || entry.name.endsWith('.jsx'))) {
      files.push(fullPath);
    }
  }

  return files;
}

function main() {
  console.log('='.repeat(80));
  console.log('ArdhaMind Frontend Code Review Linter: Market Data Fallback Scanner');
  console.log('Rule Intent: "fallback values must never be plausible market data — always null/undefined so the UI can render an explicit awaiting-data state."');
  console.log('='.repeat(80));

  const allFiles = getAllSourceFiles(SRC_DIR);
  const allIssues: FlaggedIssue[] = [];

  for (const file of allFiles) {
    const issues = scanFile(file);
    allIssues.push(...issues);
  }

  if (allIssues.length === 0) {
    console.log(`\n✅ Scan complete: 0 plausible market data fallbacks found across ${allFiles.length} source files.`);
    process.exit(0);
  }

  console.log(`\n🔍 Found ${allIssues.length} fallback expressions flagged for review across ${allFiles.length} source files:\n`);

  for (const issue of allIssues) {
    console.log(`⚠️  [REVIEW FLAGGED] ${issue.file}:${issue.line}:${issue.col}`);
    console.log(`   Expression: ${issue.fullSnippet}`);
    console.log(`   RHS Fallback: ${issue.rhsCode}`);
    console.log(`   Reason: ${issue.reason}`);
    console.log(`   Guidance: Replace with null/undefined or propagate awaiting-data state.\n`);
  }

  console.log('-'.repeat(80));
  console.log(`Summary: ${allIssues.length} items flagged for code review.`);
  console.log('Note: These are flagged for peer review rather than auto-blocking standard builds.');
  console.log('='.repeat(80));

  if (STRICT_MODE) {
    console.error(`\n❌ STRICT MODE ACTIVE: Exiting with non-zero code due to ${allIssues.length} flagged fallback(s).`);
    process.exit(1);
  } else {
    process.exit(0);
  }
}

main();
