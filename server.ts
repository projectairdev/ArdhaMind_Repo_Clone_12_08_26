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
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

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

function rejectPendingDaemonRequests(error: Error) {
  pendingRequests.forEach(({ reject }) => reject(error));
  pendingRequests.clear();
}

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
          backend_forward_timestamp: t_forward,
          transport_sent_at: t_forward
        };
        if (!workstationState) workstationState = {} as any;
        if (!workstationState.ticks) workstationState.ticks = {};
        workstationState.ticks[msg.symbol] = tickData;
        broadcastToClients({ type: "tick", symbol: msg.symbol, data: tickData });
      } else if (msg.type === "live_event") {
        const t_forward = new Date().toISOString();
        const eventData = {
          ...msg.data,
          transport_sent_at: t_forward
        };
        broadcastToClients({ type: "live_event", data: eventData });
      } else if (msg.type === "feed_status") {
        broadcastToClients({ type: "feed_status", symbol: msg.symbol, data: msg.data });
      } else if (msg.type === "state") {
        const existingTicks = workstationState?.ticks || {};
        workstationState = { ...(msg.data || {}), ticks: (msg.data && msg.data.ticks) || existingTicks };
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

  pyDaemon.stdin!.on("error", (error) => {
    console.warn(`Python Daemon stdin unavailable: ${error.message}`);
    rejectPendingDaemonRequests(new Error("Python bridge daemon is currently offline"));
  });

  pyDaemon.on("close", (code) => {
    console.warn(`Python Daemon closed with exit code ${code}.`);
    rejectPendingDaemonRequests(new Error(`Python bridge daemon closed with exit code ${code}`));
    pyDaemon = null;
    if (!isShuttingDown) {
      console.log("Respawning Python Daemon in 3 seconds...");
      setTimeout(startPythonDaemon, 3000);
    }
  });
}

let isShuttingDown = false;
function shutdownCleanly(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.log(`Received ${signal}. Shutting down ArdhaMind server cleanly...`);
  if (pyDaemon) {
    try {
      pyDaemon.kill("SIGTERM");
    } catch {}
  }
  process.exit(0);
}

process.on("SIGINT", () => shutdownCleanly("SIGINT"));
process.on("SIGTERM", () => shutdownCleanly("SIGTERM"));
process.on("exit", () => {
  if (pyDaemon) {
    try { pyDaemon.kill("SIGKILL"); } catch {}
  }
});

// Start the daemon process
startPythonDaemon();

function sendDaemonRequest(action: string, params: any = {}, timeoutMs: number = 5000): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!pyDaemon?.stdin?.writable || pyDaemon.stdin.destroyed) {
      return reject(new Error("Python bridge daemon is currently offline"));
    }
    const requestId = `REQ-${++requestCounter}-${Date.now()}`;

    const timer = setTimeout(() => {
      if (pendingRequests.has(requestId)) {
        pendingRequests.delete(requestId);
        reject(new Error(`Python bridge request timed out after ${timeoutMs}ms`));
      }
    }, timeoutMs);

    pendingRequests.set(requestId, {
      resolve: (data: any) => {
        clearTimeout(timer);
        resolve(data);
      },
      reject: (err: any) => {
        clearTimeout(timer);
        reject(err);
      }
    });

    pyDaemon.stdin.write(JSON.stringify({ requestId, action, params }) + "\n", (error) => {
      if (!error) return;
      clearTimeout(timer);
      pendingRequests.delete(requestId);
      reject(new Error(`Python bridge request failed: ${error.message}`));
    });
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
      const targetBrokerState = result?.brokerState || "CONNECTED_VERIFIED";
      workstationState.workspaceContext = {
        ...workstationState.workspaceContext,
        brokerState: targetBrokerState,
        timestamp: new Date().toISOString()
      };
      broadcastToClients({
        type: "auth_event",
        brokerState: targetBrokerState,
        timestamp: new Date().toISOString()
      });
      broadcastToClients({
        type: "phase3_broker_health_updated",
        data: {
          status: targetBrokerState,
          connection_status: targetBrokerState,
          transport_connected: true,
          authenticated: true,
          session_valid: true,
          execution_verified: targetBrokerState === "CONNECTED_VERIFIED",
          reconciliation_complete: targetBrokerState === "CONNECTED_VERIFIED"
        }
      });
      console.log(`[AUTH] Broker canonical publication SUCCESS — auth_event (${targetBrokerState}) broadcast to all clients.`);
      if (req.headers.accept && req.headers.accept.includes("application/json")) {
        return res.json({ success: true, brokerState: targetBrokerState });
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
      const targetBrokerState = result?.brokerState || "CONNECTED_VERIFIED";
      workstationState.workspaceContext = {
        ...workstationState.workspaceContext,
        brokerState: targetBrokerState,
        timestamp: new Date().toISOString()
      };
      broadcastToClients({
        type: "auth_event",
        brokerState: targetBrokerState,
        timestamp: new Date().toISOString()
      });
      broadcastToClients({
        type: "phase3_broker_health_updated",
        data: {
          status: targetBrokerState,
          connection_status: targetBrokerState,
          transport_connected: true,
          authenticated: true,
          session_valid: true,
          execution_verified: targetBrokerState === "CONNECTED_VERIFIED",
          reconciliation_complete: targetBrokerState === "CONNECTED_VERIFIED"
        }
      });
      console.log(`[AUTH] Broker ${targetBrokerState} — auth_event broadcast to all clients.`);
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
  broadcastToClients({
    type: "phase3_broker_health_updated",
    data: {
      status: "DISCONNECTED",
      connection_status: "DISCONNECTED",
      transport_connected: false,
      authenticated: false,
      session_valid: false,
      execution_verified: false,
      reconciliation_complete: false
    }
  });
  console.log("[AUTH] Broker DISCONNECTED — auth_event broadcast to all clients.");
  try {
    const result = await sendDaemonRequest("logout");
    res.json(result);
  } catch (err: any) {
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

app.get("/api/health", async (req, res) => {
  const readiness = workstationState.workspace_readiness || workstationState.workspaceReadiness || {};
  const overallState = readiness.overall_state || "DEGRADED";
  let bStatus = workstationState.broker_status?.normalized_status || workstationState.broker_status?.status;
  if (!bStatus) {
    try {
      const bh = await sendDaemonRequest("get_broker_health");
      if (bh && bh.status) bStatus = bh.status;
    } catch (e) {}
  }

  res.json({
    status: overallState,
    overall_state: overallState,
    market_session: workstationState.market_session?.status || "UNKNOWN",
    runtime_id: workstationState.runtime_id || null,
    state_sequence: workstationState.state_sequence || 0,
    timestamp: new Date().toISOString(),
    component_readiness: {
      zerodha: (bStatus || "disconnected").toLowerCase(),
      market_feed: workstationState.market_feed_status?.status || "offline",
      options: workstationState.option_intelligence?.status || "unavailable",
      news: workstationState.news_intelligence?.status || "unavailable",
      macro: workstationState.macro_intelligence?.usable ? "ready" : "unavailable",
      live_assistant: readiness.live_assistant?.status || "unavailable"
    }
  });
});

app.get("/api/broker/health", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_broker_health");
    if (result && result.status) {
      res.json({
        ...result,
        connection_status: result.status,
        session_valid: result.session_valid ?? false,
        last_successful_update: result.last_verified_at || null
      });
      return;
    }
  } catch (err: any) {
    console.warn("Failed fetching daemon broker health:", err.message);
  }
  if (workstationState.broker_status) {
    const bs = workstationState.broker_status;
    const normStatus = bs.normalized_status || bs.status || "DISCONNECTED";
    res.json({
      ...bs,
      status: normStatus,
      connection_status: normStatus,
      transport_connected: bs.transport_connected ?? (normStatus !== "DISCONNECTED"),
      authenticated: bs.authenticated ?? (normStatus === "CONNECTED_VERIFIED" || normStatus === "BROKER_STATE_UNVERIFIED"),
      session_valid: bs.session_valid ?? (normStatus === "CONNECTED_VERIFIED" || normStatus === "BROKER_STATE_UNVERIFIED"),
      execution_verified: bs.execution_verified ?? (normStatus === "CONNECTED_VERIFIED"),
      reconciliation_complete: bs.reconciliation_complete ?? (normStatus === "CONNECTED_VERIFIED"),
      last_verified_at: bs.last_successful_update || null,
      blocker_code: bs.blocker_code || null
    });
    return;
  }
  const status = "DISCONNECTED";
  res.json({
    status: status,
    connection_status: status,
    transport_connected: false,
    authenticated: false,
    session_valid: false,
    execution_verified: false,
    reconciliation_complete: false,
    last_verified_at: null,
    blocker_code: "BROKER_SERVICE_UNAVAILABLE"
  });
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

// Pre-Market Briefing Endpoints
app.get("/api/pre-market-briefing/current", async (req, res) => {
  try {
    if (workstationState.pre_market_briefing && workstationState.pre_market_briefing.report_id) {
      return res.json(workstationState.pre_market_briefing);
    }
    const result = await sendDaemonRequest("get_pre_market_briefing");
    res.json(result?.briefing || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/pre-market-briefing/history", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_pre_market_briefing_history");
    res.json(result?.history || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/performance/records", async (req, res) => {
  try {
    const targetDate = (req.query.date as string) || new Date().toISOString().split("T")[0];
    const result = await sendDaemonRequest("get_performance_records", { date: targetDate });
    res.json(result?.records || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/performance/history", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_performance_history");
    res.json(result?.history || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/performance/evaluate", async (req, res) => {
  try {
    const { date, session_truth } = req.body || {};
    const result = await sendDaemonRequest("evaluate_performance_records", {
      date: date || new Date().toISOString().split("T")[0],
      session_truth: session_truth || {}
    });
    res.json(result?.records || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/performance/capture", async (req, res) => {
  try {
    const { date, phase, state } = req.body || {};
    const result = await sendDaemonRequest("capture_performance_snapshot", {
      date: date || new Date().toISOString().split("T")[0],
      phase: phase || "LIVE_INTRADAY",
      state: state || workstationState || {}
    });
    res.json(result?.records || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/pre-market-briefing/:date", async (req, res) => {
  try {
    const targetDate = req.params.date;
    const result = await sendDaemonRequest("get_pre_market_briefing", { date: targetDate });
    res.json(result?.briefing || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Staging-only Developer Controls
app.post("/api/pre-market-briefing/generate", async (req, res) => {
  const isProduction = process.env.NODE_ENV === "production" && process.env.VITE_STAGING_MODE !== "true";
  if (isProduction && PORT === 3000) {
    return res.status(403).json({ error: "Staging developer controls are disabled in production." });
  }
  try {
    const result = await sendDaemonRequest("generate_pre_market_briefing", {
      force_freeze: req.body?.force_freeze ?? true,
      force_regenerate: req.body?.force_regenerate ?? true
    });
    if (result?.briefing) {
      workstationState = {
        ...workstationState,
        pre_market_briefing: result.briefing
      };
      broadcastToClients({ type: "state", data: workstationState });
    }
    res.json(result?.briefing || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/pre-market-briefing/validate", async (req, res) => {
  const isProduction = process.env.NODE_ENV === "production" && process.env.VITE_STAGING_MODE !== "true";
  if (isProduction && PORT === 3000) {
    return res.status(403).json({ error: "Staging developer controls are disabled in production." });
  }
  try {
    const result = await sendDaemonRequest("validate_pre_market_briefing", {
      date: req.body?.date,
      is_preview: req.body?.is_preview ?? true
    });
    if (result?.briefing) {
      workstationState = {
        ...workstationState,
        pre_market_briefing: result.briefing
      };
      broadcastToClients({ type: "state", data: workstationState });
    }
    res.json(result?.briefing || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Post-Market Briefing API Endpoints
app.get("/api/post-market-briefing/current", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_post_market_briefing", {});
    res.json(result?.data || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/post-market-briefing/history", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_post_market_briefing_history", {});
    res.json(result?.history || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/post-market-briefing/:date", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_post_market_briefing", { trading_date: req.params.date });
    res.json(result?.data || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/post-market-briefing/reconcile", async (req, res) => {
  try {
    const result = await sendDaemonRequest("reconcile_post_market_briefing", { trading_date: req.body?.date });
    res.json(result?.data || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Intelligence Sprint I1 Actionable Opportunities Endpoints
app.get("/api/intelligence/opportunities/current", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_intelligence_opportunities", {});
    res.json(result?.data || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/intelligence/opportunities/history", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_intelligence_opportunity_history", { date: req.query.date });
    res.json(result?.data || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Phase 3 Trade Proposal & Approval State Machine Endpoints
app.get("/api/phase3/proposals/active", async (_req, res) => {
  try {
    const result = await sendDaemonRequest("get_active_proposal");
    res.json(result?.proposal || { state: "NO_TRADE", contract_symbol: "NO ACTIVE PROPOSAL" });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/proposals/:id/validate", async (req, res) => {
  try {
    const result = await sendDaemonRequest("validate_proposal", { proposal_id: req.params.id });
    if (result?.proposal) {
      broadcastToClients({ type: "phase3_proposal", data: result.proposal });
    }
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/proposals/:id/margin", async (req, res) => {
  try {
    const lots = req.body?.lots ? parseInt(req.body.lots, 10) : 1;
    const product = req.body?.product || "NRML";
    const result = await sendDaemonRequest("calculate_proposal_margin", {
      proposal_id: req.params.id,
      lots,
      product
    });
    if (result?.proposal) {
      broadcastToClients({ type: "phase3_proposal", data: result.proposal });
    }
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message, status: "MARGIN_UNAVAILABLE" });
  }
});

app.post("/api/phase3/proposals/:id/approve", async (req, res) => {
  try {
    const lots = req.body?.lots ? parseInt(req.body.lots, 10) : undefined;
    const product = req.body?.product || undefined;
    const result = await sendDaemonRequest("approve_proposal", {
      proposal_id: req.params.id,
      lots,
      product
    });
    if (result?.proposal) {
      broadcastToClients({ type: "phase3_proposal", data: result.proposal });
    }
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/proposals/:id/reject", async (req, res) => {
  try {
    const result = await sendDaemonRequest("reject_proposal", {
      proposal_id: req.params.id,
      reason: req.body?.reason || "Trader rejected proposal"
    });
    if (result?.proposal) {
      broadcastToClients({ type: "phase3_proposal", data: result.proposal });
    }
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/proposals/audit", async (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 50;
    const result = await sendDaemonRequest("get_proposal_audits", { limit });
    res.json(result?.audits || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ── PHASE 3 MILESTONE 3: LIVE BROKER EXECUTION & RECONCILIATION ──

app.post("/api/phase3/orders/execute", async (req, res) => {
  try {
    const isLiveEnabled = process.env.ENABLE_LIVE_EXECUTION === "true";
    if (!isLiveEnabled) {
      return res.status(403).json({
        success: false,
        error: "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
        code: "LIVE_EXECUTION_DISABLED"
      });
    }

    const { proposal_id, intent_id, lots, product } = req.body || {};
    const result = await sendDaemonRequest("execute_live_order", {
      proposal_id,
      intent_id,
      lots: lots ? parseInt(lots, 10) : 1,
      product: product || "NRML"
    });

    if (result?.order) {
      broadcastToClients({ type: "phase3_order_updated", data: result.order });
    }
    if (result?.proposal) {
      broadcastToClients({ type: "phase3_proposal", data: result.proposal });
    }

    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/orders/active", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_active_orders", {});
    res.json(result?.orders || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/orders/recent", async (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 50;
    const result = await sendDaemonRequest("get_recent_orders", { limit });
    res.json(result?.orders || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/orders/:id/events", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_order_events", { order_id: req.params.id });
    res.json(result?.events || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/positions", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_live_positions", {});
    res.json(result?.positions || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/positions/all", async (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 50;
    const result = await sendDaemonRequest("get_all_positions", { limit });
    res.json(result?.positions || []);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/orders/:id/cancel", async (req, res) => {
  try {
    const isLiveEnabled = process.env.ENABLE_LIVE_EXECUTION === "true";
    if (!isLiveEnabled) {
      return res.status(403).json({
        success: false,
        error: "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
        code: "LIVE_EXECUTION_DISABLED"
      });
    }

    const { idempotency_key } = req.body || {};
    const result = await sendDaemonRequest("cancel_order", {
      order_id: req.params.id,
      idempotency_key
    });

    // Trigger immediate reconciliation and broadcast
    const recon = await sendDaemonRequest("reconcile_orders", {});
    if (recon?.updated_orders) {
      recon.updated_orders.forEach((ord: any) => {
        broadcastToClients({ type: "phase3_order_updated", data: ord });
      });
    }

    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/positions/:id/exit", async (req, res) => {
  try {
    const isLiveEnabled = process.env.ENABLE_LIVE_EXECUTION === "true";
    if (!isLiveEnabled) {
      return res.status(403).json({
        success: false,
        error: "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
        code: "LIVE_EXECUTION_DISABLED"
      });
    }

    const { idempotency_key, quantity, order_type, price } = req.body || {};
    const result = await sendDaemonRequest("exit_position", {
      position_id: req.params.id,
      idempotency_key,
      quantity,
      order_type: order_type || "MARKET",
      price
    });

    // Immediate reconciliation
    const recon = await sendDaemonRequest("reconcile_orders", {});
    if (recon?.open_positions) {
      broadcastToClients({ type: "phase3_positions_updated", data: recon.open_positions });
    }

    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/positions/exit-all", async (req, res) => {
  try {
    const isLiveEnabled = process.env.ENABLE_LIVE_EXECUTION === "true";
    if (!isLiveEnabled) {
      return res.status(403).json({
        success: false,
        error: "Live execution is disabled. Set ENABLE_LIVE_EXECUTION=true in staging environment.",
        code: "LIVE_EXECUTION_DISABLED"
      });
    }

    const { idempotency_key } = req.body || {};
    const result = await sendDaemonRequest("emergency_close_all", {
      idempotency_key
    });

    // Immediate reconciliation
    const recon = await sendDaemonRequest("reconcile_orders", {});
    if (recon?.open_positions) {
      broadcastToClients({ type: "phase3_positions_updated", data: recon.open_positions });
    }

    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/orders/reconcile", async (req, res) => {
  try {
    const result = await sendDaemonRequest("reconcile_orders", {});
    if (result?.updated_orders && result.updated_orders.length > 0) {
      result.updated_orders.forEach((ord: any) => {
        broadcastToClients({ type: "phase3_order_updated", data: ord });
      });
    }
    if (result?.open_positions) {
      broadcastToClients({ type: "phase3_positions_updated", data: result.open_positions });
    }
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ── MILESTONE 5: EXECUTION JOURNAL & PERFORMANCE LINEAGE ──

app.get("/api/phase3/journal", async (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 50;
    const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : 0;
    const date_from = req.query.date_from as string;
    const date_to = req.query.date_to as string;
    const symbol = req.query.symbol as string;
    const setup_type = req.query.setup_type as string;
    const result_filter = req.query.result_filter as string;

    const result = await sendDaemonRequest("get_journal_entries", {
      limit,
      offset,
      date_from,
      date_to,
      symbol,
      setup_type,
      result_filter
    });
    res.json(result || { entries: [], total: 0 });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/journal/analytics/summary", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_journal_analytics", {});
    res.json(result?.summary || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/phase3/journal/:id", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_journal_entry", {
      journal_id: req.params.id
    });
    if (!result?.entry) {
      return res.status(404).json({ error: "Journal entry not found" });
    }
    res.json(result.entry);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/journal/:id/notes", async (req, res) => {
  try {
    const { note_text, tags } = req.body || {};
    const result = await sendDaemonRequest("add_journal_note", {
      journal_id: req.params.id,
      note_text,
      tags: tags || []
    });
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ── MILESTONE 6: EXECUTION SAFETY & CIRCUIT BREAKERS ──

app.get("/api/phase3/safety/status", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_safety_status", {});
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/phase3/safety/kill-switch", async (req, res) => {
  try {
    const { active } = req.body || {};
    const result = await sendDaemonRequest("toggle_kill_switch", { active: Boolean(active) });
    broadcastToClients({ type: "phase3_safety_updated", data: result });
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ── MILESTONE 7: CONSOLIDATED EXECUTION STATE SNAPSHOT ──

app.get("/api/phase3/state", async (req, res) => {
  try {
    const result = await sendDaemonRequest("get_phase3_state", {});
    res.json(result || {});
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Periodic background reconciler (every 3 seconds)
setInterval(async () => {
  try {
    const result = await sendDaemonRequest("reconcile_orders", {});
    if (result?.updated_orders && result.updated_orders.length > 0) {
      result.updated_orders.forEach((ord: any) => {
        broadcastToClients({ type: "phase3_order_updated", data: ord });
      });
    }
  } catch {}
}, 3000);

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

app.post("/api/live-assistant/query", async (req, res) => {
  try {
    const message = req.body?.message || req.body?.prompt || "";
    const conversation_id = req.body?.conversation_id || "default";
    const provider = req.body?.provider;
    
    if (!message) {
      return res.status(400).json({ error: "Message/prompt parameter is required." });
    }

    let effectiveState = workstationState;
    if (process.env.ALLOW_TEST_STATE_OVERRIDE === "true" || process.env.PYTEST_CURRENT_TEST) {
      effectiveState = req.body?.workstation_state || workstationState;
    }

    const daemonResult = await sendDaemonRequest("live_assistant_query", {
      message,
      conversation_id,
      provider,
      workstation_state: effectiveState
    });

    if (daemonResult && daemonResult.success) {
      return res.json(daemonResult.result);
    } else {
      return res.status(500).json({ error: daemonResult?.error || "Daemon failed to process query." });
    }
  } catch (err: any) {
    console.error("Live assistant query error:", err);
    return res.status(500).json({ error: err.message || "Failed to process live assistant query." });
  }
});

app.post("/api/macro/refresh", async (req, res) => {
  const now = Date.now();
  const targetKeys: string[] = Array.isArray(req.body?.keys) ? req.body.keys : (req.body?.key ? [req.body.key] : []);

  if (manualMacroRefreshStatus === "running" && targetKeys.length === 0) {
    return res.status(409).json({ status: "running", error: "A master macro refresh is already in progress." });
  }
  if (targetKeys.length === 0 && now - lastMacroRefreshTime < 60000) {
    return res.status(429).json({ status: "rate_limited", error: "Rate limit exceeded. Manual master refresh is allowed once per minute." });
  }

  manualMacroRefreshStatus = "running";
  macroRefreshError = null;
  res.json({ status: "running", message: targetKeys.length > 0 ? `Macro refresh initiated for ${targetKeys.join(", ")}.` : "Master macro refresh initiated." });

  (async () => {
    try {
      const result = await sendDaemonRequest("refresh_macro", { keys: targetKeys });
      if (result && result.success) {
        manualMacroRefreshStatus = "completed";
        if (targetKeys.length === 0) {
          lastMacroRefreshTime = Date.now();
        }
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
  const isProduction = process.env.NODE_ENV === "production" || fs.existsSync(path.join(process.cwd(), "dist/index.html"));
  if (!isProduction) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      if (req.path.startsWith("/api/")) {
        return res.status(404).json({ error: "API endpoint not found" });
      }
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
