export type SearchMode = "entity" | "baseline";
export type ViewMode = "entity" | "baseline" | "compare";

export type RecognizedEntity = {
  entity_id: string;
  name: string;
  category: string;
  matched_text: string;
  ambiguous: boolean;
};

export type SearchResult = {
  rank: number;
  doc_id: string;
  title: string;
  media: string | null;
  published_at: string | null;
  topic: string | null;
  url: string | null;
  author: string | null;
  snippet: string;
  score: number;
  text_score: number;
  entity_score: number;
  matched_entities: string[];
};

export type SearchResponse = {
  query: string;
  preprocessed_query: string;
  mode: SearchMode;
  alpha: number | null;
  beta: number | null;
  recognized_entities: RecognizedEntity[];
  entity_fallback: boolean;
  total: number;
  results: SearchResult[];
};

export type CompareResponse = {
  baseline: SearchResponse;
  entity: SearchResponse;
};

export type DocumentEntity = {
  entity_id: string;
  name: string;
  category: string | null;
  mention_count: number;
};

export type DocumentDetail = {
  doc_id: string;
  title: string;
  published_at: string | null;
  media: string | null;
  topic: string | null;
  url: string | null;
  author: string | null;
  content: string;
  entities: DocumentEntity[];
};

export type EntityItem = {
  entity_id: string;
  name: string;
  category: string | null;
  description: string | null;
  source_url: string | null;
  verification_status: string | null;
  aliases: string[];
  document_count: number;
};

export type EntityDocumentRef = {
  doc_id: string;
  title: string;
  media: string | null;
  published_at: string | null;
  url: string | null;
  mention_count: number;
};

export type EntityDetail = EntityItem & {
  documents: EntityDocumentRef[];
};

export type HealthResponse = {
  status: string;
  database: string;
  index_ready: boolean;
  engine?: string;
};

export type IndexStatus = {
  ready: boolean;
  engine: string | null;
  built_at: string | null;
  num_documents: number | null;
  num_terms: number | null;
  num_entities: number | null;
};
