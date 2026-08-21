import React from "react";

interface AssetProps {
  size?: number;
  className?: string;
}

// 1. ArdhaMind Brand Mark: Custom AI Signal Node + Precision Market Crosshair
export function ArdhaMindBrandMark({ size = 28, className = "" }: AssetProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect width="32" height="32" rx="8" fill="#091410" stroke="#00E5A8" strokeWidth="1.5" />
      <path d="M7 21L12 15L17 18L25 9" stroke="#00E5A8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="25" cy="9" r="2.5" fill="#00E5A8" />
      <circle cx="12" cy="15" r="1.5" fill="#39D9FF" />
      <path d="M7 24H25" stroke="#00E5A8" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />
      <path d="M17 11V21" stroke="#39D9FF" strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
    </svg>
  );
}

// 2. Navigation & Workspace Glyphs
export function MarketGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 17L8.5 11.5L12.5 15.5L21 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 7H21V11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 21H21" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.4" />
    </svg>
  );
}

export function IntelligenceGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M12 3V21M3 12H21" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2 2" opacity="0.4" />
      <circle cx="12" cy="12" r="5" fill="#C084FC" fillOpacity="0.2" stroke="#C084FC" strokeWidth="2" />
      <circle cx="12" cy="12" r="2" fill="#C084FC" />
      <path d="M6 6L18 18M18 6L6 18" stroke="currentColor" strokeWidth="1" strokeOpacity="0.3" />
    </svg>
  );
}

export function PortfolioGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="3" y="6" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M8 6V4C8 3.44772 8.44772 3 9 3H15C15.5523 3 16 3.44772 16 4V6" stroke="currentColor" strokeWidth="2" />
      <path d="M12 11V15M10 13H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function JournalGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M4 19.5C4 18.6716 4.67157 18 5.5 18H20" stroke="currentColor" strokeWidth="2" />
      <path d="M6 4H20V20H5.5C4.67157 20 4 19.3284 4 18.5V5.5C4 4.67157 4.67157 4 5.5 4H6Z" stroke="currentColor" strokeWidth="2" />
      <path d="M8 9H16M8 13H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function OptionsGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="4" y="4" width="7" height="7" rx="1.5" stroke="#FF5C77" strokeWidth="2" />
      <rect x="13" y="13" width="7" height="7" rx="1.5" stroke="#00E5A8" strokeWidth="2" />
      <path d="M11 7.5H16.5C17.0523 7.5 17.5 7.94772 17.5 8.5V13" stroke="#FFB84D" strokeWidth="1.5" strokeDasharray="2 2" />
    </svg>
  );
}

export function MetricsGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M12 7V12L15.5 15.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="2" fill="currentColor" />
    </svg>
  );
}

export function VixGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M2 12C4 6 6 18 9 12C12 6 14 18 17 12C19 8 21 15 22 12" stroke="#FFB84D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function BreadthGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <rect x="3" y="5" width="18" height="4" rx="1" fill="#00E5A8" fillOpacity="0.3" stroke="#00E5A8" strokeWidth="1.5" />
      <rect x="3" y="11" width="12" height="4" rx="1" fill="#FF5C77" fillOpacity="0.3" stroke="#FF5C77" strokeWidth="1.5" />
      <rect x="3" y="17" width="15" height="4" rx="1" fill="#39D9FF" fillOpacity="0.3" stroke="#39D9FF" strokeWidth="1.5" />
    </svg>
  );
}

export function KeyLevelsGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 6H21" stroke="#FF5C77" strokeWidth="2" strokeDasharray="3 3" />
      <path d="M3 12H21" stroke="#FFB84D" strokeWidth="2" />
      <path d="M3 18H21" stroke="#00E5A8" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="12" cy="12" r="3" fill="#FFB84D" />
    </svg>
  );
}

export function GlobalCuesGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="9" stroke="#39D9FF" strokeWidth="2" />
      <ellipse cx="12" cy="12" rx="9" ry="4" stroke="#39D9FF" strokeWidth="1.5" />
      <path d="M12 3V21" stroke="#39D9FF" strokeWidth="1.5" />
    </svg>
  );
}

export function PreMarketGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="12" cy="12" r="5" stroke="#FFB84D" strokeWidth="2" />
      <path d="M12 2V4M12 20V22M2 12H4M20 12H22M4.93 4.93L6.34 6.34M17.66 17.66L19.07 19.07M4.93 19.07L6.34 17.66M17.66 6.34L19.07 4.93" stroke="#FFB84D" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function PostMarketGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" stroke="#C084FC" strokeWidth="2" fill="#C084FC" fillOpacity="0.2" />
    </svg>
  );
}

export function InstitutionalGlyph({ size = 20, className = "" }: AssetProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M3 21H21M4 18V9L12 3L20 9V18M9 18V13H15V18" stroke="#00E5A8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// 3. Specific Asset Glyphs for METRICS Instrument Selector
export function InstrumentAssetIcon({ symbol, kind, size = 24 }: { symbol: string; kind?: string; size?: number }) {
  const sym = symbol.toUpperCase();

  if (sym.includes("GIFT") || sym.includes("NIFTY")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#00E5A8" fillOpacity="0.15" stroke="#00E5A8" strokeWidth="1.5" />
        <path d="M6 16L10 11L14 14L18 8" stroke="#00E5A8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (sym.includes("S&P") || sym.includes("DOW") || sym.includes("NASDAQ")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#39D9FF" fillOpacity="0.15" stroke="#39D9FF" strokeWidth="1.5" />
        <path d="M5 16L9 9L13 13L19 7" stroke="#39D9FF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (sym.includes("NIKKEI") || sym.includes("HANG")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#60A5FA" fillOpacity="0.15" stroke="#60A5FA" strokeWidth="1.5" />
        <circle cx="12" cy="12" r="5" stroke="#60A5FA" strokeWidth="2" />
      </svg>
    );
  }
  if (sym.includes("VIX")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#FFB84D" fillOpacity="0.15" stroke="#FFB84D" strokeWidth="1.5" />
        <path d="M4 12C6 7 8 17 11 12C14 7 16 17 19 12" stroke="#FFB84D" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }
  if (sym.includes("USD") || sym.includes("DXY")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#00E5A8" fillOpacity="0.15" stroke="#00E5A8" strokeWidth="1.5" />
        <path d="M12 6V18M15 9.5C15 8.1 13.7 7 12 7C10.3 7 9 8.1 9 9.5C9 10.9 10.3 12 12 12C13.7 12 15 13.1 15 14.5C15 15.9 13.7 17 12 17C10.3 17 9 15.9 9 14.5" stroke="#00E5A8" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }
  if (sym.includes("BRENT") || sym.includes("OIL")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#FF5C77" fillOpacity="0.15" stroke="#FF5C77" strokeWidth="1.5" />
        <path d="M12 4C12 4 7 10 7 14.5C7 17.26 9.24 19.5 12 19.5C14.76 19.5 17 17.26 17 14.5C17 10 12 4 12 4Z" stroke="#FF5C77" strokeWidth="2" />
      </svg>
    );
  }
  if (sym.includes("GOLD")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#FFB84D" fillOpacity="0.15" stroke="#FFB84D" strokeWidth="1.5" />
        <path d="M6 15L12 7L18 15H6Z" stroke="#FFB84D" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    );
  }
  if (sym.includes("10Y") || sym.includes("YIELD")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#39D9FF" fillOpacity="0.15" stroke="#39D9FF" strokeWidth="1.5" />
        <path d="M5 19H19M7 15L12 9L17 15" stroke="#39D9FF" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }
  if (kind === "institutional" || sym.includes("FII") || sym.includes("DII")) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="6" fill="#00E5A8" fillOpacity="0.15" stroke="#00E5A8" strokeWidth="1.5" />
        <path d="M4 18V9L12 4L20 9V18" stroke="#00E5A8" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#39D9FF" fillOpacity="0.15" stroke="#39D9FF" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="4" stroke="#39D9FF" strokeWidth="2" />
    </svg>
  );
}
