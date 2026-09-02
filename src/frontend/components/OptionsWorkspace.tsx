import React from "react";
import { OptionsIntelligenceWorkspace } from "./canonical/OptionsIntelligenceWorkspace";
import { useCanonicalState } from "../context/CanonicalStateContext";

export function OptionsWorkspace() {
  const { envelope } = useCanonicalState();
  return (
    <OptionsIntelligenceWorkspace
      options={envelope.options}
      candidateStrike={envelope.decision?.strike_candidates?.[0]}
    />
  );
}

export default OptionsWorkspace;
