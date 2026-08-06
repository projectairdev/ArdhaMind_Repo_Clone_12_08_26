import { AnalyticsReport } from "../types";

export async function getAnalyticsReport(): Promise<AnalyticsReport> {
  const resp = await fetch("/api/analytics");
  if (!resp.ok) {
    throw new Error(`Failed to fetch analytics report: ${resp.statusText}`);
  }
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}
