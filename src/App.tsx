/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { ThemeProvider } from "./frontend/context/ThemeContext";
import { WorkstationStateProvider } from "./frontend/context/WorkstationStateContext";
import { NavigationProvider } from "./frontend/context/NavigationContext";
import { DashboardLayout } from "./frontend/layout/DashboardLayout";

export default function App() {
  return (
    <ThemeProvider>
      <WorkstationStateProvider>
        <NavigationProvider>
          <DashboardLayout />
        </NavigationProvider>
      </WorkstationStateProvider>
    </ThemeProvider>
  );
}

