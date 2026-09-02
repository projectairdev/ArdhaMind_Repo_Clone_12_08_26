/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * CalendarTab.tsx
 * Canonical wrapper for EconomicCalendarView.
 */

import React from "react";
import { NewsPresentationState } from "../../utils/canonicalNewsAdapter";
import { EconomicCalendarView } from "./EconomicCalendarView";

export function CalendarTab({ pres }: { pres: NewsPresentationState }) {
  return <EconomicCalendarView pres={pres} />;
}

export default CalendarTab;
