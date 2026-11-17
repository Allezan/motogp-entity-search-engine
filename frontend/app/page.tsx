"use client";

import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ResultItem from "@/components/ResultItem";
import { searchDocuments } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  async function handleSearch() {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const data = await searchDocuments(q);
      setResults(data.results);
    } catch {
      setResults([]);
      setError("Gagal menghubungi server. Coba lagi.");
    } finally {
      setSearched(true);
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="mb-6 text-center text-3xl font-bold">MotoGP News Search</h1>
      <SearchBar
        value={query}
        loading={loading}
        onChange={setQuery}
        onSubmit={handleSearch}
      />

      <section className="mt-8 flex flex-col gap-3">
        {loading && <p className="text-center text-gray-500">Mencari...</p>}
        {error && <p className="text-center text-red-600">{error}</p>}
        {!loading && !error && searched && results.length === 0 && (
          <p className="text-center text-gray-500">Tidak ada hasil.</p>
        )}
        {!loading &&
          results.map((r) => <ResultItem key={r.doc_id} result={r} />)}
      </section>
    </main>
  );
}
