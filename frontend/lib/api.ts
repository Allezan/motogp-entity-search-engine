import type { SearchResponse } from "./types";
import { dummyResults } from "./dummyData";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_DUMMY = process.env.NEXT_PUBLIC_USE_DUMMY === "true";

export async function searchDocuments(
  query: string,
  topK = 10
): Promise<SearchResponse> {
  if (USE_DUMMY) {
    const q = query.toLowerCase();
    const results = dummyResults
      .filter(
        (d) =>
          d.title.toLowerCase().includes(q) ||
          d.content.toLowerCase().includes(q)
      )
      .slice(0, topK);
    return { query, results };
  }

  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  const res = await fetch(`${API_URL}/search?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Request gagal (${res.status})`);
  }
  return res.json();
}
