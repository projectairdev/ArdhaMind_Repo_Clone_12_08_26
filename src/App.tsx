/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { ThemeProvider } from "./frontend/context/ThemeContext";
import { WorkstationStateProvider } from "./frontend/context/WorkstationStateContext";
import { DashboardLayout } from "./frontend/layout/DashboardLayout";

export default function App() {
  return (
    <ThemeProvider>
      <WorkstationStateProvider>
        <DashboardLayout />
      </WorkstationStateProvider>
    </ThemeProvider>
  );
}

