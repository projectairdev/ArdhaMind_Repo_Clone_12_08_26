// src/frontend/components/TradingCheatsheetWorkspace.tsx
import React, { useState, useMemo, useEffect } from "react";
import {
  BookOpen,
  Info,
  Search,
  CheckCircle2,
  AlertTriangle,
  Compass,
  Layers,
  BarChart2,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  Zap,
  Globe,
  Sliders,
  RotateCcw,
  Sparkles,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  HelpCircle,
  X,
  Target,
  GraduationCap,
  Briefcase,
  Cpu
} from "lucide-react";
import {
  ExperienceLevel,
  UnifiedTradingConcept,
  UNIFIED_CORE_METRICS,
  UNIFIED_PRICE_OI_MATRIX,
  UNIFIED_PRICE_ACTION_CONCEPTS,
  UNIFIED_SCENARIO_LIBRARY,
  UNIFIED_TREND_VS_RANGE,
  UNIFIED_INDICATOR_COMBINATIONS,
  UNIFIED_GLOBAL_RELATIONSHIPS,
  UNIFIED_RISK_RULES,
  CanonicalScenarioInputState,
  BeginnerScenarioInputState,
  IntermediateScenarioInputState,
  AdaptiveScenarioResult,
  mapBeginnerToCanonical,
  mapIntermediateToCanonical,
  evaluateAdaptiveScenario,
  ADAPTIVE_SCENARIO_PRESETS,
  MetricInterpretationRange
} from "../data/tradingCheatsheet";
import { useNavigation } from "../context/NavigationContext";

type CategoryFilter =
  | "ALL"
  | "METRICS"
  | "OPTIONS"
  | "PRICE_ACTION"
  | "SCENARIOS"
  | "OPENING"
  | "INDICATORS"
  | "GLOBAL"
  | "RISK"
  | "EXPLORER";

const DEFAULT_BEGINNER_EXPLORER_STATE: BeginnerScenarioInputState = {
  participation: "STRONG",
  volatility: "CALM",
  priceDirection: "UP",
  banking: "STRONG"
};

const DEFAULT_INTERMEDIATE_EXPLORER_STATE: IntermediateScenarioInputState = {
  breadth: "STRONG_POSITIVE",
  vix: "FALLING",
  price: "BREAKING_RESISTANCE",
  bankNifty: "STRONG",
  pcr: "SUPPORTIVE",
  volume: "STRONG"
};

const DEFAULT_CANONICAL_EXPLORER_STATE: CanonicalScenarioInputState = {
  breadth: "STRONG_POSITIVE",
  vix: "FALLING",
  price: "BREAKING_RESISTANCE",
  bankNifty: "STRONG",
  pcr: "SUPPORTIVE",
  oi: "LONG_BUILDUP",
  volume: "STRONG",
  structure: "BREAKOUT"
};

export function TradingCheatsheetWorkspace() {
  // Experience Level (Default: BEGINNER, persisted locally in localStorage)
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>(() => {
    const saved = localStorage.getItem("trading_cheatsheet_experience_level");
    if (saved === "INTERMEDIATE" || saved === "ADVANCED") {
      return saved as ExperienceLevel;
    }
    return "BEGINNER";
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<CategoryFilter>("ALL");
  const [selectedMetricDetail, setSelectedMetricDetail] = useState<UnifiedTradingConcept | null>(null);

  // Scenario Explorer States by Level
  const [beginnerInputs, setBeginnerInputs] = useState<BeginnerScenarioInputState>(DEFAULT_BEGINNER_EXPLORER_STATE);
  const [intermediateInputs, setIntermediateInputs] = useState<IntermediateScenarioInputState>(DEFAULT_INTERMEDIATE_EXPLORER_STATE);
  const [advancedInputs, setAdvancedInputs] = useState<CanonicalScenarioInputState>(DEFAULT_CANONICAL_EXPLORER_STATE);
  const [activePreset, setActivePreset] = useState<string>("STRONG_BULLISH_TREND");

  // Handle Experience Level Change with Persistence
  const handleSelectExperienceLevel = (level: ExperienceLevel) => {
    setExperienceLevel(level);
    localStorage.setItem("trading_cheatsheet_experience_level", level);
  };

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedMetricDetail(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Compute Active Canonical Input State based on current Level
  const activeCanonicalInputState: CanonicalScenarioInputState = useMemo(() => {
    if (experienceLevel === "BEGINNER") {
      return mapBeginnerToCanonical(beginnerInputs);
    } else if (experienceLevel === "INTERMEDIATE") {
      return mapIntermediateToCanonical(intermediateInputs);
    }
    return advancedInputs;
  }, [experienceLevel, beginnerInputs, intermediateInputs, advancedInputs]);

  // Evaluate Active Scenario Rule Engine
  const scenarioResult: AdaptiveScenarioResult = useMemo(() => {
    return evaluateAdaptiveScenario(activeCanonicalInputState, experienceLevel);
  }, [activeCanonicalInputState, experienceLevel]);

  // Handle Presets
  const handleLoadPreset = (presetKey: string) => {
    setActivePreset(presetKey);
    const preset = ADAPTIVE_SCENARIO_PRESETS[presetKey];
    if (preset) {
      setBeginnerInputs(preset.beginnerState);
      setIntermediateInputs({
        breadth: preset.canonicalState.breadth,
        vix: preset.canonicalState.vix,
        price: preset.canonicalState.price as any,
        bankNifty: preset.canonicalState.bankNifty,
        pcr: preset.canonicalState.pcr,
        volume: preset.canonicalState.volume
      });
      setAdvancedInputs(preset.canonicalState);
    }
  };

  // Reset Explorer
  const handleResetExplorer = () => {
    setActivePreset("STRONG_BULLISH_TREND");
    setBeginnerInputs(DEFAULT_BEGINNER_EXPLORER_STATE);
    setIntermediateInputs(DEFAULT_INTERMEDIATE_EXPLORER_STATE);
    setAdvancedInputs(DEFAULT_CANONICAL_EXPLORER_STATE);
  };

  // Filtered metrics based on search
  const filteredMetrics = useMemo(() => {
    if (!searchQuery.trim()) return UNIFIED_CORE_METRICS;
    const q = searchQuery.toLowerCase();
    return UNIFIED_CORE_METRICS.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.canonicalDefinition.toLowerCase().includes(q) ||
        m.beginner.friendlySubtitle.toLowerCase().includes(q) ||
        m.beginner.simpleDefinition.toLowerCase().includes(q) ||
        m.category.toLowerCase().includes(q) ||
        (m.id === "india_vix" && (q.includes("fear") || q.includes("volatility"))) ||
        (m.id === "open_interest" && q.includes("oi"))
    );
  }, [searchQuery]);

  // Filtered scenarios based on search
  const filteredScenarios = useMemo(() => {
    if (!searchQuery.trim()) return UNIFIED_SCENARIO_LIBRARY;
    const q = searchQuery.toLowerCase();
    return UNIFIED_SCENARIO_LIBRARY.filter(
      (s) =>
        s.title.beginner.toLowerCase().includes(q) ||
        s.title.intermediate.toLowerCase().includes(q) ||
        s.title.advanced.toLowerCase().includes(q) ||
        s.meaning.beginner.toLowerCase().includes(q) ||
        s.conditions.beginner.some((c) => c.toLowerCase().includes(q))
    );
  }, [searchQuery]);

  return (
    <div className="space-y-4 pb-12 font-sans text-[#E6E8EB] max-w-[1600px] mx-auto">
      {/* 1. HEADER & EXPERIENCE LEVEL SELECTOR */}
      <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#191D23] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen size={18} className="text-[#00E5FF]" />
              <h1 className="text-sm sm:text-base font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                TRADING CHEATSHEET
              </h1>
              <span className="text-[9px] font-mono font-bold bg-[#00E5FF]/10 text-[#00E5FF] px-2 py-0.5 rounded border border-[#00E5FF]/30">
                GENERAL TRADING REFERENCE
              </span>
              <span className="text-[9px] font-mono font-bold bg-[#00C896]/10 text-[#00C896] px-2 py-0.5 rounded border border-[#00C896]/30 hidden sm:inline-block">
                3 EXPERIENCE LAYERS
              </span>
            </div>
            <p className="text-[11px] text-[#707987] font-mono mt-0.5">
              One canonical trading-knowledge base • Tailored for Beginners, Intermediate Traders &amp; Advanced Analysts.
            </p>
          </div>

          {/* Prominent Experience Level Selector */}
          <div className="flex flex-col items-start sm:items-end gap-1 font-mono">
            <span className="text-[9px] text-[#707987] font-bold uppercase tracking-wider">EXPERIENCE LEVEL</span>
            <div className="flex items-center bg-[#08090B] p-1 rounded border border-[#22272E] gap-1">
              <button
                onClick={() => handleSelectExperienceLevel("BEGINNER")}
                className={`flex items-center gap-1 px-3 py-1 rounded text-[10px] font-bold transition-colors ${
                  experienceLevel === "BEGINNER"
                    ? "bg-[#00E5FF] text-black shadow-sm"
                    : "text-[#707987] hover:text-[#E6E8EB] hover:bg-[#13161A]"
                }`}
              >
                <GraduationCap size={13} />
                <span>BEGINNER</span>
              </button>
              <button
                onClick={() => handleSelectExperienceLevel("INTERMEDIATE")}
                className={`flex items-center gap-1 px-3 py-1 rounded text-[10px] font-bold transition-colors ${
                  experienceLevel === "INTERMEDIATE"
                    ? "bg-[#00C896] text-black shadow-sm"
                    : "text-[#707987] hover:text-[#E6E8EB] hover:bg-[#13161A]"
                }`}
              >
                <Briefcase size={13} />
                <span>INTERMEDIATE</span>
              </button>
              <button
                onClick={() => handleSelectExperienceLevel("ADVANCED")}
                className={`flex items-center gap-1 px-3 py-1 rounded text-[10px] font-bold transition-colors ${
                  experienceLevel === "ADVANCED"
                    ? "bg-[#8B5CF6] text-white shadow-sm"
                    : "text-[#707987] hover:text-[#E6E8EB] hover:bg-[#13161A]"
                }`}
              >
                <Cpu size={13} />
                <span>ADVANCED</span>
              </button>
            </div>
          </div>
        </div>

        {/* Experience Mode Banner Subtitle */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono py-0.5">
          <div className="flex items-center gap-2">
            <span className="text-[#00E5FF] font-bold uppercase">
              {experienceLevel === "BEGINNER" && "BEGINNER MODE:"}
              {experienceLevel === "INTERMEDIATE" && "INTERMEDIATE MODE:"}
              {experienceLevel === "ADVANCED" && "ADVANCED MODE:"}
            </span>
            <span className="text-[#A5ABB4]">
              {experienceLevel === "BEGINNER" && "Learn the language of markets • Simple explanations • Round examples • Minimal jargon."}
              {experienceLevel === "INTERMEDIATE" && "Understand market relationships • Technical indicators • Confirmations • Scenarios."}
              {experienceLevel === "ADVANCED" && "Analyze mechanics & structure • Derivatives open interest • Volatility regimes • Multi-factor confluence."}
            </span>
          </div>
          <span className="text-[9px] text-[#FFB020] bg-[#FFB020]/10 px-2 py-0.5 rounded border border-[#FFB020]/30 flex items-center gap-1">
            <Shield size={11} />
            <span>Offline-Ready • 0 Live Feeds Required</span>
          </span>
        </div>

        {/* Search Bar & Category Navigation Chips */}
        <div className="flex flex-wrap items-center justify-between gap-2.5 pt-1 border-t border-[#191D23]">
          <div className="relative flex-1 min-w-[240px] max-w-[380px]">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#707987]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={experienceLevel === "BEGINNER" ? "Search 'fear', 'VWAP', 'support'..." : "Search 'VIX', 'PCR', 'Breakout', 'OI'..."}
              className="w-full bg-[#13161A] border border-[#22272E] rounded-[3px] pl-8 pr-3 py-1 text-xs font-mono text-[#E6E8EB] placeholder-[#505763] focus:border-[#00E5FF] focus:outline-none transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#707987] hover:text-white"
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
            {[
              { id: "ALL", label: "ALL" },
              { id: "METRICS", label: experienceLevel === "BEGINNER" ? "CORE CONCEPTS" : "METRICS" },
              { id: "OPTIONS", label: experienceLevel === "BEGINNER" ? "OPTIONS & OI" : "OPTIONS & OI" },
              { id: "PRICE_ACTION", label: experienceLevel === "BEGINNER" ? "CHART PATTERNS" : "PRICE ACTION" },
              { id: "SCENARIOS", label: experienceLevel === "BEGINNER" ? "MARKET MOVES" : "SCENARIO LIBRARY" },
              { id: "INDICATORS", label: experienceLevel === "BEGINNER" ? "INDICATOR COMBOS" : "INDICATORS" },
              { id: "RISK", label: "RISK RULES" },
              { id: "EXPLORER", label: experienceLevel === "BEGINNER" ? "MARKET EXPLORER" : "SCENARIO EXPLORER" }
            ].map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id as CategoryFilter)}
                className={`px-2 py-1 rounded-[2px] font-bold transition-colors ${
                  activeCategory === cat.id
                    ? "bg-[#00E5FF] text-black"
                    : "bg-[#13161A] text-[#707987] hover:text-[#E6E8EB] hover:bg-[#191D23] border border-[#22272E]"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. SECTION 1: CORE MARKET CONCEPTS / METRICS */}
      {(activeCategory === "ALL" || activeCategory === "METRICS") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <Activity size={15} className="text-[#00E5FF]" />
              <h2 className="text-xs font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                {experienceLevel === "BEGINNER" ? "1. HOW TO READ THE MARKET (CORE CONCEPTS)" : "1. CORE MARKET METRICS"}
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#707987]">
              Click ⓘ Detail on any card for full breakdown
            </span>
          </div>

          {/* BEGINNER VIEW: Grouped in 4 Intuitive Clusters */}
          {experienceLevel === "BEGINNER" ? (
            <div className="space-y-4">
              {[
                { title: "HOW THE MARKET FEELS", group: "FEELS", icon: HeartIcon },
                { title: "HOW PRICE IS MOVING", group: "MOVING", icon: TrendingUp },
                { title: "HOW OPTIONS POSITION", group: "OPTIONS", icon: Target },
                { title: "HOW STRONG THE MOVE IS", group: "STRENGTH", icon: Activity }
              ].map((grp) => {
                const groupMetrics = filteredMetrics.filter((m) => m.beginnerGroup === grp.group);
                if (groupMetrics.length === 0) return null;
                return (
                  <div key={grp.group} className="space-y-2">
                    <div className="text-[11px] font-mono font-bold text-[#00E5FF] uppercase flex items-center gap-1.5 border-b border-[#1E232B] pb-1">
                      <span>{grp.title}</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {groupMetrics.map((m) => (
                        <div
                          key={m.id}
                          className="bg-[#13161A] border border-[#22272E] rounded-[4px] p-3 space-y-2.5 hover:border-[#00E5FF]/40 transition-colors flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between border-b border-[#1E232B] pb-1.5">
                              <div>
                                <span className="text-xs font-bold text-[#E6E8EB] font-mono">{m.beginner.shortLabel}</span>
                                <div className="text-[10px] text-[#00E5FF] font-mono italic">{m.beginner.friendlySubtitle}</div>
                              </div>
                              <button
                                onClick={() => setSelectedMetricDetail(m)}
                                className="text-[#00E5FF] hover:text-white p-1 rounded hover:bg-[#00E5FF]/20 transition-colors flex items-center gap-1 text-[10px] font-mono shrink-0"
                              >
                                <Info size={13} />
                                <span>Learn More</span>
                              </button>
                            </div>

                            <p className="text-[11px] text-[#A5ABB4] font-mono mt-2 leading-relaxed">
                              {m.beginner.simpleDefinition}
                            </p>

                            {/* Simple States */}
                            <div className="mt-2.5 space-y-1 bg-[#0E1013] p-2 rounded border border-[#191D23]">
                              {m.beginner.simpleStates.map((st, si) => (
                                <div key={si} className="text-[10px] font-mono space-y-0.5">
                                  <div className="font-bold text-[#00C896] flex items-center justify-between">
                                    <span>{st.label}</span>
                                    {st.rangeText && <span className="text-[#707987] text-[9px]">{st.rangeText}</span>}
                                  </div>
                                  <p className="text-[#8E95A2] text-[9px] leading-tight">{st.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="pt-2 border-t border-[#1E232B] space-y-1.5 text-[10px] font-mono">
                            <div className="text-[#E6E8EB] bg-[#191D23] p-1.5 rounded text-[9px] leading-tight">
                              <strong className="text-[#FFB020]">EXAMPLE: </strong>
                              {m.beginner.simpleExample.replace("EXAMPLE: ", "")}
                            </div>
                            <div className="text-[#00C896] text-[9px] leading-tight">
                              <strong>REMEMBER: </strong>
                              {m.beginner.rememberThis.replace("REMEMBER: ", "")}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* INTERMEDIATE & ADVANCED VIEW: Compact Professional Grid */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {filteredMetrics.map((m) => (
                <div
                  key={m.id}
                  className="bg-[#13161A] border border-[#22272E] rounded-[3px] p-2.5 space-y-2 hover:border-[#00E5FF]/40 transition-colors flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between border-b border-[#1E232B] pb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-[#E6E8EB] font-mono">{m.name}</span>
                        <span className="text-[8px] font-mono text-[#707987] bg-[#191D23] px-1.5 py-0.5 rounded">
                          {m.category}
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedMetricDetail(m)}
                        className="text-[#00E5FF] hover:text-white p-0.5 rounded hover:bg-[#00E5FF]/20 transition-colors flex items-center gap-0.5 text-[10px] font-mono"
                      >
                        <Info size={13} />
                        <span className="text-[9px]">Detail</span>
                      </button>
                    </div>

                    <p className="text-[10px] text-[#A5ABB4] font-mono mt-1.5 leading-relaxed">
                      {experienceLevel === "INTERMEDIATE" ? m.intermediate.definition : m.canonicalDefinition}
                    </p>

                    {/* Ranges Table */}
                    <div className="mt-2 space-y-1">
                      <div className="text-[9px] font-mono font-bold text-[#707987] uppercase">
                        {experienceLevel === "ADVANCED" ? "Regime Breakdown:" : "Common Reference Ranges:"}
                      </div>
                      <div className="space-y-0.5 font-mono text-[9px]">
                        {experienceLevel === "ADVANCED"
                          ? m.advanced.detailedRanges.slice(0, 3).map((r, i) => (
                              <div key={i} className="flex items-start justify-between gap-1 py-0.5 border-b border-[#191D23]/50">
                                <span className="font-bold text-[#00E5FF] shrink-0 w-[70px]">{r.range}</span>
                                <span className="text-[#A5ABB4] flex-1 text-right">{r.regimeContext}</span>
                              </div>
                            ))
                          : m.intermediate.ranges.slice(0, 4).map((r, i) => (
                              <div key={i} className="flex items-start justify-between gap-1 py-0.5 border-b border-[#191D23]/50">
                                <span className="font-bold text-[#E6E8EB] shrink-0 w-[75px]">{r.range}</span>
                                <span className="text-[#8E95A2] flex-1 text-right">{r.label}</span>
                              </div>
                            ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-[#1E232B] space-y-1 text-[9px] font-mono">
                    <div className="text-[#00C896]">
                      <strong>Takeaway:</strong> {m.intermediate.traderTakeaway}
                    </div>
                    <div className="text-[#E5484D]">
                      <strong>Mistake:</strong> {m.intermediate.commonMistake}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. SECTION 2: PRICE VS OPEN INTEREST (OI) MATRIX */}
      {(activeCategory === "ALL" || activeCategory === "OPTIONS") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <BarChart2 size={15} className="text-[#00E5FF]" />
              <h2 className="text-xs font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                2. PRICE VS OPEN INTEREST (OI) MATRIX
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#00C896]">4 Core Institutional Regimes</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-[10px] font-mono border-collapse">
              <thead>
                <tr className="bg-[#13161A] text-[#707987] uppercase border-b border-[#1E232B]">
                  <th className="p-2 text-left">Condition</th>
                  <th className="p-2 text-left">Regime Label</th>
                  <th className="p-2 text-left">Interpretation</th>
                  <th className="p-2 text-left">Trader Warning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#191D23]">
                {UNIFIED_PRICE_OI_MATRIX.map((row, i) => (
                  <tr key={i} className="hover:bg-[#13161A]/60 transition-colors">
                    <td className="p-2 font-bold text-[#E6E8EB] whitespace-nowrap">
                      <span className={row.priceDirection.includes("↑") ? "text-[#00C896]" : "text-[#E5484D]"}>
                        {row.priceDirection}
                      </span>
                      {" + "}
                      <span className={row.oiDirection.includes("↑") ? "text-[#00E5FF]" : "text-[#FFB020]"}>
                        {row.oiDirection}
                      </span>
                    </td>
                    <td className="p-2 font-extrabold whitespace-nowrap">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] ${
                          row.tone === "BULLISH"
                            ? "bg-[#00C896]/10 text-[#00C896] border border-[#00C896]/30"
                            : row.tone === "BEARISH"
                            ? "bg-[#E5484D]/10 text-[#E5484D] border border-[#E5484D]/30"
                            : "bg-[#FFB020]/10 text-[#FFB020] border border-[#FFB020]/30"
                        }`}
                      >
                        {experienceLevel === "BEGINNER" ? row.beginnerLabel : row.label}
                      </span>
                    </td>
                    <td className="p-2 text-[#A5ABB4] leading-tight">
                      {experienceLevel === "BEGINNER"
                        ? row.beginnerExplanation
                        : experienceLevel === "ADVANCED"
                        ? row.advancedMechanics
                        : row.intermediateInterpretation}
                    </td>
                    <td className="p-2 text-[#707987] leading-tight">{row.warning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. SECTION 3: PRICE ACTION PATTERNS */}
      {(activeCategory === "ALL" || activeCategory === "PRICE_ACTION") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp size={15} className="text-[#00C896]" />
              <h2 className="text-xs font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                3. PRICE ACTION PATTERNS &amp; STRUCTURAL BASICS
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#00C896]">Confluence &gt; Isolated Candlesticks</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {UNIFIED_PRICE_ACTION_CONCEPTS.map((p) => (
              <div key={p.id} className="bg-[#13161A] border border-[#22272E] rounded-[3px] p-2.5 space-y-1.5 font-mono text-[10px]">
                <div className="flex items-center justify-between border-b border-[#1E232B] pb-1">
                  <span className="font-bold text-[#E6E8EB]">{experienceLevel === "BEGINNER" ? p.beginnerTitle : p.title}</span>
                  <span
                    className={`px-1 py-0.5 rounded text-[8px] font-bold ${
                      p.tone === "BULLISH"
                        ? "text-[#00C896] bg-[#00C896]/10"
                        : p.tone === "BEARISH"
                        ? "text-[#E5484D] bg-[#E5484D]/10"
                        : "text-[#FFB020] bg-[#FFB020]/10"
                    }`}
                  >
                    {p.tone}
                  </span>
                </div>
                <p className="text-[#A5ABB4] leading-tight">
                  {experienceLevel === "BEGINNER" ? p.beginnerDescription : p.whatItIs}
                </p>
                <div className="text-[#00C896] text-[9px]">
                  <strong>Confirms:</strong> {p.whatConfirms}
                </div>
                <div className="text-[#E5484D] text-[9px]">
                  <strong>Invalidates:</strong> {p.whatInvalidates}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. SECTION 4: SCENARIO LIBRARY */}
      {(activeCategory === "ALL" || activeCategory === "SCENARIOS") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <Compass size={15} className="text-[#00E5FF]" />
              <h2 className="text-xs font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                4. SCENARIO LIBRARY (MARKET MOVES &amp; TRAPS)
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#00E5FF]">If Condition $\to$ Then Conclusion</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {filteredScenarios.map((scen) => (
              <div
                key={scen.id}
                className="bg-[#13161A] border border-[#22272E] rounded-[3px] p-2.5 space-y-2 font-mono text-[10px] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between border-b border-[#1E232B] pb-1.5">
                    <span className="font-bold text-[#E6E8EB]">
                      {experienceLevel === "BEGINNER"
                        ? scen.title.beginner
                        : experienceLevel === "ADVANCED"
                        ? scen.title.advanced
                        : scen.title.intermediate}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                        scen.tone === "BULLISH"
                          ? "bg-[#00C896]/10 text-[#00C896] border border-[#00C896]/30"
                          : scen.tone === "BEARISH"
                          ? "bg-[#E5484D]/10 text-[#E5484D] border border-[#E5484D]/30"
                          : scen.tone === "RANGE"
                          ? "bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/30"
                          : "bg-[#FFB020]/10 text-[#FFB020] border border-[#FFB020]/30"
                      }`}
                    >
                      {scen.confidenceBand}
                    </span>
                  </div>

                  <div className="space-y-0.5 text-[9px] mt-1.5">
                    <span className="text-[#707987] font-bold">{experienceLevel === "BEGINNER" ? "LOOK FOR:" : "IF:"}</span>
                    <ul className="list-disc list-inside text-[#A5ABB4] space-y-0.5 pl-1">
                      {(experienceLevel === "BEGINNER" ? scen.conditions.beginner : experienceLevel === "ADVANCED" ? scen.conditions.advanced : scen.conditions.intermediate).map((cond, ci) => (
                        <li key={ci} className="leading-tight">
                          {cond}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="space-y-1 pt-2 border-t border-[#1E232B]">
                  <div className="p-1.5 rounded bg-[#0E1013] border border-[#191D23] text-[9px]">
                    <span className="text-[#00E5FF] font-bold">{experienceLevel === "BEGINNER" ? "MEANING: " : "THEN: "}</span>
                    <span className="text-[#E6E8EB]">
                      {experienceLevel === "BEGINNER" ? scen.meaning.beginner : experienceLevel === "ADVANCED" ? scen.meaning.advanced : scen.meaning.intermediate}
                    </span>
                  </div>
                  <div className="text-[8px] text-[#E5484D]">
                    <strong>{experienceLevel === "BEGINNER" ? "WHAT WOULD CHANGE THIS? " : "Invalidation: "}</strong>
                    {experienceLevel === "BEGINNER" ? scen.invalidation.beginner : experienceLevel === "ADVANCED" ? scen.invalidation.advanced : scen.invalidation.intermediate}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. SECTION 5: RISK MANAGEMENT RULES */}
      {(activeCategory === "ALL" || activeCategory === "RISK") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-2.5 font-mono text-[10px]">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-1.5">
              <Shield size={14} className="text-[#00C896]" />
              <h3 className="text-xs font-bold text-[#E6E8EB] uppercase">
                5. CORE RISK MANAGEMENT PRINCIPLES
              </h3>
            </div>
            <span className="text-[10px] text-[#00C896]">Capital Preservation First</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {UNIFIED_RISK_RULES.map((r) => (
              <div key={r.id} className="p-2.5 rounded bg-[#13161A] border border-[#1E232B] space-y-1.5">
                <div className="font-bold text-[#00C896] text-[10px]">{r.title}</div>
                <p className="text-[#E6E8EB] text-[9px] leading-relaxed">
                  {experienceLevel === "BEGINNER" ? r.beginnerRule : experienceLevel === "ADVANCED" ? r.advancedRule : r.intermediateRule}
                </p>
                <div className="text-[#707987] text-[8px] bg-[#0E1013] p-1.5 rounded">
                  {r.example}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. SECTION 6: INTERACTIVE SCENARIO EXPLORER (ADAPTED TO 3 LEVELS) */}
      {(activeCategory === "ALL" || activeCategory === "EXPLORER") && (
        <div className="bg-[#0E1013] border border-[#191D23] rounded-[4px] p-3.5 space-y-3.5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#191D23] pb-2.5">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-[#00E5FF]" />
              <h2 className="text-xs font-extrabold text-[#E6E8EB] font-mono uppercase tracking-wider">
                6. &quot;IF X + Y + Z, THEN WHAT?&quot; SCENARIO EXPLORER ({experienceLevel})
              </h2>
            </div>
            <div className="flex items-center gap-2 font-mono text-[10px]">
              <span className="text-[#707987]">
                {experienceLevel === "BEGINNER" ? "4 Simple Market Controls" : experienceLevel === "INTERMEDIATE" ? "6 Indicator Controls" : "8 Institutional Controls"}
              </span>
              <button
                onClick={handleResetExplorer}
                className="px-2 py-0.5 rounded bg-[#191D23] hover:bg-[#22272E] text-[#00E5FF] border border-[#00E5FF]/30 transition-colors flex items-center gap-1"
              >
                <RotateCcw size={10} />
                <span>Reset</span>
              </button>
            </div>
          </div>

          {/* Presets Row */}
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[10px] bg-[#13161A] p-2 rounded border border-[#1E232B]">
            <span className="text-[#707987] font-bold uppercase mr-1">Educational Presets:</span>
            {Object.entries(ADAPTIVE_SCENARIO_PRESETS).map(([key, p]) => (
              <button
                key={key}
                onClick={() => handleLoadPreset(key)}
                className={`px-2 py-0.5 rounded text-[9px] transition-colors ${
                  activePreset === key
                    ? "bg-[#00E5FF] text-black font-bold"
                    : "bg-[#191D23] text-[#A5ABB4] hover:text-white border border-[#22272E]"
                }`}
              >
                {experienceLevel === "BEGINNER" ? p.name.beginner : experienceLevel === "ADVANCED" ? p.name.advanced : p.name.intermediate}
              </button>
            ))}
          </div>

          {/* INPUT SELECTORS: Adapted by Experience Level */}
          {experienceLevel === "BEGINNER" ? (
            /* BEGINNER: 4 Simplified Controls */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-[10px]">
              <div className="space-y-1 bg-[#13161A] p-2 rounded border border-[#22272E]">
                <label className="text-[9px] font-bold text-[#00E5FF] uppercase">1. MARKET PARTICIPATION</label>
                <select
                  value={beginnerInputs.participation}
                  onChange={(e) => {
                    setActivePreset("");
                    setBeginnerInputs({ ...beginnerInputs, participation: e.target.value as any });
                  }}
                  className="w-full bg-[#0E1013] border border-[#22272E] rounded px-2 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong (Most stocks 35+ rising)</option>
                  <option value="MIXED">Mixed (Half up, half down)</option>
                  <option value="WEAK">Weak (Most stocks falling)</option>
                </select>
              </div>

              <div className="space-y-1 bg-[#13161A] p-2 rounded border border-[#22272E]">
                <label className="text-[9px] font-bold text-[#00E5FF] uppercase">2. MARKET VOLATILITY</label>
                <select
                  value={beginnerInputs.volatility}
                  onChange={(e) => {
                    setActivePreset("");
                    setBeginnerInputs({ ...beginnerInputs, volatility: e.target.value as any });
                  }}
                  className="w-full bg-[#0E1013] border border-[#22272E] rounded px-2 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="CALM">Calm / Peaceful</option>
                  <option value="NORMAL">Normal Movements</option>
                  <option value="HIGH">High Nervousness / Wide Swings</option>
                </select>
              </div>

              <div className="space-y-1 bg-[#13161A] p-2 rounded border border-[#22272E]">
                <label className="text-[9px] font-bold text-[#00E5FF] uppercase">3. PRICE DIRECTION</label>
                <select
                  value={beginnerInputs.priceDirection}
                  onChange={(e) => {
                    setActivePreset("");
                    setBeginnerInputs({ ...beginnerInputs, priceDirection: e.target.value as any });
                  }}
                  className="w-full bg-[#0E1013] border border-[#22272E] rounded px-2 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="UP">Going Up (Above Average)</option>
                  <option value="SIDEWAYS">Sideways (Near Average)</option>
                  <option value="DOWN">Going Down (Below Average)</option>
                </select>
              </div>

              <div className="space-y-1 bg-[#13161A] p-2 rounded border border-[#22272E]">
                <label className="text-[9px] font-bold text-[#00E5FF] uppercase">4. BANKING STOCKS</label>
                <select
                  value={beginnerInputs.banking}
                  onChange={(e) => {
                    setActivePreset("");
                    setBeginnerInputs({ ...beginnerInputs, banking: e.target.value as any });
                  }}
                  className="w-full bg-[#0E1013] border border-[#22272E] rounded px-2 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong / Leading Higher</option>
                  <option value="NEUTRAL">Neutral / Flat</option>
                  <option value="WEAK">Weak / Lagging Lower</option>
                </select>
              </div>
            </div>
          ) : experienceLevel === "INTERMEDIATE" ? (
            /* INTERMEDIATE: 6 Controls */
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 font-mono text-[10px]">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">1. BREADTH</label>
                <select
                  value={intermediateInputs.breadth}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, breadth: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG_POSITIVE">&gt;35 ADV (Strong)</option>
                  <option value="POSITIVE">30–35 ADV</option>
                  <option value="MIXED">22–28 ADV</option>
                  <option value="NEGATIVE">&lt;20 ADV</option>
                  <option value="STRONG_NEGATIVE">&lt;15 ADV (Weak)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">2. INDIA VIX</label>
                <select
                  value={intermediateInputs.vix}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, vix: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="FALLING">Falling</option>
                  <option value="STABLE_LOW">Stable Low (&lt;13)</option>
                  <option value="RISING">Rising</option>
                  <option value="HIGH">High (&gt;20)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">3. PRICE / VWAP</label>
                <select
                  value={intermediateInputs.price}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, price: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="BREAKING_RESISTANCE">Breaking Resistance</option>
                  <option value="ABOVE_VWAP">Above VWAP</option>
                  <option value="CROSSING_VWAP">Crossing VWAP</option>
                  <option value="BELOW_VWAP">Below VWAP</option>
                  <option value="BREAKING_SUPPORT">Breaking Support</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">4. BANK NIFTY</label>
                <select
                  value={intermediateInputs.bankNifty}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, bankNifty: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong (+1.0%)</option>
                  <option value="POSITIVE">Positive</option>
                  <option value="NEUTRAL">Neutral</option>
                  <option value="WEAK">Weak (-1.0%)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">5. PCR (OI)</label>
                <select
                  value={intermediateInputs.pcr}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, pcr: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="SUPPORTIVE">Supportive (&gt;1.15)</option>
                  <option value="BALANCED">Balanced (0.9–1.1)</option>
                  <option value="CALL_HEAVY">Call Heavy (&lt;0.8)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">6. VOLUME</label>
                <select
                  value={intermediateInputs.volume}
                  onChange={(e) => {
                    setActivePreset("");
                    setIntermediateInputs({ ...intermediateInputs, volume: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong (&gt;1.3x)</option>
                  <option value="NORMAL">Normal (1.0x)</option>
                  <option value="WEAK">Weak (&lt;0.7x)</option>
                </select>
              </div>
            </div>
          ) : (
            /* ADVANCED: Full 8 Controls */
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 font-mono text-[10px]">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">1. BREADTH</label>
                <select
                  value={advancedInputs.breadth}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, breadth: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG_POSITIVE">&gt;35 ADV</option>
                  <option value="POSITIVE">30–35 ADV</option>
                  <option value="MIXED">22–28 ADV</option>
                  <option value="NEGATIVE">&lt;20 ADV</option>
                  <option value="STRONG_NEGATIVE">&lt;15 ADV</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">2. INDIA VIX</label>
                <select
                  value={advancedInputs.vix}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, vix: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="FALLING">Falling</option>
                  <option value="STABLE_LOW">Stable Low (&lt;13)</option>
                  <option value="RISING">Rising</option>
                  <option value="HIGH">High (&gt;20)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">3. PRICE / VWAP</label>
                <select
                  value={advancedInputs.price}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, price: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="BREAKING_RESISTANCE">Break Resistance</option>
                  <option value="ABOVE_VWAP">Above VWAP</option>
                  <option value="CROSSING_VWAP">Cross VWAP</option>
                  <option value="INSIDE_RANGE">Inside Range</option>
                  <option value="BELOW_VWAP">Below VWAP</option>
                  <option value="BREAKING_SUPPORT">Break Support</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">4. BANK NIFTY</label>
                <select
                  value={advancedInputs.bankNifty}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, bankNifty: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong</option>
                  <option value="POSITIVE">Positive</option>
                  <option value="NEUTRAL">Neutral</option>
                  <option value="WEAK">Weak</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">5. PCR (OI)</label>
                <select
                  value={advancedInputs.pcr}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, pcr: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="SUPPORTIVE">Supportive</option>
                  <option value="BALANCED">Balanced</option>
                  <option value="CALL_HEAVY">Call Heavy</option>
                  <option value="EXTREME">Extreme</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">6. OI DYNAMIC</label>
                <select
                  value={advancedInputs.oi}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, oi: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="LONG_BUILDUP">Long Buildup</option>
                  <option value="SHORT_COVERING">Short Covering</option>
                  <option value="SHORT_BUILDUP">Short Buildup</option>
                  <option value="LONG_UNWINDING">Long Unwinding</option>
                  <option value="MIXED">Mixed</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">7. VOLUME</label>
                <select
                  value={advancedInputs.volume}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, volume: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="STRONG">Strong</option>
                  <option value="NORMAL">Normal</option>
                  <option value="WEAK">Weak</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-[#707987] uppercase">8. STRUCTURE</label>
                <select
                  value={advancedInputs.structure}
                  onChange={(e) => {
                    setActivePreset("");
                    setAdvancedInputs({ ...advancedInputs, structure: e.target.value as any });
                  }}
                  className="w-full bg-[#13161A] border border-[#22272E] rounded px-1.5 py-1 text-[10px] text-[#E6E8EB] focus:border-[#00E5FF] outline-none"
                >
                  <option value="BREAKOUT">Breakout</option>
                  <option value="HIGHER_HIGHS">Higher Highs</option>
                  <option value="RANGE">Range</option>
                  <option value="LOWER_LOWS">Lower Lows</option>
                  <option value="BREAKDOWN">Breakdown</option>
                </select>
              </div>
            </div>
          )}

          {/* Rule Engine Output Card */}
          <div className="p-3.5 rounded bg-[#13161A] border border-[#22272E] space-y-3 font-mono">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E232B] pb-2">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${
                    scenarioResult.classification === "BULLISH_CONTINUATION"
                      ? "bg-[#00C896]/15 text-[#00C896] border-[#00C896]/30"
                      : scenarioResult.classification === "BEARISH_CONTINUATION"
                      ? "bg-[#E5484D]/15 text-[#E5484D] border-[#E5484D]/30"
                      : scenarioResult.classification === "FALSE_BREAKOUT_RISK"
                      ? "bg-[#FFB020]/15 text-[#FFB020] border-[#FFB020]/30"
                      : scenarioResult.classification === "BEAR_TRAP_RISK"
                      ? "bg-[#00E5FF]/15 text-[#00E5FF] border-[#00E5FF]/30"
                      : scenarioResult.classification === "RANGE_CHOP"
                      ? "bg-[#8B5CF6]/15 text-[#8B5CF6] border-[#8B5CF6]/30"
                      : "bg-[#FFB020]/15 text-[#FFB020] border-[#FFB020]/30"
                  }`}
                >
                  {scenarioResult.title}
                </span>
                <span className="text-[9px] text-[#707987]">Confidence: {scenarioResult.confidenceBand}</span>
              </div>
              <span className="text-[9px] text-[#707987]">{scenarioResult.scenarioId}</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-[10px]">
              {/* Supporting Conditions */}
              <div className="space-y-1">
                <div className="text-[9px] font-bold text-[#00C896] uppercase flex items-center gap-1">
                  <CheckCircle2 size={11} />
                  <span>{experienceLevel === "BEGINNER" ? "Why this happens:" : `Supporting Factors (${scenarioResult.supportingConditions.length})`}</span>
                </div>
                <ul className="list-disc list-inside text-[#A5ABB4] space-y-0.5 text-[9px] pl-1">
                  {scenarioResult.supportingConditions.map((s, i) => (
                    <li key={i} className="leading-tight">
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Opposing / Conflicting Conditions */}
              <div className="space-y-1">
                <div className="text-[9px] font-bold text-[#FFB020] uppercase flex items-center gap-1">
                  <AlertTriangle size={11} />
                  <span>{experienceLevel === "BEGINNER" ? "Watch out for:" : `Opposing / Risk Factors (${scenarioResult.opposingConditions.length})`}</span>
                </div>
                <ul className="list-disc list-inside text-[#A5ABB4] space-y-0.5 text-[9px] pl-1">
                  {scenarioResult.opposingConditions.length > 0 ? (
                    scenarioResult.opposingConditions.map((o, i) => (
                      <li key={i} className="leading-tight text-[#E5484D]">
                        {o}
                      </li>
                    ))
                  ) : (
                    <li className="text-[#707987]">No major conflicting signals detected in selected parameters.</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Interpretation & Invalidation */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 pt-2 border-t border-[#1E232B] text-[10px]">
              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                <div className="text-[9px] font-bold text-[#00E5FF] uppercase">
                  {experienceLevel === "BEGINNER" ? "What this usually means for you:" : "Probable Market Behavior:"}
                </div>
                <p className="text-[#E6E8EB] text-[9px] leading-relaxed">{scenarioResult.interpretation}</p>
              </div>

              <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-0.5">
                <div className="text-[9px] font-bold text-[#E5484D] uppercase">
                  {experienceLevel === "BEGINNER" ? "What would change this view?" : "What Invalidates This View:"}
                </div>
                <p className="text-[#E6E8EB] text-[9px] leading-relaxed">{scenarioResult.invalidation}</p>
              </div>
            </div>

            {/* Educational Takeaway Note */}
            <div className="p-2 rounded bg-[#0E1013]/70 border border-[#1E232B] text-[9px] text-[#A5ABB4]">
              <strong className="text-[#00C896]">Key Takeaway: </strong>
              {scenarioResult.educationalNote}
            </div>
          </div>
        </div>
      )}

      {/* 8. GLOBAL DETAIL MODAL / POPOVER (ADAPTED TO 3 LEVELS) */}
      {selectedMetricDetail && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
          onClick={() => setSelectedMetricDetail(null)}
        >
          <div
            className="bg-[#0E1013] border border-[#00E5FF]/40 rounded-[4px] max-w-[560px] w-full p-4 space-y-3 font-mono shadow-2xl animate-in fade-in zoom-in-95 duration-150 text-[#E6E8EB] max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
              <div className="flex items-center gap-2">
                <Info size={16} className="text-[#00E5FF]" />
                <h3 className="text-sm font-bold text-[#E6E8EB] uppercase">
                  {selectedMetricDetail.name}
                </h3>
                <span className="text-[9px] font-mono bg-[#191D23] text-[#00E5FF] px-1.5 py-0.5 rounded border border-[#00E5FF]/20">
                  {experienceLevel} DETAIL
                </span>
              </div>
              <button
                onClick={() => setSelectedMetricDetail(null)}
                className="text-[#707987] hover:text-white p-1 rounded transition-colors"
              >
                <X size={15} />
              </button>
            </div>

            {/* BEGINNER DETAIL POPOVER: 1. What is this? 2. Why it matters 3. Simple example 4. Remember this */}
            {experienceLevel === "BEGINNER" ? (
              <div className="space-y-3 text-[11px]">
                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00E5FF] uppercase">1. WHAT IS THIS?</div>
                  <p className="text-[#A5ABB4] leading-relaxed">
                    {selectedMetricDetail.beginner.simpleDefinition}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00C896] uppercase">2. WHY DOES IT MATTER?</div>
                  <p className="text-[#A5ABB4] leading-relaxed">
                    {selectedMetricDetail.beginner.whyItMatters}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#FFB020] uppercase">3. SIMPLE EXAMPLE</div>
                  <div className="text-[#E6E8EB] bg-[#13161A] p-2 rounded border border-[#22272E] text-[10px] leading-relaxed">
                    {selectedMetricDetail.beginner.simpleExample}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#E5484D] uppercase">4. REMEMBER THIS</div>
                  <p className="text-[#E6E8EB] bg-[#E5484D]/10 text-[#E5484D] p-2 rounded border border-[#E5484D]/20 leading-relaxed text-[10px]">
                    {selectedMetricDetail.beginner.rememberThis}
                  </p>
                </div>

                {selectedMetricDetail.beginner.jargonBreakdown && (
                  <div className="pt-2 border-t border-[#191D23] text-[9px] text-[#707987]">
                    <strong>Jargon Breakdown: </strong>
                    <span className="text-[#E6E8EB] font-bold">{selectedMetricDetail.beginner.jargonBreakdown.term}</span> ({selectedMetricDetail.beginner.jargonBreakdown.fullName}) — {selectedMetricDetail.beginner.jargonBreakdown.simpleExplanation}
                  </div>
                )}
              </div>
            ) : experienceLevel === "INTERMEDIATE" ? (
              /* INTERMEDIATE DETAIL: 1. What is this? 2. How traders interpret it 3. Common ranges 4. Confirm with 5. Common mistake */
              <div className="space-y-3 text-[11px]">
                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00E5FF] uppercase">1. WHAT IS THIS?</div>
                  <p className="text-[#A5ABB4] leading-relaxed">
                    {selectedMetricDetail.intermediate.infoDetail.whatIsThis}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00C896] uppercase">2. HOW TRADERS INTERPRET IT</div>
                  <p className="text-[#A5ABB4] leading-relaxed">
                    {selectedMetricDetail.intermediate.infoDetail.howTradersInterpretIt}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#FFB020] uppercase">3. COMMON REFERENCE RANGES</div>
                  <div className="grid grid-cols-1 gap-1">
                    {selectedMetricDetail.intermediate.ranges.map((r, i) => (
                      <div key={i} className="flex items-center justify-between p-1 rounded bg-[#13161A] text-[9px]">
                        <span className="font-bold text-[#00E5FF] w-[90px]">{r.range}</span>
                        <span className="text-[#E6E8EB] flex-1 text-right">{r.label} — {r.interpretation}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00E5FF] uppercase">4. CONFIRM WITH</div>
                  <p className="text-[#A5ABB4] leading-relaxed">
                    {selectedMetricDetail.intermediate.infoDetail.confirmWith}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#E5484D] uppercase">5. COMMON MISTAKE</div>
                  <p className="text-[#E5484D] leading-relaxed">
                    {selectedMetricDetail.intermediate.infoDetail.commonMistake}
                  </p>
                </div>
              </div>
            ) : (
              /* ADVANCED DETAIL: 1. Definition 2. Mechanics 3. Regimes 4. Confluence 5. Failure conditions 6. Edge cases 7. Related */
              <div className="space-y-3 text-[11px]">
                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00E5FF] uppercase">1. DEFINITION &amp; ARCHITECTURE</div>
                  <p className="text-[#A5ABB4] leading-relaxed">{selectedMetricDetail.advanced.infoDetail.definition}</p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00C896] uppercase">2. QUANTITATIVE MECHANICS</div>
                  <p className="text-[#A5ABB4] leading-relaxed">{selectedMetricDetail.advanced.mechanics}</p>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#FFB020] uppercase">3. INTERPRETATION REGIMES</div>
                  <div className="space-y-1">
                    {selectedMetricDetail.advanced.detailedRanges.map((dr, di) => (
                      <div key={di} className="p-1.5 rounded bg-[#13161A] text-[9px] space-y-0.5">
                        <div className="flex items-center justify-between text-[#00E5FF] font-bold">
                          <span>{dr.label} ({dr.range})</span>
                          <span className="text-[#A5ABB4]">{dr.regimeContext}</span>
                        </div>
                        <p className="text-[#707987]">{dr.optionOrMarketImpact}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#00E5FF] uppercase">4. CONFLUENCE RULES</div>
                  <ul className="list-disc list-inside text-[#A5ABB4] text-[9px] space-y-0.5">
                    {selectedMetricDetail.advanced.confluenceRules.map((cr, ci) => (
                      <li key={ci}>{cr}</li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-[#E5484D] uppercase">5. FAILURE CONDITIONS &amp; EDGE CASES</div>
                  <p className="text-[#E5484D] text-[9px] leading-relaxed">
                    {selectedMetricDetail.advanced.failureConditions[0]}
                  </p>
                </div>

                <div className="p-2 rounded bg-[#13161A] border border-[#22272E] text-[9px] space-y-0.5">
                  <div className="text-[#FFB020] font-bold uppercase">Hypothetical Case Study:</div>
                  <p className="text-[#E6E8EB]">{selectedMetricDetail.advanced.advancedHypotheticalExample}</p>
                </div>
              </div>
            )}

            <div className="pt-2 border-t border-[#191D23] flex justify-between items-center text-[10px]">
              {selectedMetricDetail.beginner.nextConcept ? (
                <button
                  onClick={() => {
                    const next = UNIFIED_CORE_METRICS.find((m) => m.id === selectedMetricDetail.beginner.nextConcept?.id);
                    if (next) setSelectedMetricDetail(next);
                  }}
                  className="text-[#00E5FF] hover:underline flex items-center gap-1"
                >
                  <span>Next: {selectedMetricDetail.beginner.nextConcept.label}</span>
                  <ArrowRight size={11} />
                </button>
              ) : (
                <div />
              )}
              <button
                onClick={() => setSelectedMetricDetail(null)}
                className="px-3 py-1 bg-[#191D23] hover:bg-[#22272E] text-[#00E5FF] text-[10px] font-bold rounded border border-[#00E5FF]/30 transition-colors"
              >
                Close (Esc)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function HeartIcon(props: { size?: number; className?: string }) {
  return <Activity {...props} />;
}

export default TradingCheatsheetWorkspace;
