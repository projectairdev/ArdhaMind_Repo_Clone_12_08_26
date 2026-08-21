// src/frontend/services/workspace.ts
export type WorkspaceMode = "READ_ONLY" | "LIVE_PRACTICE" | "LIVE_TRADING";

export interface WorkspaceContext {
  currentMode: WorkspaceMode;
  brokerState: "CONNECTED" | "AUTHENTICATING" | "TOKEN_EXPIRED" | "DISCONNECTED";
  marketState: "PRE_OPEN" | "OPEN" | "CLOSED" | "HOLIDAY";
  brokerType: "ZERODHA";
  marketDataSource: "LIVE";
  executionMode: "READ_ONLY" | "PAPER_EXECUTION" | "LIVE_BROKER";
  portfolioSource: "READ_ONLY_BROKER" | "BROKER";
  analyticsMode: "ENABLED" | "DISABLED";
  notificationMode: "ENABLED" | "DISABLED";
  timestamp: string;
}

export interface WorkspaceConfig {
  workspaceMode: WorkspaceMode;
  defaultWorkspaceMode: WorkspaceMode;
  allowLiveTrading: boolean;
  requireConfirmation: boolean;
  showModeWarning: boolean;
  autoFallbackToDevelopment: boolean;
}

// Retrieve from localStorage or fallback to standard LIVE_PRACTICE
let currentMode: WorkspaceMode = "READ_ONLY";

let cachedContext: WorkspaceContext = {
  currentMode: currentMode,
  brokerState: "DISCONNECTED",
  marketState: "CLOSED",
  brokerType: "ZERODHA",
  marketDataSource: "LIVE",
  executionMode: "READ_ONLY",
  portfolioSource: "READ_ONLY_BROKER",
  analyticsMode: "ENABLED",
  notificationMode: "ENABLED",
  timestamp: new Date().toISOString()
};

const config: WorkspaceConfig = {
  workspaceMode: currentMode,
  defaultWorkspaceMode: "READ_ONLY",
  allowLiveTrading: false, // Default to false initially, sync with backend
  requireConfirmation: true,
  showModeWarning: true,
  autoFallbackToDevelopment: false,
};

const listeners: Set<(mode: WorkspaceMode) => void> = new Set();

function syncConfig(data: any) {
  if (!data) return;
  if (data.allow_live_trading !== undefined) {
    config.allowLiveTrading = Boolean(data.allow_live_trading);
  } else if (data.allowLiveTrading !== undefined) {
    config.allowLiveTrading = Boolean(data.allowLiveTrading);
  }

  if (data.require_confirmation !== undefined) {
    config.requireConfirmation = Boolean(data.require_confirmation);
  } else if (data.requireConfirmation !== undefined) {
    config.requireConfirmation = Boolean(data.requireConfirmation);
  }

  if (data.show_mode_warning !== undefined) {
    config.showModeWarning = Boolean(data.show_mode_warning);
  } else if (data.showModeWarning !== undefined) {
    config.showModeWarning = Boolean(data.showModeWarning);
  }

  if (data.auto_fallback_to_development !== undefined) {
    config.autoFallbackToDevelopment = Boolean(data.auto_fallback_to_development);
  } else if (data.autoFallbackToDevelopment !== undefined) {
    config.autoFallbackToDevelopment = Boolean(data.autoFallbackToDevelopment);
  }
}

function mapBackendContext(data: any): WorkspaceContext {
  syncConfig(data);
  const rawStatus = data.broker_status?.normalized_status || data.broker_status?.status || data.brokerState || data.broker_state || "DISCONNECTED";
  const brokerState = rawStatus === "CONNECTED_VERIFIED" || rawStatus === "connected" ? "CONNECTED_VERIFIED" : rawStatus === "CONNECTED_AUTH_REQUIRED" || rawStatus === "session_expired" ? "CONNECTED_AUTH_REQUIRED" : rawStatus === "BROKER_STATE_UNVERIFIED" || rawStatus === "unverified" ? "BROKER_STATE_UNVERIFIED" : rawStatus;
  const mStatus = data.market_session?.status || data.marketState || data.market_state || "CLOSED";
  const marketState = mStatus === "open" ? "OPEN" : mStatus === "holiday" ? "HOLIDAY" : mStatus;
  return {
    currentMode: "READ_ONLY",
    brokerState: brokerState,
    marketState: marketState,
    brokerType: "ZERODHA",
    marketDataSource: "LIVE",
    executionMode: "READ_ONLY",
    portfolioSource: "READ_ONLY_BROKER",
    analyticsMode: data.analytics_mode || data.analyticsMode || "ENABLED",
    notificationMode: data.notification_mode || data.notificationMode || "ENABLED",
    timestamp: data.generated_at || data.timestamp || new Date().toISOString()
  };
}

// Async initialization of workspace from backend API
async function initWorkspace() {
  try {
    const resp = await fetch("/api/workspace");
    const data = await resp.json();
    if (data && !data.error) {
      cachedContext = mapBackendContext(data);
      currentMode = cachedContext.currentMode;
      localStorage.setItem("workspace_mode", currentMode);
      listeners.forEach((l) => l(currentMode));
    }
  } catch (err) {
    console.warn("Failed to sync workspace context with backend:", err);
  }
}

// Fire initial synchronization
initWorkspace();

export const workspaceService = {
  getMode(): WorkspaceMode {
    return currentMode;
  },

  getConfig(): WorkspaceConfig {
    return { ...config, workspaceMode: currentMode };
  },

  updateConfig(updates: Partial<WorkspaceConfig>) {
    Object.assign(config, updates);
  },

  subscribe(listener: (mode: WorkspaceMode) => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  async setMode(newMode: WorkspaceMode, operatorConfirmed: boolean = false): Promise<{ success: boolean; error?: string }> {
    void operatorConfirmed;
    if (newMode !== "READ_ONLY") {
      return { success: false, error: "AIR ArdhaMind has one fixed read-only product mode." };
    }
    return { success: true };

    /* Historical transport retained as unreachable compatibility context.
    if (newMode === "LIVE_TRADING") {
      if (config.requireConfirmation && !operatorConfirmed) {
        return { success: false, error: "Operator confirmation is required to enter LIVE_TRADING." };
      }
    } */

    try {
      const resp = await fetch("/api/workspace/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode, operatorConfirmed })
      });
      const data = await resp.json();
      if (data.error) {
        return { success: false, error: data.error };
      }

      cachedContext = mapBackendContext(data);
      currentMode = cachedContext.currentMode;
      localStorage.setItem("workspace_mode", currentMode);

      // Broadcast updates to all registered listeners
      listeners.forEach((l) => l(currentMode));

      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || "Failed to contact backend Workspace service." };
    }
  },

  getContext(): WorkspaceContext {
    return cachedContext;
  },

  async fetchContext(): Promise<WorkspaceContext> {
    try {
      const resp = await fetch("/api/workspace");
      const data = await resp.json();
      if (data && !data.error) {
        cachedContext = mapBackendContext(data);
        currentMode = cachedContext.currentMode;
      }
    } catch (err) {
      console.warn("Failed to fetch fresh workspace context from API:", err);
    }
    return cachedContext;
  }
};
