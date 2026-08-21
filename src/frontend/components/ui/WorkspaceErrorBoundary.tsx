import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export interface WorkspaceErrorBoundaryProps {
  children: ReactNode;
  workspaceName?: string;
}

export interface WorkspaceErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class WorkspaceErrorBoundary extends Component<WorkspaceErrorBoundaryProps, WorkspaceErrorBoundaryState> {
  // @ts-ignore
  state: WorkspaceErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  static getDerivedStateFromError(error: Error): WorkspaceErrorBoundaryState {
    return { hasError: true, error };
  }

  // @ts-ignore
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[WORKSPACE ERROR BOUNDARY - ${(this as any).props?.workspaceName || "UNKNOWN"}]`, error, errorInfo);
  }

  handleRetry = () => {
    (this as any).setState({ hasError: false, error: null });
  };

  render() {
    const state = (this as any).state as WorkspaceErrorBoundaryState;
    const props = (this as any).props as WorkspaceErrorBoundaryProps;

    if (state?.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[300px] p-6 bg-[#0E1013] border border-[#242830] rounded-[2px] font-mono text-center space-y-3 text-[#e6e8eb]">
          <div className="p-3 bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#ef4444] rounded-[2px]">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#e6e8eb]">
            {props.workspaceName || "Workspace"} Encountered A Runtime Exception
          </h2>
          <p className="text-xs text-[#94a3b8] max-w-md">
            The workstation shell prevented an application outage. Other workspaces and system controls remain active.
          </p>
          {state.error && (
            <div className="text-[10px] text-[#ef4444] bg-[#13161A] border border-[#242830] p-2 rounded-[2px] max-w-lg overflow-x-auto text-left font-mono">
              {state.error.toString()}
            </div>
          )}
          <button
            onClick={this.handleRetry}
            className="px-3 py-1.5 bg-[#06b6d4]/10 hover:bg-[#06b6d4]/20 border border-[#06b6d4]/40 text-[#06b6d4] text-xs font-bold rounded-[2px] transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reload Workspace
          </button>
        </div>
      );
    }

    return props.children;
  }
}
