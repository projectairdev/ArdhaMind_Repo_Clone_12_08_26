import "dotenv/config";
import express from "express";
import { rejectReadOnlyMutation } from "./src/read_only_http";
import path from "path";
import fs from "fs";
import { spawn, ChildProcess } from "child_process";
import readline from "readline";
import { createServer as createViteServer } from "vite";
import { WebSocketServer, WebSocket } from "ws";

const app = express();
const PORT = 3000;

app.use(express.json());

// In-memory REST rate limiter (120 requests / min per IP)
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();
app.use((req, res, next) => {
  if (!req.path.startsWith("/api/")) return next();
  const ip = req.ip || "127.0.0.1";
  const now = Date.now();
  const record = rateLimitMap.get(ip) || { count: 0, resetAt: now + 60000 };
  if (now > record.resetAt) {
    record.count = 1;
    record.resetAt = now + 60000;
  } else {
    record.count += 1;
  }
  rateLimitMap.set(ip, record);
  if (record.count > 150) {
    res.status(429).json({ error: "Too many REST requests. Rate limit exceeded." });
    return;
  }
  next();
});

// Persistent state for workspace mode in-memory (defaults to LIVE_PRACTICE)
let activeWorkspaceMode = "READ_ONLY";

// In-memory active broker keys for the duration of the server process
let activeApiKey = process.env.KITE_API_KEY || "";
let activeAccessToken = process.env.KITE_ACCESS_TOKEN || "";

// Attempt to load persisted credentials from local cache file on startup
function loadPersistedSession() {
  try {
    const cachePath = path.join(process.cwd(), ".cache/session.json");
    if (fs.existsSync(cachePath)) {
      const data = JSON.parse(fs.readFileSync(cachePath, "utf-8"));
      if (data) {
        if (data.api_key) {
          activeApiKey = data.api_key;
        }
        const expiresAt = data.expires_at || 0;
        const now = Date.now() / 1000;
        if (data.access_token && (expiresAt === 0 || expiresAt > now)) {
          activeAccessToken = data.access_token;
        }
      }
    }
  } catch (err) {
    console.error("Failed to load persisted session in server.ts:", err);
  }
}

loadPersistedSession();

// Central global workstation state cache
let workstationState: any = {
  workspaceContext: {
    currentMode: activeWorkspaceMode,
    brokerState: "DISCONNECTED",
    marketState: "CLOSED",
    brokerType: "ZERODHA",
    marketDataSource: "LIVE",
    executionMode: "READ_ONLY",
    portfolioSource: "BROKER",
    analyticsMode: "ENABLED",
    notificationMode: "ENABLED",
    timestamp: new Date().toISOString()
  },
  brokerAccount: null,
  brokerFunds: null,
  portfolioReport: null,
  marketScore: null,
  opportunityContext: null,
  strategyEvaluation: null,
  tradePlan: null,
  confidenceReport: null,
  riskReport: null,
  decisionReport: null,
  operationsReport: null,
  configurationReport: null,
  explanationReport: null,
  intradayReport: null,
  validationReport: null,
  optimizationReport: null,
  marketStatusReport: null,
  eveningReport: null,
  analyticsReport: null,
  newsSentiment: null,
  ticks: {}
};

function mergeOfficialIndiaEvents(macro: any, news: any) {
  const existing = Array.isArray(macro?.official_india_events) ? macro.official_india_events : [];
  const officialNews = (Array.isArray(news?.items) ? news.items : [])
    .filter((item: any) => ["RBI", "SEBI", "GOVERNMENT_POLICY", "INDIA_MACRO"].includes(String(item?.canonical_event_category || "")))
    .map((item: any) => ({
      id: item.id,
      event_category: item.canonical_event_category,
      headline: item.headline,
      description: item.summary_snippet,
      published_at: item.published_at,
      retrieved_at: item.received_at,
      source_name: item.source_name,
      source_url: item.original_url,
      source_reference: item.source_reference || item.original_url,
      source_authority: item.source_authority || "PRIMARY",
      verification_status: String(item.verification_status || "").toUpperCase(),
      relevance_score: item.nifty_relevance_score,
      impact_level: String(item.impact_strength || "").toUpperCase(),
      confidence: item.confidence,
      official_subcategory: item.official_subcategory,
      freshness_status: item.freshness_status,
    }));
  const merged = [...existing, ...officialNews].filter((item: any, index: number, all: any[]) =>
    all.findIndex((candidate: any) => String(candidate?.id || "") === String(item?.id || "")) === index
  );
  return { ...(macro || {}), official_india_events: merged };
}

// WebSocket broadcast server instance
let wss: WebSocketServer | null = null;

function broadcastToClients(msg: any) {
  if (!wss) return;
  const rawStr = JSON.stringify(msg);
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(rawStr);
    }
  });
}

// Persistent Python Daemon process
let pyDaemon: ChildProcess | null = null;
let pendingRequests: Map<string, { resolve: (val: any) => void; reject: (err: any) => void }> = new Map();
let requestCounter = 0;

function startPythonDaemon() {
  if (pyDaemon) {
    console.log("Terminating existing Python Daemon process...");
    try {
      pyDaemon.kill();
    } catch {}
  }

  const env = {
    ...process.env,
    PYTHONPATH: ".",
    WORKSPACE_MODE: activeWorkspaceMode,
    KITE_API_KEY: activeApiKey || process.env.KITE_API_KEY || "",
    KITE_API_SECRET: process.env.KITE_API_SECRET || "",
    KITE_REDIRECT_URL: process.env.KITE_REDIRECT_URL || "http://127.0.0.1:3000/api/broker/callback",
    OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",
    PREFERRED_TRADING_STYLE: process.env.PREFERRED_TRADING_STYLE || "Intraday"
  };

  let pythonCmd = process.platform === "win32" ? "python" : "python3";
  const venvPath1 = path.join(process.cwd(), "new/Scripts/python.exe");
  const venvPath2 = process.platform === "win32"
    ? path.join(process.cwd(), ".venv/Scripts/python.exe")
    : path.join(process.cwd(), ".venv/bin/python");
  if (fs.existsSync(venvPath1)) {
    pythonCmd = venvPath1;
  } else if (fs.existsSync(venvPath2)) {
    pythonCmd = venvPath2;
  }
  console.log(`Spawning persistent Python bridge daemon: ${pythonCmd} src/server_bridge.py --action daemon`);

  pyDaemon = spawn(pythonCmd, ["src/server_bridge.py", "--action", "daemon"], { env });

  const rl = readline.createInterface({
    input: pyDaemon.stdout!,
    terminal: false
  });

  rl.on("line", (line) => {
    try {
      const msg = JSON.parse(line.trim());
      if (msg.type === "tick") {
        const t_forward = new Date().toISOString();
        const tickData = {
          ...msg.data,
          backend_forward_timestamp: t_forward
        };
        workstationState.ticks[msg.symbol] = tickData;
        broadcastToClients({ type: "tick", symbol: msg.symbol, data: tickData });
      } else if (msg.type === "state") {
        workstationState = msg.data;
        broadcastToClients({ type: "state", data: workstationState });
      } else if (msg.type === "response") {
        const req = pendingRequests.get(msg.requestId);
        if (req) {
          pendingRequests.delete(msg.requestId);
          if (msg.success) {
            req.resolve(msg.data);
          } else {
            req.reject(new Error(msg.error || "Bridge execution failed"));
          }
        }
      }
    } catch (err) {
      console.warn("Non-JSON stdout line from Python Daemon:", line);
    }
  });

  pyDaemon.stderr!.on("data", (data) => {
    console.error("Python Daemon stderr output:", data.toString().trim());
  });

  pyDaemon.on("close", (code) => {
    console.warn(`Python Daemon closed with exit code ${code}. Respawning in 3 seconds...`);
    pyDaemon = null;
    setTimeout(startPythonDaemon, 3000);
  });
}

// Start the daemon process
startPythonDaemon();

function sendDaemonRequest(action: string, params: any = {}): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!pyDaemon) {
      return reject(new Error("Python bridge daemon is currently offline"));
    }
    const requestId = `REQ-${++requestCounter}-${Date.now()}`;
    pendingRequests.set(requestId, { resolve, reject });
    
    pyDaemon.stdin!.write(JSON.stringify({ requestId, action, params }) + "\n");
  });
}

// REST API Endpoints (Return cached state instantly to support legacy fetches with 0ms latency)
app.get("/api/workspace", (req, res) => {
  res.json(workstationState);
});

app.post("/api/workspace/mode", (_req, res) => {
  res.status(410).json({ error: "AIR ArdhaMind Phase 1 has one fixed LIVE INTELLIGENCE — READ ONLY profile." });
});

app.post("/api/workspace/runtime-flags", (_req, res) => {
  process.env.ALLOW_LIVE_TRADING = "False";
  res.status(410).json({ allowLiveTrading: false, error: "Live execution is unavailable in AIR ArdhaMind Phase 1." });
});

app.get("/api/workspace/trading-preferences", async (req, res) => {
  res.json({ preferredTradingStyle: process.env.PREFERRED_TRADING_STYLE || "Intraday" });
});

app.post("/api/workspace/trading-preferences", async (req, res) => {
  const { preferredTradingStyle } = req.body;
  if (preferredTradingStyle) {
    process.env.PREFERRED_TRADING_STYLE = preferredTradingStyle;
  }
  res.json({ preferredTradingStyle: process.env.PREFERRED_TRADING_STYLE || "Intraday" });
});

app.get("/api/broker/login-url", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_login_url");
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/broker/callback", async (req, res) => {
  const requestToken = (req.query.request_token as string) || (req.query.requestToken as string);
  console.log(`[AUTH] Callback route reached. RequestToken present: ${Boolean(requestToken)}`);
  if (!requestToken) {
    res.status(400).json({ success: false, error: "Missing request_token parameter from Zerodha authentication." });
    return;
  }
  try {
    const result = await sendDaemonRequest("exchange_request_token", { request_token: requestToken });
    console.log(`[AUTH] Token exchange result success: ${Boolean(result && result.success)}`);
    if (result && result.success) {
      workstationState.workspaceContext = {
        ...workstationState.workspaceContext,
        brokerState: "CONNECTED",
        timestamp: new Date().toISOString()
      };
      broadcastToClients({
        type: "auth_event",
        brokerState: "CONNECTED",
        timestamp: new Date().toISOString()
      });
      console.log("[AUTH] Broker canonical publication SUCCESS — auth_event broadcast to all clients.");
      if (req.headers.accept && req.headers.accept.includes("application/json")) {
        return res.json({ success: true, brokerState: "CONNECTED" });
      }
      return res.redirect("/?connected=true");
    } else {
      console.log(`[AUTH] Token exchange failed: ${result?.error || "Unknown error"}`);
      if (req.headers.accept && req.headers.accept.includes("application/json")) {
        return res.status(400).json({ success: false, error: result?.error || "Unknown error" });
      }
      return res.redirect(`/?login=failed&reason=${encodeURIComponent(result?.error || "Token exchange failed")}`);
    }
  } catch (err: any) {
    console.log(`[AUTH] Callback exception: ${err.message}`);
    if (req.headers.accept && req.headers.accept.includes("application/json")) {
      return res.status(500).json({ error: err.message });
    }
    return res.redirect(`/?login=failed&reason=${encodeURIComponent(err.message)}`);
  }
});

app.get("/api/broker/config", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_broker_config");
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/broker/login", async (req, res) => {
  const { api_key, access_token, persist_key, persist_token } = req.body;
  if (!api_key || !access_token) {
    res.status(400).json({ error: "API Key and Access Token are required." });
    return;
  }

  activeApiKey = api_key;
  activeAccessToken = access_token;

  try {
    const result = await sendDaemonRequest("login", {
      api_key,
      access_token,
      persist_key,
      persist_token
    });
    if (result && result.success) {
      // [V1.3.1 FIX] DO NOT restart the daemon after login.
      // The running daemon already has the authenticated session via gateway.connect().
      // Restarting it caused a 3-10 second gap where brokerState stayed DISCONNECTED.
      //
      // Instead: immediately update the server-side cached state so REST polls get CONNECTED,
      // then broadcast an auth_event to all WebSocket clients for instant React propagation.
      workstationState.workspaceContext = {
        ...workstationState.workspaceContext,
        brokerState: "CONNECTED",
        timestamp: new Date().toISOString()
      };
      broadcastToClients({
        type: "auth_event",
        brokerState: "CONNECTED",
        timestamp: new Date().toISOString()
      });
      console.log("[AUTH] Broker CONNECTED — auth_event broadcast to all clients.");
    } else {
      activeApiKey = "";
      activeAccessToken = "";
    }
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/broker/logout", async (req, res) => {
  activeApiKey = "";
  activeAccessToken = "";
  // [V1.3.1 FIX] Broadcast DISCONNECTED immediately before daemon restart
  // so React updates the UI instantly rather than waiting for the next daemon cycle.
  workstationState.workspaceContext = {
    ...workstationState.workspaceContext,
    brokerState: "DISCONNECTED",
    timestamp: new Date().toISOString()
  };
  broadcastToClients({
    type: "auth_event",
    brokerState: "DISCONNECTED",
    timestamp: new Date().toISOString()
  });
  console.log("[AUTH] Broker DISCONNECTED — auth_event broadcast to all clients.");
  try {
    const result = await sendDaemonRequest("logout");
    // Restart daemon to stop stream and clean mock gateway
    startPythonDaemon();
    res.json(result);
  } catch (err: any) {
    // Even if sendDaemonRequest fails, restart the daemon cleanly
    startPythonDaemon();
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/interpretation/status", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_interpretation_status");
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ status: "unavailable", reason: err.message });
  }
});

app.post("/api/interpretation/generate", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_interpretation");
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/health", (req, res) => {
  const readiness = workstationState.workspace_readiness || workstationState.workspaceReadiness || {};
  const overallState = readiness.overall_state || "DEGRADED";

  res.json({
    status: overallState,
    overall_state: overallState,
    market_session: workstationState.market_session?.status || "UNKNOWN",
    runtime_id: workstationState.runtime_id || null,
    state_sequence: workstationState.state_sequence || 0,
    timestamp: new Date().toISOString(),
    component_readiness: {
      zerodha: workstationState.broker_status?.status || "disconnected",
      market_feed: workstationState.market_feed_status?.status || "offline",
      options: workstationState.option_intelligence?.status || "unavailable",
      news: workstationState.news_intelligence?.status || "unavailable",
      macro: workstationState.macro_intelligence?.usable ? "ready" : "unavailable",
      live_assistant: readiness.live_assistant?.status || "unavailable"
    }
  });
});

app.get("/api/broker/health", (req, res) => {
  const status = workstationState.broker_status?.status || "disconnected";
  res.json({ connection_status: status.toUpperCase(), session_valid: status === "connected", last_successful_update: workstationState.broker_status?.last_successful_update || null });
});

app.get("/api/portfolio", (req, res) => {
  res.json(workstationState.portfolioReport || {});
});

app.get("/api/profile", (req, res) => {
  res.json(workstationState.read_only_account_summary || {});
});

app.get("/api/funds", (req, res) => {
  res.json(workstationState.brokerFunds || {});
});

app.get("/api/holdings", (req, res) => {
  res.json(workstationState.portfolioReport?.holdings || []);
});

app.get("/api/positions", (req, res) => {
  res.json(workstationState.portfolioReport?.positions || { net: [], day: [] });
});

app.get("/api/orders", (req, res) => {
  res.json(workstationState.portfolioReport?.orders || { all_orders: [], completed: [], open_orders: [] });
});

app.get("/api/market", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_market_context");
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/evening-report", (req, res) => {
  res.json(workstationState.evening_report || {});
});

app.get("/api/news", (req, res) => {
  res.json(workstationState.news_intelligence || {});
});

app.get("/api/analytics", (req, res) => {
  res.json(workstationState.analytics_report || {});
});

app.get("/api/dashboard/market-score", (req, res) => {
  res.json(workstationState.market_score || {});
});

app.get("/api/dashboard/opportunity-context", (req, res) => {
  res.json(workstationState.opportunity || {});
});

app.get("/api/dashboard/strategy-evaluation", (req, res) => {
  res.json(workstationState.strategy_suitability || {});
});

app.get("/api/dashboard/confidence-report", (req, res) => {
  res.json(workstationState.confidence || {});
});

app.get("/api/dashboard/risk-report", (req, res) => {
  res.json(workstationState.deterministic_risk || {});
});

app.get("/api/dashboard/decision-report", (req, res) => {
  res.json(workstationState.decision_support || {});
});

app.get("/api/dashboard/operations-report", (req, res) => {
  res.json(workstationState.operations_health || {});
});

app.get("/api/dashboard/configuration-report", (req, res) => {
  res.json(workstationState.configurationReport || {});
});

app.get("/api/dashboard/explanation-report", (req, res) => {
  res.json(workstationState.explanation || {});
});

app.get("/api/planner/trade-plan", (req, res) => {
  res.json(workstationState.tradePlan || {});
});

app.get("/api/planner/intraday-report", (req, res) => {
  res.json(workstationState.intraday_report || {});
});

app.get("/api/planner/validation-report", (req, res) => {
  res.json(workstationState.validation_report || {});
});

app.get("/api/planner/optimization-report", (req, res) => {
  res.json(workstationState.optimization_report || {});
});

app.post("/api/orders/place", rejectReadOnlyMutation("Order placement"));
app.post("/api/orders/modify", rejectReadOnlyMutation("Order modification"));
app.post("/api/orders/cancel", rejectReadOnlyMutation("Order cancellation"));
app.post("/api/positions/exit", rejectReadOnlyMutation("Position exit"));
app.post("/api/paper-trading/:action", rejectReadOnlyMutation("Paper trading"));

let manualRefreshStatus: "idle" | "running" | "completed" | "failed" = "idle";
let lastRefreshTime = 0;
let refreshError: string | null = null;

app.post("/api/news/refresh", async (req, res) => {
  const now = Date.now();
  if (manualRefreshStatus === "running") {
    return res.status(409).json({ status: "running", error: "A refresh is already in progress." });
  }
  if (now - lastRefreshTime < 60000) {
    return res.status(429).json({ status: "rate_limited", error: "Rate limit exceeded. Manual refresh is allowed once per minute." });
  }

  manualRefreshStatus = "running";
  refreshError = null;
  res.json({ status: "running", message: "Refresh initiated." });

  // Execute asynchronously
  (async () => {
    try {
      const result = await sendDaemonRequest("refresh_news");
      if (result && result.success) {
        manualRefreshStatus = "completed";
        lastRefreshTime = Date.now();
        if (result.newsSentiment) {
          workstationState = {
            ...workstationState,
            news_intelligence: result.newsSentiment,
            macro_intelligence: mergeOfficialIndiaEvents(workstationState.macro_intelligence, result.newsSentiment)
          };
          broadcastToClients({ type: "state", data: workstationState });
        }
      } else {
        manualRefreshStatus = "failed";
        refreshError = result?.error || "Daemon failed to refresh news.";
      }
    } catch (err: any) {
      manualRefreshStatus = "failed";
      refreshError = err.message;
    }
  })();
});

app.get("/api/news/refresh/status", (req, res) => {
  res.json({
    status: manualRefreshStatus,
    lastRefreshTime,
    error: refreshError
  });
});

let manualMacroRefreshStatus: "idle" | "running" | "completed" | "failed" = "idle";
let lastMacroRefreshTime = 0;
let macroRefreshError: string | null = null;

app.post("/api/macro/refresh", async (req, res) => {
  const now = Date.now();
  if (manualMacroRefreshStatus === "running") {
    return res.status(409).json({ status: "running", error: "A macro refresh is already in progress." });
  }
  if (now - lastMacroRefreshTime < 60000) {
    return res.status(429).json({ status: "rate_limited", error: "Rate limit exceeded. Manual refresh is allowed once per minute." });
  }

  manualMacroRefreshStatus = "running";
  macroRefreshError = null;
  res.json({ status: "running", message: "Macro refresh initiated." });

  (async () => {
    try {
      const result = await sendDaemonRequest("refresh_macro");
      if (result && result.success) {
        manualMacroRefreshStatus = "completed";
        lastMacroRefreshTime = Date.now();
        if (result.macroIntelligence) {
          workstationState = {
            ...workstationState,
            macro_intelligence: mergeOfficialIndiaEvents(result.macroIntelligence, workstationState.news_intelligence)
          };
          broadcastToClients({ type: "state", data: workstationState });
        }
      } else {
        manualMacroRefreshStatus = "failed";
        macroRefreshError = result?.error || "Daemon failed to refresh macro data.";
      }
    } catch (err: any) {
      manualMacroRefreshStatus = "failed";
      macroRefreshError = err.message;
    }
  })();
});

app.get("/api/macro/refresh/status", (req, res) => {
  res.json({
    status: manualMacroRefreshStatus,
    lastRefreshTime: lastMacroRefreshTime,
    error: macroRefreshError
  });
});

// Vite middleware setup for development, or static serving for production
async function setupVite() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });

  // Attach WebSocket Server
  wss = new WebSocketServer({ noServer: true });

  server.on("upgrade", (request, socket, head) => {
    if (request.url === "/api/ws") {
      wss!.handleUpgrade(request, socket, head, (ws) => {
        wss!.emit("connection", ws, request);
      });
    } else {
      socket.destroy();
    }
  });

  wss.on("connection", (ws: WebSocket) => {
    console.log("React Client connected to Workstation WebSockets");
    // Send current cached state immediately on connection
    ws.send(JSON.stringify({ type: "state", data: workstationState }));

    ws.on("close", () => {
      console.log("React Client disconnected from Workstation WebSockets");
    });
  });
}

setupVite().catch((err) => {
  console.error("Failed to boot Express server:", err);
});
