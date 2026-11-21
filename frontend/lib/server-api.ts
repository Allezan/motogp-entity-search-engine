import type {
  CompareResponse,
  DocumentDetail,
  EntityDetail,
  EntityItem,
  HealthResponse,
  IndexStatus,
  SearchMode,
  SearchResponse,
} from "./types";

function getBackendBaseUrl(): string {
  const raw =
    process.env.BACKEND_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  return `${raw.replace(/\/+$/, "")}/api/v1`;
}

async function serverFetchJson<T>(path: string): Promise<T> {
  const url = `${getBackendBaseUrl()}${path}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    let detail = `Backend request gagal (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore non-json error body
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export type ServerSearchOptions = {
  mode?: SearchMode;
  topK?: number;
  alpha?: number;
  beta?: number;
};

export async function serverSearchDocuments(
  query: string,
  options: ServerSearchOptions = {}
): Promise<SearchResponse> {
  const { mode = "entity", topK = 10, alpha, beta } = options;
  const params = new URLSearchParams({
    q: query,
    mode,
    top_k: String(topK),
  });
  if (alpha !== undefined) params.set("alpha", String(alpha));
  if (beta !== undefined) params.set("beta", String(beta));
  return serverFetchJson<SearchResponse>(`/search?${params.toString()}`);
}

export async function serverCompareSearch(
  query: string,
  options: Omit<ServerSearchOptions, "mode"> = {}
): Promise<CompareResponse> {
  const { topK = 10, alpha, beta } = options;
  const params = new URLSearchParams({
    q: query,
    top_k: String(topK),
  });
  if (alpha !== undefined) params.set("alpha", String(alpha));
  if (beta !== undefined) params.set("beta", String(beta));
  return serverFetchJson<CompareResponse>(
    `/search/compare?${params.toString()}`
  );
}

export async function serverGetDocumentDetail(
  docId: string
): Promise<DocumentDetail> {
  return serverFetchJson<DocumentDetail>(
    `/documents/${encodeURIComponent(docId)}`
  );
}

export async function serverGetEntities(
  category?: string
): Promise<EntityItem[]> {
  const params = new URLSearchParams();
  if (category && category !== "All") {
    params.set("category", category);
  }
  const qs = params.toString();
  return serverFetchJson<EntityItem[]>(`/entities${qs ? `?${qs}` : ""}`);
}

export async function serverGetEntityDetail(
  entityId: string
): Promise<EntityDetail> {
  return serverFetchJson<EntityDetail>(
    `/entities/${encodeURIComponent(entityId)}`
  );
}

export async function serverGetHealth(): Promise<HealthResponse> {
  return serverFetchJson<HealthResponse>("/health");
}

export async function serverGetIndexStatus(): Promise<IndexStatus> {
  return serverFetchJson<IndexStatus>("/index/status");
}

