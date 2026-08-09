// src/frontend/components/OpenAIInterpretationBadge.tsx
import React, { useEffect, useState } from "react";
import { Sparkles, AlertTriangle, ShieldCheck } from "lucide-react";

export function OpenAIInterpretationBadge() {
  const [statusInfo, setStatusInfo] = useState<{ status: string; reason: string }>({
    status: "disabled",
    reason: "Initializing..."
  });

  useEffect(() => {
    fetch("/api/interpretation/status")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.status) {
          setStatusInfo({ status: data.status, reason: data.reason || "" });
        }
      })
      .catch(() => {
        setStatusInfo({ status: "unavailable", reason: "API bridge unreachable" });
      });
  }, []);

  const st = statusInfo.status.toLowerCase();
  const colorClass =
    st === "available"
      ? "bg-emerald-950/80 text-emerald-400 border-emerald-800"
      : st === "degraded"
      ? "bg-amber-950/80 text-amber-400 border-amber-800"
      : "bg-slate-900 text-slate-400 border-slate-800";

  return (
    <span
      title={statusInfo.reason}
      className={`px-2.5 py-1 rounded border text-[10px] font-mono font-bold flex items-center gap-1.5 uppercase ${colorClass}`}
    >
      <Sparkles size={12} className={st === "available" ? "text-emerald-400 animate-pulse" : "text-slate-400"} />
      AI Layer: {st}
    </span>
  );
}
