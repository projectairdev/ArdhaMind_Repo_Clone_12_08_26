/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * CatalystsTab.tsx
 * Canonical wrapper for CatalystsMatrixView.
 */

import React from "react";
import { NewsPresentationState } from "../../utils/canonicalNewsAdapter";
import { CatalystsMatrixView } from "./CatalystsMatrixView";

export function CatalystsTab({ pres }: { pres: NewsPresentationState }) {
  return <CatalystsMatrixView pres={pres} />;
}

export default CatalystsTab;
