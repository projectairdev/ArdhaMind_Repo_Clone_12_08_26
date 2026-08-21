/**
 * AuthenticMarketLogo.tsx
 * 
 * Renders authentic market/index logos from the local asset directory.
 * Falls back gracefully to InstrumentMonogram when asset unavailable.
 * 
 * Asset provenance documented in src/frontend/assets/MANIFEST.json
 * Sources: Wikimedia Commons (public domain / freely licensed)
 * 
 * IMPORTANT: All logos are trademarks of their respective owners.
 * Assets are used in a referential/data-display context only.
 */
import React, { useState } from "react";
import { InstrumentMonogram } from "../visualizations/DataVisualizations";

interface AuthenticLogoProps {
  symbol: string;
  size?: number;
  className?: string;
}

/**
 * Asset configuration for each instrument.
 * 
 * Assets are in /public/assets/ → served at /assets/ by Vite.
 * 
 * dark: true = apply brightness(0)invert(1) for dark-bg compatibility
 * photo: true = photographic asset, render as cropped thumbnail
 */
const LOGO_CONFIGS: Record<string, {
  path: string;
  dark?: boolean;  // white treatment for light logos on dark background
  photo?: boolean; // photographic commodity asset
  opacity?: number;
}> = {
  // Indices — authentic Wikimedia Commons SVG logos
  "S&P 500": {
    path: "/assets/indices/sp500.svg",
    dark: true,
    opacity: 0.85,
  },
  "NASDAQ": {
    path: "/assets/indices/nasdaq.svg",
    dark: true,
    opacity: 0.9,
  },
  "DOW_JONES": {
    path: "/assets/indices/dow_jones.svg",
    dark: true,
    opacity: 0.85,
  },
  "NIKKEI_225": {
    path: "/assets/indices/nikkei.svg",
    dark: true,
    opacity: 0.85,
  },
  "HANG_SENG": {
    path: "/assets/indices/hang_seng.svg",
    dark: false, // monogram, no inversion needed
    opacity: 1.0,
  },
  // Commodities — photographic assets
  "GOLD": {
    path: "/assets/commodities/gold.jpg",
    photo: true,
  },
  "BRENT_CRUDE": {
    path: "/assets/commodities/brent_crude.jpg",
    photo: true,
  },
  // Currency — INR symbol
  "USD_INR": {
    path: "/assets/currencies/inr.svg",
    dark: true,
    opacity: 0.9,
  },
  // GIFT Nifty / NSE
  "GIFT_NIFTY": { path: "/assets/exchanges/nse.svg", dark: true, opacity: 0.9 },
  "NIFTY 50": { path: "/assets/exchanges/nse.svg", dark: true, opacity: 0.9 },
  "NIFTY": { path: "/assets/exchanges/nse.svg", dark: true, opacity: 0.9 },
  "NSE": { path: "/assets/exchanges/nse.svg", dark: true, opacity: 0.9 },
  "BSE": { path: "/assets/exchanges/bse.svg", dark: true, opacity: 0.9 },

  // Regulators / Institutions
  "RBI": { path: "/assets/institutions/rbi.svg", dark: false, opacity: 1 },
  "SEBI": { path: "/assets/institutions/sebi.svg", dark: false, opacity: 1 },
  "FED": { path: "/assets/institutions/fed.svg", dark: false, opacity: 1 },
  "ECB": { path: "/assets/institutions/ecb.svg", dark: false, opacity: 1 },
  "ZERODHA": { path: "/assets/institutions/zerodha.svg", dark: false, opacity: 1 },
  "OPENAI": { path: "/assets/institutions/openai.svg", dark: false, opacity: 1 },

  // Publishers
  "REUTERS": { path: "/assets/publishers/reuters.svg", dark: false, opacity: 1 },
  "BLOOMBERG": { path: "/assets/publishers/bloomberg.svg", dark: false, opacity: 1 },

  // Major Companies / Constituents
  "APOLLOHOSP": { path: "/assets/companies/apollohosp.svg", dark: false, opacity: 1 },
  "BHARTIARTL": { path: "/assets/companies/bhartiartl.svg", dark: false, opacity: 1 },
  "TMPV": { path: "/assets/companies/tmpv.svg", dark: false, opacity: 1 },
  "TATAMOTORS": { path: "/assets/companies/tmpv.svg", dark: false, opacity: 1 },
  "JIOFIN": { path: "/assets/companies/jiofin.svg", dark: false, opacity: 1 },
  "RELIANCE": { path: "/assets/companies/reliance.svg", dark: false, opacity: 1 },
  "HDFCBANK": { path: "/assets/companies/hdfcbank.svg", dark: false, opacity: 1 },
  "ICICIBANK": { path: "/assets/companies/icicibank.svg", dark: false, opacity: 1 },
  "TCS": { path: "/assets/companies/tcs.svg", dark: false, opacity: 1 },
  "INFY": { path: "/assets/companies/infy.svg", dark: false, opacity: 1 },
};

/**
 * AuthenticMarketLogo — renders real asset if available, falls back to monogram.
 * 
 * Design constraints (per sprint spec):
 * - Target size in cards: 28-40px, detail panel: 48-72px
 * - Logos on dark background: white treatment where needed
 * - Commodity photos: contained/cropped at specified size
 * - Failed load: silent fallback to InstrumentMonogram
 */
export function AuthenticMarketLogo({ symbol, size = 32, className = "" }: AuthenticLogoProps) {
  const [failed, setFailed] = useState(false);

  const config = LOGO_CONFIGS[symbol];

  if (!config || failed) {
    return (
      <InstrumentMonogram symbol={symbol} size={size} className={className} />
    );
  }

  if (config.photo) {
    // Photographic commodity asset — cropped thumbnail
    return (
      <div
        className={`overflow-hidden rounded-lg border border-[#1c1c24] shrink-0 ${className}`}
        style={{ width: size, height: size }}
      >
        <img
          src={config.path}
          alt={symbol}
          loading="lazy"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            display: "block",
            filter: "brightness(0.85) saturate(0.8)",
          }}
          onError={() => setFailed(true)}
        />
      </div>
    );
  }

  // Logo/SVG: render with optional dark treatment
  const filterStyle = config.dark
    ? `brightness(0) invert(1) opacity(${config.opacity ?? 0.85})`
    : `opacity(${config.opacity ?? 1})`;

  return (
    <div
      className={`flex items-center justify-center shrink-0 overflow-hidden ${className}`}
      style={{ width: size, height: Math.round(size * 0.65) }}
      title={symbol}
    >
      <img
        src={config.path}
        alt={symbol}
        loading="lazy"
        style={{
          maxWidth: "100%",
          maxHeight: "100%",
          objectFit: "contain",
          display: "block",
          filter: filterStyle,
        }}
        onError={() => setFailed(true)}
      />
    </div>
  );
}

/**
 * InstrumentVisual — primary visual component for instrument cards.
 * 
 * Uses AuthenticMarketLogo when a real asset exists,
 * falls back to InstrumentMonogram otherwise.
 * 
 * Never shows a broken image.
 */
export function InstrumentVisual({
  symbol,
  kind,
  size = 32,
  className = "",
}: {
  symbol: string;
  kind?: string;
  size?: number;
  className?: string;
}) {
  return (
    <AuthenticMarketLogo symbol={symbol} size={size} className={className} />
  );
}

export default InstrumentVisual;
