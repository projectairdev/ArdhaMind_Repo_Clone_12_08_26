/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Provenance Popover & Details Modal.
 * Exposes data lineage, exact source timestamps, provider, and revision metadata.
 */

import React, { useState } from "react";
import { Info, Database, Clock, Layers, ShieldCheck } from "lucide-react";
import { DataQualityStatus } from "../../../types/canonical";

export interface ProvenanceDetails {
  provider: string;
  sourceType: string;
  exchangeTimestamp?: string | null;
  receivedAt?: string | null;
  sessionDate: string;
  stateRevision?: number;
  quality: DataQualityStatus;
  notes?: string;
}

export function ProvenancePopover({ details }: { details: ProvenanceDetails }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        title="View provenance & data lineage"
        className="p-1 text-[#707987] hover:text-[#38BDF8] transition-colors rounded hover:bg-[#1E232B]"
      >
        <Info className="w-3.5 h-3.5" />
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 top-6 z-50 w-72 rounded-md border border-[#2A313C] bg-[#12151A] p-3 text-[11px] font-mono shadow-2xl backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-[#222832] pb-2 mb-2">
              <span className="font-bold text-[#E6E8EB] flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#38BDF8]" />
                Data Provenance
              </span>
              <span className="px-1.5 py-0.5 rounded bg-[#1C2128] text-[9px] text-[#A5ABB4] border border-[#2B333E]">
                REV #{details.stateRevision || 0}
              </span>
            </div>

            <div className="space-y-1.5 text-[#A5ABB4]">
              <div className="flex justify-between">
                <span className="text-[#707987]">Provider:</span>
                <span className="font-semibold text-[#E6E8EB]">{details.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#707987]">Source Type:</span>
                <span className="text-[#E6E8EB]">{details.sourceType}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#707987]">Session Date:</span>
                <span className="text-[#E6E8EB]">{details.sessionDate}</span>
              </div>
              {details.exchangeTimestamp && (
                <div className="flex justify-between">
                  <span className="text-[#707987]">Exchange Time:</span>
                  <span className="text-[#E6E8EB]">{details.exchangeTimestamp.slice(11, 19)} IST</span>
                </div>
              )}
              {details.receivedAt && (
                <div className="flex justify-between">
                  <span className="text-[#707987]">Received At:</span>
                  <span className="text-[#E6E8EB]">{details.receivedAt.slice(11, 19)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[#707987]">Quality Status:</span>
                <span className={details.quality === "VALID" ? "text-[#00C896] font-bold" : "text-[#F59E0B] font-bold"}>
                  {details.quality}
                </span>
              </div>
            </div>

            {details.notes && (
              <div className="mt-2.5 pt-2 border-t border-[#222832] text-[10px] text-[#707987] italic">
                {details.notes}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
