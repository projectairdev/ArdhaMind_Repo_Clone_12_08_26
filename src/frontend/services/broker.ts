// src/frontend/services/broker.ts
import {
  BrokerAccount,
  BrokerFunds,
  BrokerPosition,
  BrokerHolding,
  BrokerOrder,
  ExecutionReport,
  ExecutionOrder,
} from "../types";

export interface LivePortfolioReport {
  account_profile: {
    client_id: string;
    client_name: string;
    email: string;
    pan: string;
    broker_name: string;
    user_type: string;
    login_time: string;
  };
  funds: {
    equity: {
      available_cash: number;
      utilized_margin: number;
      available_margin: number;
      opening_balance: number;
      collateral: number;
      payin_amount: number;
      payout_amount: number;
    };
    commodity: {
      available_cash: number;
      utilized_margin: number;
      available_margin: number;
      opening_balance: number;
      collateral: number;
      payin_amount: number;
      payout_amount: number;
    };
  };
  holdings: Array<{
    symbol: string;
    exchange: string;
    quantity: number;
    average_price: number;
    current_price: number;
    current_value: number;
    unrealized_pnl: number;
    day_change: number;
    day_change_pct: number;
  }>;
  positions: {
    net: Array<{
      symbol: string;
      product: string;
      exchange: string;
      quantity: number;
      buy_quantity: number;
      sell_quantity: number;
      average_price: number;
      last_price: number;
      mtm: number;
      unrealized_pnl: number;
      realized_pnl: number;
    }>;
    day: Array<{
      symbol: string;
      product: string;
      exchange: string;
      quantity: number;
      buy_quantity: number;
      sell_quantity: number;
      average_price: number;
      last_price: number;
      mtm: number;
      unrealized_pnl: number;
      realized_pnl: number;
    }>;
  };
  orders: {
    all_orders: BrokerOrder[];
    completed: BrokerOrder[];
    open_orders: BrokerOrder[];
  };
  trades: Array<{
    trade_id: string;
    order_id: string;
    symbol: string;
    exchange: string;
    transaction_type: "BUY" | "SELL";
    quantity: number;
    execution_price: number;
    timestamp: string;
  }>;
  statistics: {
    total_holdings_value: number;
    total_unrealized_pnl: number;
    total_realized_pnl: number;
    today_mtm: number;
    total_margin_utilized: number;
    available_cash: number;
  };
  timestamp: string;
  broker_health: {
    broker_name: string;
    connection_status: string;
    trading_mode: string;
    latency: number;
    authentication_status: string;
    last_heartbeat: string;
    instrument_cache_status: string;
    market_status: string;
    health_score: number;
    last_error: string | null;
    session_valid: boolean;
    broker_version: string;
    api_status: string;
  };
  sync_status: "SUCCESS" | "FAILED";
}

export async function getBrokerAccount(): Promise<BrokerAccount> {
  const resp = await fetch("/api/profile");
  const data = await resp.json();
  return {
    name: data.client_name || data.user_name || "N/A",
    client_id: data.client_id || "N/A",
    email: data.email || "N/A",
    broker: data.broker_name || data.broker || "N/A"
  };
}

export interface BrokerConfig {
  api_key: string;
  access_token_saved: boolean;
}

export async function getBrokerConfig(): Promise<BrokerConfig> {
  const resp = await fetch("/api/broker/config");
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

export async function connectBroker(
  apiKey: string,
  accessToken: string,
  persistKey: boolean,
  persistToken: boolean
): Promise<any> {
  const resp = await fetch("/api/broker/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      api_key: apiKey,
      access_token: accessToken,
      persist_key: persistKey,
      persist_token: persistToken,
    }),
  });
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

export async function setRuntimeLiveTradingAllowed(allowLiveTrading: boolean): Promise<boolean> {
  const resp = await fetch("/api/workspace/runtime-flags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ allowLiveTrading }),
  });
  const data = await resp.json();
  return Boolean(data.allowLiveTrading);
}

export async function getBrokerFunds(): Promise<BrokerFunds> {
  const resp = await fetch("/api/funds");
  const data = await resp.json();
  return {
    available_cash: data.available_cash || 0.0,
    margins: data.margins || 0.0,
    utilized_margin: data.utilized_margin || 0.0,
    available_margin: data.available_margin || 0.0
  };
}

export async function getBrokerPositions(): Promise<BrokerPosition[]> {
  const resp = await fetch("/api/positions");
  return resp.json();
}

export async function getBrokerHoldings(): Promise<BrokerHolding[]> {
  const resp = await fetch("/api/holdings");
  return resp.json();
}

export async function getBrokerOrders(): Promise<BrokerOrder[]> {
  const resp = await fetch("/api/orders");
  return resp.json();
}

export async function getLivePortfolioReport(forceRefresh = false): Promise<LivePortfolioReport> {
  const resp = await fetch("/api/portfolio");
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

export async function executeOrder(order: ExecutionOrder): Promise<ExecutionReport> {
  const resp = await fetch("/api/orders/place", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol: order.tradingsymbol,
      transaction_type: order.transaction_type,
      quantity: order.quantity,
      product: order.product || "NRML",
      order_type: order.order_type || "MARKET",
      price: order.price,
      exchange: order.exchange || "NSE"
    })
  });
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return {
    report_id: "EXE_" + Math.floor(Math.random() * 100000),
    request_id: "REQ_" + Math.floor(Math.random() * 100000),
    submitted_orders: [order],
    accepted_orders: [order],
    rejected_orders: [],
    broker_order_id: data.order_id || "N/A",
    exchange_order_id: "EXE_" + Math.floor(Math.random() * 100000),
    timestamp: new Date().toISOString(),
    failure_reason: "",
    status: "COMPLETED"
  };
}

export async function exitPosition(symbol: string, product: string): Promise<any> {
  const resp = await fetch("/api/positions/exit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, product })
  });
  return resp.json();
}
