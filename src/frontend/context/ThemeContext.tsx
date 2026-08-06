// src/frontend/context/ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect } from "react";

export type ThemeType = "dark-pro" | "light-pro" | "midnight-focus";
export type AccentColor = "cyan" | "emerald" | "amber" | "rose" | "indigo";
export type FontSize = "small" | "normal" | "large";
export type Density = "compact" | "comfortable";

export interface ThemeContextProps {
  theme: ThemeType;
  accentColor: AccentColor;
  fontSize: FontSize;
  density: Density;
  setTheme: (t: ThemeType) => void;
  setAccentColor: (c: AccentColor) => void;
  setFontSize: (s: FontSize) => void;
  setDensity: (d: Density) => void;
  // Dynamic theme styling helpers
  themeClasses: {
    bg: string;
    card: string;
    border: string;
    text: string;
    textMuted: string;
    input: string;
    bgMuted: string;
  };
  accentClasses: {
    text: string;
    bg: string;
    border: string;
    badge: string;
    glow: string;
    button: string;
  };
  densityClasses: {
    padding: string;
    gap: string;
    heading: string;
  };
  fontClasses: {
    base: string;
    title: string;
    mono: string;
  };
}

const ThemeContext = createContext<ThemeContextProps | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeType>(() => {
    return (localStorage.getItem("theme_pref") as ThemeType) || "dark-pro";
  });
  const [accentColor, setAccentColorState] = useState<AccentColor>(() => {
    return (localStorage.getItem("accent_pref") as AccentColor) || "cyan";
  });
  const [fontSize, setFontSizeState] = useState<FontSize>(() => {
    return (localStorage.getItem("font_size_pref") as FontSize) || "normal";
  });
  const [density, setDensityState] = useState<Density>(() => {
    return (localStorage.getItem("density_pref") as Density) || "compact";
  });

  useEffect(() => {
    localStorage.setItem("theme_pref", theme);
    // Apply class to body for global styling overrides if needed
    const bodyClass = document.body.classList;
    bodyClass.remove("theme-dark-pro", "theme-light-pro", "theme-midnight-focus");
    bodyClass.add(`theme-${theme}`);
    if (theme === "light-pro") {
      bodyClass.add("bg-[#f5f5f4]");
      bodyClass.remove("bg-neutral-950");
    } else {
      bodyClass.add("bg-neutral-950");
      bodyClass.remove("bg-[#f5f5f4]");
    }
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("accent_pref", accentColor);
  }, [accentColor]);

  useEffect(() => {
    localStorage.setItem("font_size_pref", fontSize);
  }, [fontSize]);

  useEffect(() => {
    localStorage.setItem("density_pref", density);
  }, [density]);

  const setTheme = (t: ThemeType) => setThemeState(t);
  const setAccentColor = (c: AccentColor) => setAccentColorState(c);
  const setFontSize = (s: FontSize) => setFontSizeState(s);
  const setDensity = (d: Density) => setDensityState(d);

  // 1. Theme-Specific Tailwind Classes Mapping
  const themeClasses = {
    "dark-pro": {
      bg: "bg-[#0a0a0a]",
      card: "bg-[#141414] border-neutral-800/80",
      border: "border-neutral-850",
      text: "text-neutral-100",
      textMuted: "text-neutral-400",
      input: "bg-[#1e1e1e] border-neutral-800 text-white focus:border-cyan-500",
      bgMuted: "bg-[#1c1c1c]",
    },
    "light-pro": {
      bg: "bg-[#f5f5f4]",
      card: "bg-white border-neutral-200/90 shadow-sm",
      border: "border-neutral-200",
      text: "text-neutral-900",
      textMuted: "text-neutral-500",
      input: "bg-neutral-50 border-neutral-300 text-neutral-900 focus:border-cyan-600",
      bgMuted: "bg-neutral-100",
    },
    "midnight-focus": {
      bg: "bg-[#020617]",
      card: "bg-[#0b1329]/95 border-slate-800/80 shadow-[0_4px_20px_rgba(0,0,0,0.3)]",
      border: "border-slate-850",
      text: "text-slate-100",
      textMuted: "text-slate-400",
      input: "bg-[#0d1731] border-slate-800 text-slate-100 focus:border-cyan-400",
      bgMuted: "bg-[#111e3d]",
    }
  }[theme];

  // 2. Accent-Specific Tailwind Classes Mapping
  const accentClasses = {
    cyan: {
      text: theme === "light-pro" ? "text-cyan-650" : "text-cyan-400",
      bg: "bg-cyan-500",
      border: theme === "light-pro" ? "border-cyan-300" : "border-cyan-500/30",
      badge: "bg-cyan-950/40 text-cyan-400 border border-cyan-800/40",
      glow: "shadow-[0_0_12px_rgba(6,182,212,0.15)]",
      button: "bg-cyan-600 hover:bg-cyan-500 text-slate-950",
    },
    emerald: {
      text: theme === "light-pro" ? "text-emerald-650" : "text-emerald-400",
      bg: "bg-emerald-500",
      border: theme === "light-pro" ? "border-emerald-300" : "border-emerald-500/30",
      badge: "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40",
      glow: "shadow-[0_0_12px_rgba(16,185,129,0.15)]",
      button: "bg-emerald-600 hover:bg-emerald-500 text-slate-950",
    },
    amber: {
      text: theme === "light-pro" ? "text-amber-650" : "text-amber-400",
      bg: "bg-amber-500",
      border: theme === "light-pro" ? "border-amber-300" : "border-amber-500/30",
      badge: "bg-amber-950/40 text-amber-400 border border-amber-850/40",
      glow: "shadow-[0_0_12px_rgba(245,158,11,0.15)]",
      button: "bg-amber-600 hover:bg-amber-500 text-slate-950",
    },
    rose: {
      text: theme === "light-pro" ? "text-rose-650" : "text-rose-400",
      bg: "bg-rose-500",
      border: theme === "light-pro" ? "border-rose-300" : "border-rose-500/30",
      badge: "bg-rose-950/40 text-rose-400 border border-rose-850/40",
      glow: "shadow-[0_0_12px_rgba(244,63,94,0.15)]",
      button: "bg-rose-600 hover:bg-rose-500 text-white",
    },
    indigo: {
      text: theme === "light-pro" ? "text-indigo-650" : "text-indigo-400",
      bg: "bg-indigo-500",
      border: theme === "light-pro" ? "border-indigo-300" : "border-indigo-500/30",
      badge: "bg-indigo-950/40 text-indigo-400 border border-indigo-850/40",
      glow: "shadow-[0_0_12px_rgba(99,102,241,0.15)]",
      button: "bg-indigo-600 hover:bg-indigo-500 text-white",
    }
  }[accentColor];

  // 3. Density-Specific Tailwind Classes Mapping
  const densityClasses = {
    compact: {
      padding: "p-3 sm:p-4",
      gap: "gap-3 sm:gap-4",
      heading: "mb-3 pb-3",
    },
    comfortable: {
      padding: "p-5 sm:p-6",
      gap: "gap-5 sm:gap-6",
      heading: "mb-5 pb-5",
    }
  }[density];

  // 4. Sizing classes
  const fontClasses = {
    small: {
      base: "text-[11px] sm:text-xs",
      title: "text-sm font-bold tracking-tight",
      mono: "font-mono text-[10px]",
    },
    normal: {
      base: "text-xs sm:text-sm",
      title: "text-base font-bold tracking-tight",
      mono: "font-mono text-xs",
    },
    large: {
      base: "text-sm sm:text-base",
      title: "text-lg font-bold tracking-tight",
      mono: "font-mono text-sm",
    }
  }[fontSize];

  return (
    <ThemeContext.Provider
      value={{
        theme,
        accentColor,
        fontSize,
        density,
        setTheme,
        setAccentColor,
        setFontSize,
        setDensity,
        themeClasses,
        accentClasses,
        densityClasses,
        fontClasses,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
