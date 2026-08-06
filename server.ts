import express from "express";
import path from "path";
import fs from "fs";
import { spawn, ChildProcess } from "child_process";
import readline from "readline";
import { createServer as createViteServer } from "vite";
import { WebSocketServer, WebSocket } from "ws";

const app = express();
const PORT = 3000;

app.use(express.json());

// Persistent state for workspace mode in-memory (defaults to LIVE_PRACTICE)
let activeWorkspaceMode = process.env.WORKSPACE_MODE || "LIVE_PRACTICE";

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
    executionMode: "PAPER_EXECUTION",
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
    KITE_API_KEY: activeApiKey,
    KITE_ACCESS_TOKEN: activeAccessToken,
    PREFERRED_TRADING_STYLE: process.env.PREFERRED_TRADING_STYLE || "Intraday"
  };

  let pythonCmd = process.platform === "win32" ? "python" : "python3";
  const venvPath = process.platform === "win32"
    ? path.join(process.cwd(), ".venv/Scripts/python.exe")
    : path.join(process.cwd(), ".venv/bin/python");
  if (fs.existsSync(venvPath)) {
    pythonCmd = venvPath;
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
        workstationState = {
          ...workstationState,
          ...msg.data,
          ticks: workstationState.ticks
        };
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

app.get("/api/broker/health", (req, res) => {
  res.json(workstationState.portfolioReport?.broker_health || { connection_status: "DISCONNECTED", session_valid: false });
});

app.get("/api/portfolio", (req, res) => {
  res.json(workstationState.portfolioReport || {});
});

app.get("/api/profile", (req, res) => {
  res.json(workstationState.brokerAccount || {});
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

app.post("/api/orders/place", (_req, res) => {
  res.status(410).json({ error: "Order placement is unavailable: AIR ArdhaMind is read only." });
});

app.post("/api/positions/exit", (_req, res) => {
  res.status(410).json({ error: "Position exits are unavailable: AIR ArdhaMind is read only." });
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
