/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * LiveNewsTab.tsx
 * Canonical wrapper for LiveNewsFeedView.
 */

import React from "react";
import { NewsPresentationState } from "../../utils/canonicalNewsAdapter";
import { LiveNewsFeedView } from "./LiveNewsFeedView";

export function LiveNewsTab({
  pres,
  onSelectSubTab,
}: {
  pres: NewsPresentationState;
  onSelectSubTab?: (tab: "live_news" | "catalysts" | "calendar") => void;
}) {
  return <LiveNewsFeedView pres={pres} onSelectSubTab={onSelectSubTab} />;
}

export default LiveNewsTab;
