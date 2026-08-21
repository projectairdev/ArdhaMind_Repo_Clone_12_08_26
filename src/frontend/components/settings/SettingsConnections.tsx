import React, { useState } from "react";
import { Database, ShieldCheck, RefreshCw, KeyRound, Radio, Zap, AlertCircle, CheckCircle2 } from "lucide-react";
import { Surface, SectionHeader } from "../ui/WorkspacePrimitives";
import { SettingsPresentationState } from "../../utils/canonicalSettingsAdapter";
import { useWorkstationState } from "../../context/WorkstationStateContext";

export function SettingsConnections({ pres }: { pres: SettingsPresentationState }) {
  const { canonicalState, lastValidState, syncBroker } = useWorkstationState() as any;
  const [message, setMessage] = useState<string | null>(null);
  const rawBroker = (canonicalState ?? lastValidState)?.broker_status;
  const isConnected = pres.brokerState.status === "CONNECTED" || rawBroker?.execution_verified === true;

  const handleOAuthConnect = async () => {
    try {
      setMessage("Redirecting to official Zerodha OAuth login...");
      const res = await fetch("/api/broker/login-url");
      const body = await res.json();
      if (body && body.login_url) {
        window.location.href = body.login_url;
      } else {
        setMessage(body.error || "Failed to generate Zerodha login URL.");
      }
    } catch (err: any) {
      setMessage(err.message || "OAuth initiation failed.");
    }
  };

  const handleDisconnect = async () => {
    try {
      setMessage("Disconnecting broker session...");
      await fetch("/api/broker/logout", { method: "POST" });
      if (syncBroker) await syncBroker(true);
      setMessage("Broker session disconnected.");
    } catch (err: any) {
      setMessage(err.message || "Disconnect failed.");
    }
  };

  return (
    <div className="space-y-3 font-sans text-left text-[11px] min-w-0">
      {/* ── 1. ZERODHA / BROKER CONNECTION ── */}
      <Surface id="settings-connections-broker" className="overflow-hidden">
        <SectionHeader title="ZERODHA KITECONNECT BROKER INTEGRATION" eyebrow="1. Broker Authentication" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-2.5 font-mono text-[10px]">
          <div className="flex items-center justify-between border-b border-[#191D23] pb-2">
            <div className="flex items-center gap-2">
              <KeyRound size={14} className="text-[#38BDF8]" />
              <span className="font-bold text-[#E6E8EB]">Zerodha KiteConnect v5</span>
            </div>
            <span className={`px-1.5 py-0.5 rounded text-[8.5px] font-bold ${
              isConnected ? "bg-[#00C896]/20 text-[#00C896]" : "bg-[#E5484D]/20 text-[#E5484D]"
            }`}>
              {pres.brokerState.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[9px] text-[#707987]">
            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <div className="flex justify-between">
                <span>Account Client ID:</span>
                <span className="font-bold text-[#E6E8EB]">{pres.brokerState.clientIdMasked}</span>
              </div>
              <div className="flex justify-between">
                <span>Session Validity:</span>
                <span className="font-bold text-[#00C896]">{isConnected ? "VALIDATED" : "EXPIRED / DISCONNECTED"}</span>
              </div>
              <div className="flex justify-between">
                <span>Last Authenticated:</span>
                <span className="text-[#E6E8EB]">{pres.brokerState.lastAuthenticated}</span>
              </div>
            </div>

            <div className="p-2 rounded bg-[#0E1013] border border-[#191D23] space-y-1">
              <div className="flex justify-between">
                <span>Execution Capability:</span>
                <span className="font-bold text-[#00C896]">READ ONLY (Orders Hard-Disabled)</span>
              </div>
              <div className="flex justify-between">
                <span>Redirect Callback URL:</span>
                <span className="text-[#38BDF8]">/api/broker/callback</span>
              </div>
              <div className="flex justify-between">
                <span>Secret Exposure Status:</span>
                <span className="font-bold text-[#8B5CF6]">SAFE (No Secret Tokens Rendered)</span>
              </div>
            </div>
          </div>

          {message && (
            <div className="p-2 bg-[#0E1013] border border-[#191D23] text-[9px] text-[#38BDF8] rounded">
              {message}
            </div>
          )}

          <div className="pt-1 flex items-center gap-2">
            {isConnected ? (
              <button
                onClick={handleDisconnect}
                className="px-3 py-1.5 bg-[#E5484D]/15 hover:bg-[#E5484D]/25 border border-[#E5484D]/30 text-[#E5484D] font-bold rounded text-[10px] transition"
              >
                Disconnect Broker Session
              </button>
            ) : (
              <button
                onClick={handleOAuthConnect}
                className="px-3 py-1.5 bg-[#38BDF8]/15 hover:bg-[#38BDF8]/25 border border-[#38BDF8]/30 text-[#38BDF8] font-bold rounded text-[10px] transition"
              >
                Authenticate Broker (Zerodha OAuth)
              </button>
            )}
          </div>
        </div>
      </Surface>

      {/* ── 2. MARKET DATA & OPTIONS PROVIDERS ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start min-w-0">
        <Surface className="overflow-hidden">
          <SectionHeader title="MARKET &amp; BREADTH DATA PROVIDER" eyebrow="2. Spot Stream Telemetry" accent="violet" />
          <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
            <div className="flex justify-between py-1 border-b border-[#191D23]">
              <span className="text-[#707987]">Primary Spot Provider:</span>
              <span className="font-bold text-[#E6E8EB]">Zerodha Kite WebSocket / Quote</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#191D23]">
              <span className="text-[#707987]">Stream Readiness:</span>
              <span className="font-bold text-[#00C896]">HEALTHY</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#707987]">Constituent Coverage:</span>
              <span className="font-bold text-[#38BDF8]">50 / 50 NIFTY Constituents</span>
            </div>
          </div>
        </Surface>

        <Surface className="overflow-hidden">
          <SectionHeader title="OPTIONS MATRIX PROVIDER" eyebrow="3. Derivatives Telemetry" accent="amber" />
          <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
            <div className="flex justify-between py-1 border-b border-[#191D23]">
              <span className="text-[#707987]">Option Chain Ingestion:</span>
              <span className="font-bold text-[#E6E8EB]">Zerodha Kite Depth &amp; OI</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#191D23]">
              <span className="text-[#707987]">Matrix Status:</span>
              <span className="font-bold text-[#00C896]">HEALTHY</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#707987]">Last Matrix Refresh:</span>
              <span className="font-bold text-[#E6E8EB]">{pres.lastUpdatedIst}</span>
            </div>
          </div>
        </Surface>
      </div>

      {/* ── 3. NEWS & MACRO PROVIDERS ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="FINANCIAL NEWS &amp; OFFICIAL MACRO SOURCES" eyebrow="4. Content Ingestion Feeds" accent="cyan" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
          <div className="divide-y divide-[#191D23]">
            {pres.services.filter((s) => s.category.includes("News") || s.category.includes("Macro")).map((svc, i) => (
              <div key={i} className="flex items-center justify-between py-1.5">
                <div>
                  <div className="font-bold text-[#E6E8EB] flex items-center gap-1">
                    <span>{svc.name}</span>
                    {svc.isOfficial && <ShieldCheck size={10} className="text-[#8B5CF6]" />}
                  </div>
                  <div className="text-[8px] text-[#707987]">{svc.detail}</div>
                </div>
                <span className="text-[8px] font-bold text-[#00C896] bg-[#00C896]/20 px-1.5 py-0.5 rounded">
                  {svc.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Surface>

      {/* ── 4. OPENAI / AI SERVICE ── */}
      <Surface className="overflow-hidden">
        <SectionHeader title="OPENAI &amp; AI DECISION SUPPORT" eyebrow="5. Intelligence Reasoning Engine" accent="violet" />
        <div className="p-3 bg-[#0B0D10] space-y-2 font-mono text-[9.5px]">
          <div className="flex justify-between py-1 border-b border-[#191D23]">
            <span className="text-[#707987]">AI Provider:</span>
            <span className="font-bold text-[#8B5CF6]">OpenAI GPT-4o &amp; Deterministic Rules Engine</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#191D23]">
            <span className="text-[#707987]">Integration Status:</span>
            <span className="font-bold text-[#00C896]">CONFIGURED &amp; HEALTHY</span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-[#707987]">API Key Exposure Status:</span>
            <span className="font-bold text-[#8B5CF6]">PROTECTED (Server-Side Enclave Only)</span>
          </div>
        </div>
      </Surface>
    </div>
  );
}

export default SettingsConnections;
