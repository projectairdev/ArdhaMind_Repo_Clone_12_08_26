import { NewsSentimentContext } from "../types";

export async function getNewsSentiment(): Promise<NewsSentimentContext> {
  const resp = await fetch("/api/news");
  if (!resp.ok) {
    throw new Error(`Failed to fetch news sentiment: ${resp.statusText}`);
  }
  const data = await resp.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}
