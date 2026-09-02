/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * AIR ArdhaMind Feature Flags & Client Configuration
 */

export const isPreviewEnabled = (): boolean => {
  return (import.meta as any).env?.VITE_ENABLE_PHASE_PREVIEW === "true";
};

export const IS_PHASE_PREVIEW_ENABLED = isPreviewEnabled();
