export type SearchResult = {
  doc_id: string;
  title: string;
  content: string;
  url: string;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
};
