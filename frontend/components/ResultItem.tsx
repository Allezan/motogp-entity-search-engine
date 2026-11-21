import Link from "next/link";
import type { SearchResult } from "@/lib/types";
import { formatDateId, formatRank } from "@/lib/format";

type Props = {
  result: SearchResult;
  showEntityScore?: boolean;
  rankDelta?: number | "NEW" | null;
  backHref?: string;
};

export default function ResultItem({
  result,
  showEntityScore = true,
  rankDelta = null,
  backHref,
}: Props) {
  const formattedDate = formatDateId(result.published_at);
  const articleHref = backHref
    ? `/articles/${encodeURIComponent(result.doc_id)}?from=${encodeURIComponent(backHref)}`
    : `/articles/${encodeURIComponent(result.doc_id)}`;

  return (
    <article className="group rounded-sm border border-zinc-200 bg-white transition-colors hover:border-zinc-400">
      {/* Top Editorial & Telemetry Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-100 px-4 py-2.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <span
            className={`font-display text-xl font-extrabold leading-none tabular-nums ${
              result.rank === 1 ? "text-[#E10600]" : "text-[#111114]"
            }`}
          >
            {formatRank(result.rank)}
          </span>

          {rankDelta === "NEW" && (
            <span className="rounded-sm bg-emerald-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-emerald-700 ring-1 ring-emerald-200">
              NEW
            </span>
          )}
          {typeof rankDelta === "number" && rankDelta > 0 && (
            <span className="rounded-sm bg-emerald-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold tabular-nums text-emerald-700 ring-1 ring-emerald-200">
              ▲ +{rankDelta}
            </span>
          )}
          {typeof rankDelta === "number" && rankDelta < 0 && (
            <span className="rounded-sm bg-zinc-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold tabular-nums text-zinc-600 ring-1 ring-zinc-200">
              ▼ {rankDelta}
            </span>
          )}

          <span className="h-3.5 w-px bg-zinc-200" aria-hidden="true" />

          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {result.media && (
              <span className="font-display text-xs font-bold uppercase tracking-[0.08em] text-[#111114]">
                {result.media}
              </span>
            )}
            {formattedDate && (
              <>
                <span className="text-zinc-300">·</span>
                <span className="font-sans text-zinc-500">{formattedDate}</span>
              </>
            )}
            {result.topic && (
              <>
                <span className="text-zinc-300">·</span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
                  {result.topic}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Live-Timing Telemetry Readout */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] tabular-nums">
          <span
            className="border-l-2 border-[#E10600] pl-2 font-semibold text-[#111114]"
            title="Skor Akhir (S_final)"
          >
            <span className="mr-1 text-[10px] font-normal uppercase text-zinc-400">
              Skor
            </span>
            {result.score.toFixed(4)}
          </span>
          <span className="text-zinc-200">|</span>
          <span
            className="text-zinc-500"
            title="Skor Kemiripan Teks TF-IDF + Cosine (S_text)"
          >
            <span className="mr-1 text-[10px] uppercase text-zinc-400">
              Teks
            </span>
            {result.text_score.toFixed(4)}
          </span>
          {showEntityScore && (
            <>
              <span className="text-zinc-200">|</span>
              <span
                className={
                  result.entity_score > 0
                    ? "font-semibold text-emerald-700"
                    : "text-zinc-400"
                }
                title="Skor Cakupan Entitas Query (S_entity = |E_Q ∩ E_D| / |E_Q|)"
              >
                <span className="mr-1 text-[10px] font-normal uppercase text-zinc-400">
                  Entitas
                </span>
                {result.entity_score.toFixed(4)}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main Headline & Snippet */}
      <div className="px-4 py-3.5">
        <h2 className="font-titillium text-[17px] font-bold leading-snug text-[#111114]">
          <Link
            href={articleHref}
            prefetch={false}
            className="transition-colors hover:text-[#E10600]"
          >
            {result.title}
          </Link>
        </h2>

        <p className="mt-1.5 line-clamp-2 font-sans text-sm leading-relaxed text-zinc-600">
          {result.snippet}
        </p>
      </div>

      {/* Bottom Action & Matched Entity Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-zinc-100 bg-[#FAF9F7] px-4 py-2">
        <div className="flex flex-wrap items-center gap-1.5">
          {result.matched_entities.length > 0 && (
            <>
              <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
                Cocok:
              </span>
              {result.matched_entities.map((name) => (
                <span
                  key={name}
                  className="rounded-sm border border-zinc-200 bg-white px-2 py-0.5 font-sans text-[11px] font-medium text-zinc-700"
                >
                  {name}
                </span>
              ))}
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <Link
            href={articleHref}
            prefetch={false}
            className="font-display text-xs font-bold uppercase tracking-[0.08em] text-[#E10600] transition-colors hover:text-[#BE0500]"
          >
            Baca Artikel →
          </Link>
          {result.url && (
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-sans text-xs font-medium text-zinc-500 transition-colors hover:text-[#111114]"
            >
              Sumber Asli ↗
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
