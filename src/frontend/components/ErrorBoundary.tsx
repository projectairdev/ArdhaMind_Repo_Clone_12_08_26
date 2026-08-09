// src/frontend/components/ErrorBoundary.tsx
import React, { useState, useEffect, ReactNode } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

export function ErrorBoundary({ children, fallbackTitle }: Props) {
  const [hasError, setHasError] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string>("");

  useEffect(() => {
    const handleErr = (event: ErrorEvent) => {
      setHasError(true);
      setErrorMsg(event.message || "Component rendering error");
    };
    window.addEventListener("error", handleErr);
    return () => window.removeEventListener("error", handleErr);
  }, []);

  if (hasError) {
    return (
      <div className="p-5 bg-slate-950 border border-amber-900/60 rounded-xl space-y-3 text-left font-sans">
        <div className="flex items-center gap-2 text-amber-400 font-mono font-bold text-xs">
          <AlertCircle size={16} />
          <span>{fallbackTitle || "Component Intelligence Degraded"}</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed font-mono">
          {errorMsg || "An unexpected rendering error occurred in this workspace component."}
        </p>
        <button
          onClick={() => {
            setHasError(false);
            setErrorMsg("");
          }}
          className="px-3 py-1 bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-mono rounded text-slate-200 transition flex items-center gap-1.5"
        >
          <RefreshCw size={12} /> Reset Component
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
