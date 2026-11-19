"use client";

import { useState } from "react";
import Image from "next/image";
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

   // true setelah user mulai mencari
  const started = searched || loading;

  return (
    <>
      {/* Header */}
      <header
        className={
          started
            ? "relative w-full overflow-hidden bg-black py-10"
            : "relative flex min-h-screen w-full items-center justify-center overflow-hidden"
        }
      >
        {/* Background gambar + overlay: hanya di landing page */}
        {!started && (
          <>
            <Image
              src="/bg-header.jpg"
              alt="header background"
              fill
              priority
              className="object-cover"
            />
            <div className="absolute inset-0 bg-black/50" />
          </>
        )}

        {/* Logo + search bar */}
        <div className="relative z-10 mx-auto flex w-full max-w-2xl flex-col items-center gap-6 px-4">
          <Image
            src="/motogp-logo.png"
            alt="Logo MotoGP"
            className="brightness-0 invert"
            width={started ? 250 : 320}
            height={started ? 250 : 320}
            priority
          />

          <SearchBar
            value={query}
            loading={loading}
            onChange={setQuery}
            onSubmit={handleSearch}
          />
        </div>
      </header>

      {/* Hasil pencarian: hanya setelah mencari */}
      {started && (
        <main className="mx-auto max-w-2xl px-4 py-8">
          <section className="flex flex-col gap-3">
            {loading && <p className="text-center text-gray-500">Mencari...</p>}
            {error && <p className="text-center text-red-600">{error}</p>}
            {!loading && !error && searched && results.length === 0 && (
              <p className="text-center text-gray-500">No results found.</p>
            )}
            {!loading &&
              results.map((r) => <ResultItem key={r.doc_id} result={r} />)}
          </section>
        </main>
      )}
    </>
  );
}