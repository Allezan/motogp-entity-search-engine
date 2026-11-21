import EntityBanner from "@/components/EntityBanner";
import ResultItem from "@/components/ResultItem";
import { serverCompareSearch, serverSearchDocuments } from "@/lib/server-api";
import type { CompareResponse, SearchResponse, ViewMode } from "@/lib/types";

type Props = {
  query: string;
  mode: ViewMode;
  alpha: number;
  beta: number;
  showDetails: boolean;
  currentSearchHref: string;
};

export default async function SearchResultsSection({
  query,
  mode,
  alpha,
  beta,
  showDetails,
  currentSearchHref,
}: Props) {
  let singleData: SearchResponse | null = null;
  let compareData: CompareResponse | null = null;
  let errorMessage = "";

  try {
    if (mode === "compare") {
      compareData = await serverCompareSearch(query, {
        topK: 10,
        alpha,
        beta,
      });
    } else {
      singleData = await serverSearchDocuments(query, {
        mode,
        topK: 10,
        alpha,
        beta,
      });
    }
  } catch (err) {
    errorMessage =
      err instanceof Error
        ? `Gagal menghubungi server backend: ${err.message}`
        : "Gagal menghubungi server backend.";
  }

  if (errorMessage) {
    return (
      <div className="mx-auto max-w-4xl rounded-sm border border-red-200 border-l-[3px] border-l-[#E10600] bg-white p-5">
        <p className="font-titillium text-sm font-bold text-[#E10600]">
          {errorMessage}
        </p>
        <p className="mt-1 font-mono text-xs text-zinc-500">
          Pastikan server FastAPI aktif dan environment variable{" "}
          <code>BACKEND_API_URL</code> sudah benar.
        </p>
      </div>
    );
  }

  if (singleData) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <EntityBanner
          recognizedEntities={singleData.recognized_entities}
          entityFallback={singleData.entity_fallback}
          preprocessedQuery={singleData.preprocessed_query}
          showIrDetails={showDetails}
          isBaselineOnly={singleData.mode === "baseline"}
          alpha={singleData.alpha}
          beta={singleData.beta}
        />

        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-200 pb-2.5 text-xs text-zinc-500">
          <p>
            Menampilkan{" "}
            <strong className="font-mono text-[#111114] tabular-nums">
              {singleData.results.length}
            </strong>{" "}
            dari{" "}
            <strong className="font-mono text-[#111114] tabular-nums">
              {singleData.total}
            </strong>{" "}
            artikel untuk{" "}
            <span className="font-semibold text-[#111114]">
              &ldquo;{singleData.query}&rdquo;
            </span>
          </p>
          <span className="font-display text-xs font-bold uppercase tracking-[0.1em] text-zinc-600">
            {singleData.mode === "entity"
              ? "Mode · Entity-Aware"
              : "Mode · Baseline TF-IDF"}
          </span>
        </div>

        {singleData.results.length === 0 ? (
          <div className="rounded-sm border border-zinc-200 bg-white p-10 text-center">
            <p className="font-titillium text-sm font-bold text-[#111114]">
              Tidak ada artikel yang cocok ditemukan.
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Coba kata kunci lain seperti nama pembalap, julukan, tim, atau
              sirkuit MotoGP.
            </p>
          </div>
        ) : (
          <section className="flex flex-col gap-3">
            {singleData.results.map((r) => (
              <ResultItem
                key={r.doc_id}
                result={r}
                showEntityScore={singleData.mode === "entity"}
                backHref={currentSearchHref}
              />
            ))}
          </section>
        )}
      </div>
    );
  }

  if (compareData) {
    const baselineRankMap = new Map<string, number>();
    compareData.baseline.results.forEach((r) =>
      baselineRankMap.set(r.doc_id, r.rank)
    );

    return (
      <div className="space-y-5">
        <EntityBanner
          recognizedEntities={compareData.entity.recognized_entities}
          entityFallback={compareData.entity.entity_fallback}
          preprocessedQuery={compareData.entity.preprocessed_query}
          showIrDetails={showDetails}
          alpha={compareData.entity.alpha}
          beta={compareData.entity.beta}
        />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Left Column: Baseline */}
          <section className="space-y-3">
            <div className="flex items-center justify-between rounded-sm border border-zinc-300 border-t-2 border-t-zinc-700 bg-white px-4 py-3">
              <div>
                <h2 className="font-display text-base font-bold uppercase tracking-[0.08em] text-[#111114]">
                  Baseline · TF-IDF + Cosine
                </h2>
                <p className="text-xs text-zinc-500">
                  Pencocokan teks murni tanpa kamus entitas
                </p>
              </div>
              <span className="font-mono text-xs font-semibold tabular-nums text-zinc-600">
                {compareData.baseline.total} hasil
              </span>
            </div>

            {compareData.baseline.results.length === 0 ? (
              <div className="rounded-sm border border-zinc-200 bg-white p-8 text-center text-xs text-zinc-500">
                Tidak ada hasil pada Baseline TF-IDF.
              </div>
            ) : (
              compareData.baseline.results.map((r) => (
                <ResultItem
                  key={`base-${r.doc_id}`}
                  result={r}
                  showEntityScore={false}
                  backHref={currentSearchHref}
                />
              ))
            )}
          </section>

          {/* Right Column: Proposed Entity-Aware */}
          <section className="space-y-3">
            <div className="flex items-center justify-between rounded-sm border border-zinc-800 border-t-2 border-t-[#E10600] bg-[#0B0B0E] px-4 py-3 text-white">
              <div>
                <h2 className="font-display text-base font-bold uppercase tracking-[0.08em]">
                  Proposed · Entity-Aware Search
                </h2>
                <p className="font-mono text-[11px] text-zinc-400">
                  α={compareData.entity.alpha}·S_text + β=
                  {compareData.entity.beta}·S_entity
                </p>
              </div>
              <span className="font-mono text-xs font-semibold tabular-nums text-zinc-300">
                {compareData.entity.total} hasil
              </span>
            </div>

            {compareData.entity.results.length === 0 ? (
              <div className="rounded-sm border border-zinc-200 bg-white p-8 text-center text-xs text-zinc-500">
                Tidak ada hasil pada Entity-Aware Search.
              </div>
            ) : (
              compareData.entity.results.map((r) => {
                const prevRank = baselineRankMap.get(r.doc_id);
                const delta: number | "NEW" | null =
                  prevRank === undefined
                    ? "NEW"
                    : prevRank - r.rank !== 0
                      ? prevRank - r.rank
                      : null;
                return (
                  <ResultItem
                    key={`ent-${r.doc_id}`}
                    result={r}
                    showEntityScore
                    rankDelta={delta}
                    backHref={currentSearchHref}
                  />
                );
              })
            )}
          </section>
        </div>
      </div>
    );
  }

  return null;
}

