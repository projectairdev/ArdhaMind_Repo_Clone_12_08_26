// src/frontend/context/NavigationContext.tsx
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

export type PrimaryModuleId =
  | "market"
  | "market_intelligence"
  | "news"
  | "portfolio"
  | "settings";

export type MarketSubTab = "nifty" | "metrics" | "options" | "predictions";
export type NewsSubTab = "live_news" | "catalysts" | "calendar";
export type SettingsSubTab =
  | "overview"
  | "workspace"
  | "connections"
  | "ai_engines"
  | "notifications"
  | "safety"
  | "system"
  | "advanced"
  | "preferences"
  | "diagnostics"
  | "about";

export interface NavigationTarget {
  workspace: PrimaryModuleId | string;
  tab?: string;
  section?: string;
  focus?: string;
  highlight?: boolean;
  source?: string;
}

export interface NavigationContextType {
  activeModule: PrimaryModuleId;
  marketSubTab: MarketSubTab;
  newsSubTab: NewsSubTab;
  settingsOpen: boolean;
  settingsSubTab: SettingsSubTab;
  assistantOpen: boolean;
  assistantExpanded: boolean;
  activeHighlightId: string | null;
  navigateTo: (target: NavigationTarget) => void;
  setActiveModule: (m: PrimaryModuleId | string) => void;
  setMarketSubTab: (t: MarketSubTab) => void;
  setNewsSubTab: (t: NewsSubTab) => void;
  setSettingsOpen: (open: boolean) => void;
  setSettingsSubTab: (t: SettingsSubTab) => void;
  setAssistantOpen: (open: boolean) => void;
  setAssistantExpanded: (expanded: boolean) => void;
  toggleAssistant: () => void;
  toggleAssistantExpanded: () => void;
}

/**
 * Migration normalizer for legacy saved workspaces.
 * Safely maps "intelligence", "market_insights", "pre_market_briefing", and temporary "market_intelligence_v2"
 * to canonical "market_intelligence", "trading_cheatsheet" to "market", and "ardha_performance" to "settings".
 */
export function normalizeModuleId(raw: string | null | undefined): PrimaryModuleId {
  if (!raw) return "market";
  const clean = String(raw).trim();
  if (
    clean === "intelligence" ||
    clean === "market_insights" ||
    clean === "pre_market_briefing" ||
    clean === "market_intelligence_v2" ||
    clean === "market_intelligence"
  ) {
    return "market_intelligence";
  }
  if (clean === "journal") return "news";
  if (clean === "ardha_performance") return "settings";
  if (clean === "trading_cheatsheet" || clean === "cheatsheet") return "market";
  const allowed: PrimaryModuleId[] = [
    "market",
    "market_intelligence",
    "news",
    "portfolio",
    "settings",
  ];
  return allowed.includes(clean as PrimaryModuleId) ? (clean as PrimaryModuleId) : "market";
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [activeModule, setActiveModuleState] = useState<PrimaryModuleId>(() => {
    const saved = localStorage.getItem("active_module");
    return normalizeModuleId(saved);
  });

  const [marketSubTab, setMarketSubTabState] = useState<MarketSubTab>(() => {
    const saved = localStorage.getItem("active_market_tab");
    if (saved === "metrics" || saved === "options" || saved === "predictions") return saved as MarketSubTab;
    return "nifty";
  });

  const [newsSubTab, setNewsSubTabState] = useState<NewsSubTab>("live_news");
  const [settingsOpen, setSettingsOpenState] = useState<boolean>(() => {
    const saved = localStorage.getItem("active_module");
    return saved === "settings" || saved === "ardha_performance";
  });
  const [settingsSubTab, setSettingsSubTabState] = useState<SettingsSubTab>(() => {
    const saved = localStorage.getItem("active_module");
    return saved === "ardha_performance" ? "diagnostics" : "overview";
  });
  const [assistantOpen, setAssistantOpenState] = useState<boolean>(false);
  const [assistantExpanded, setAssistantExpandedState] = useState<boolean>(false);
  const [activeHighlightId, setActiveHighlightId] = useState<string | null>(null);

  const setActiveModule = useCallback((m: PrimaryModuleId | string) => {
    const rawClean = String(m || "").trim();
    if (rawClean === "ardha_performance") {
      setSettingsOpenState(true);
      setSettingsSubTabState("diagnostics");
      localStorage.setItem("active_module", "settings");
      return;
    }
    const normalized = normalizeModuleId(m);
    if (normalized === "settings") {
      setSettingsOpenState(true);
    } else {
      setSettingsOpenState(false);
      setActiveModuleState(normalized);
      localStorage.setItem("active_module", normalized);
    }
  }, []);

  const setMarketSubTab = useCallback((t: MarketSubTab) => {
    setSettingsOpenState(false);
    setActiveModuleState("market");
    setMarketSubTabState(t);
    localStorage.setItem("active_module", "market");
    localStorage.setItem("active_market_tab", t);
  }, []);

  const setNewsSubTab = useCallback((t: NewsSubTab) => {
    setSettingsOpenState(false);
    setActiveModuleState("news");
    setNewsSubTabState(t);
    localStorage.setItem("active_module", "news");
  }, []);

  const setSettingsOpen = useCallback((open: boolean) => {
    setSettingsOpenState(open);
    if (open) {
      localStorage.setItem("active_module", "settings");
    }
  }, []);

  const setSettingsSubTab = useCallback((t: SettingsSubTab) => {
    setSettingsOpenState(true);
    setSettingsSubTabState(t);
  }, []);

  const navigateTo = useCallback((target: NavigationTarget) => {
    const { workspace, tab, section, focus, highlight = true } = target;
    const rawClean = String(workspace || "").trim();
    if (rawClean === "ardha_performance") {
      setSettingsOpenState(true);
      setSettingsSubTabState("diagnostics");
      localStorage.setItem("active_module", "settings");
      if (section) {
        setTimeout(() => {
          const el = document.getElementById(section) || document.getElementById("settings-diagnostics-ardha-performance");
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }, 100);
      }
      return;
    }

    const normalized = normalizeModuleId(workspace);

    // 1. Activate Workspace & SubTab
    if (normalized === "settings") {
      setSettingsOpenState(true);
      if (tab) {
        setSettingsSubTabState(tab as SettingsSubTab);
      }
    } else {
      setSettingsOpenState(false);
      setActiveModuleState(normalized);
      localStorage.setItem("active_module", normalized);

      if (normalized === "market" && tab) {
        setMarketSubTabState(tab as MarketSubTab);
        localStorage.setItem("active_market_tab", tab);
      } else if (normalized === "news" && tab) {
        setNewsSubTabState(tab as NewsSubTab);
      }
    }

    // 2. Scroll to section & apply arrival highlight pulse
    if (section) {
      const triggerScrollAndHighlight = () => {
        const elem = document.getElementById(section);
        if (elem) {
          elem.scrollIntoView({ behavior: "smooth", block: "center" });
          if (focus) {
            const focusTarget = document.getElementById(focus) || elem;
            if (typeof focusTarget.focus === "function") {
              focusTarget.focus();
            }
          }
          if (highlight !== false) {
            setActiveHighlightId(section);
            setTimeout(() => {
              setActiveHighlightId(null);
            }, 1800);
          }
        }
      };

      // Allow DOM render turn for cross-workspace transitions
      requestAnimationFrame(() => {
        setTimeout(triggerScrollAndHighlight, 80);
      });
    }
  }, []);

  // P4 — CLEAN URL ON LOAD: One-time cleanup of stale legacy URL hash if present
  useEffect(() => {
    if (typeof window !== "undefined" && window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }, []);

  const setAssistantOpen = useCallback((open: boolean) => {
    setAssistantOpenState(open);
    if (!open) {
      setAssistantExpandedState(false);
    }
  }, []);

  const toggleAssistant = useCallback(() => {
    setAssistantOpenState(prev => {
      if (prev) setAssistantExpandedState(false);
      return !prev;
    });
  }, []);

  const setAssistantExpanded = useCallback((expanded: boolean) => {
    setAssistantExpandedState(expanded);
  }, []);

  const toggleAssistantExpanded = useCallback(() => {
    setAssistantExpandedState(prev => !prev);
  }, []);

  return (
    <NavigationContext.Provider
      value={{
        activeModule,
        marketSubTab,
        newsSubTab,
        settingsOpen,
        settingsSubTab,
        assistantOpen,
        assistantExpanded,
        activeHighlightId,
        navigateTo,
        setActiveModule,
        setMarketSubTab,
        setNewsSubTab,
        setSettingsOpen,
        setSettingsSubTab,
        setAssistantOpen,
        setAssistantExpanded,
        toggleAssistant,
        toggleAssistantExpanded,
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation(): NavigationContextType {
  const ctx = useContext(NavigationContext);
  if (!ctx) {
    throw new Error("useNavigation must be used within NavigationProvider");
  }
  return ctx;
}
