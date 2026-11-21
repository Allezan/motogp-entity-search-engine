import Link from "next/link";
import { notFound } from "next/navigation";
import SiteHeader from "@/components/SiteHeader";
import {
  serverGetDocumentDetail,
  serverGetHealth,
  serverGetIndexStatus,
} from "@/lib/server-api";
import { formatDateId, getCategoryTagStyle } from "@/lib/format";

export const dynamic = "force-dynamic";

type Props = {
  params: { docId: string };
  searchParams: { from?: string | string[] };
};

export default async function ArticleDetailPage({
  params,
  searchParams,
}: Props) {
  const fromRaw = Array.isArray(searchParams.from)
    ? searchParams.from[0]
    : searchParams.from;
  const backHref =
    fromRaw && fromRaw.startsWith("/") ? fromRaw : "/";

  const [healthRes, indexRes, docRes] = await Promise.allSettled([
    serverGetHealth(),
    serverGetIndexStatus(),
    serverGetDocumentDetail(params.docId),
  ]);

  const health = healthRes.status === "fulfilled" ? healthRes.value : null;
  const indexStatus = indexRes.status === "fulfilled" ? indexRes.value : null;

  if (docRes.status === "rejected") {
    const msg =
      docRes.reason instanceof Error ? docRes.reason.message : "";
    if (msg.includes("(404)") || msg.toLowerCase().includes("not found")) {
      notFound();
    }
    return (
      <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
        <header className="border-b-2 border-[#E10600] bg-[#0B0B0E]">
          <SiteHeader health={health} indexStatus={indexStatus} />
        </header>
        <main className="mx-auto w-full max-w-3xl px-4 py-10">
          <div className="rounded-sm border border-red-200 border-l-[3px] border-l-[#E10600] bg-white p-6">
            <p className="font-titillium text-base font-bold text-[#E10600]">
              Gagal memuat artikel: {msg || "Backend tidak dapat dihubungi."}
            </p>
            <Link
              href={backHref}
              className="mt-4 inline-block font-display text-xs font-bold uppercase tracking-wider text-[#111114] hover:text-[#E10600]"
            >
              ← Kembali ke Pencarian
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const article = docRes.value;

  return (
    <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
      <header className="border-b-2 border-[#E10600] bg-[#0B0B0E]">
        <SiteHeader health={health} indexStatus={indexStatus} />
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-7 sm:px-6">
        <div className="mb-4 flex items-center justify-between">
          <Link
            href={backHref}
            className="font-display text-xs font-bold uppercase tracking-[0.1em] text-zinc-600 transition-colors hover:text-[#E10600]"
          >
            ← Kembali ke Hasil Pencarian
          </Link>
          {article.url && (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-display text-xs font-bold uppercase tracking-[0.1em] text-[#E10600] hover:text-[#BE0500]"
            >
              Buka di {article.media || "Sumber Asli"} ↗
            </a>
          )}
        </div>

        <article className="rounded-sm border border-zinc-200 border-t-2 border-t-[#111114] bg-white px-6 py-7 sm:px-9 sm:py-9">
          {/* Editorial Kicker */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {article.media && (
              <span className="font-display text-xs font-bold uppercase tracking-[0.1em] text-[#E10600]">
                {article.media}
              </span>
            )}
            {article.published_at && (
              <>
                <span className="text-zinc-300">·</span>
                <span className="font-mono text-[11px] text-zinc-500">
                  {formatDateId(article.published_at)}
                </span>
              </>
            )}
            {article.topic && (
              <>
                <span className="text-zinc-300">·</span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
                  {article.topic}
                </span>
              </>
            )}
          </div>

          {/* Headline */}
          <h1 className="mt-2.5 font-titillium text-2xl font-bold leading-tight text-[#111114] sm:text-3xl">
            {article.title}
          </h1>

          {article.author && (
            <p className="mt-2.5 border-b border-zinc-200 pb-4 font-sans text-xs text-zinc-500">
              Penulis: <span className="font-medium text-zinc-700">{article.author}</span>
            </p>
          )}

          {/* Entities Referenced in Article */}
          <section className="mt-5 rounded-sm border border-zinc-200 bg-[#FAF9F7] p-4">
            <h2 className="mb-2.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-500">
              Entitas MotoGP Terindeks dalam Artikel ({article.entities.length})
            </h2>
            {article.entities.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {article.entities.map((ent) => {
                  const cat = getCategoryTagStyle(ent.category);
                  return (
                    <Link
                      key={ent.entity_id}
                      href={`/entities/${encodeURIComponent(ent.entity_id)}`}
                      className={`group inline-flex items-center gap-1.5 rounded-sm border border-zinc-200 border-l-2 bg-white px-2.5 py-1 text-xs transition-colors hover:border-zinc-400 ${cat.borderLeftClass}`}
                    >
                      <span
                        className={`font-mono text-[10px] font-semibold tracking-wider ${cat.accentClass}`}
                      >
                        {cat.shortLabel}
                      </span>
                      <span className="font-titillium font-bold text-[#111114] group-hover:text-[#E10600]">
                        {ent.name}
                      </span>
                      <span className="font-mono text-[10px] tabular-nums text-zinc-400">
                        {ent.mention_count}×
                      </span>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-zinc-500">
                Artikel teknis/umum — tidak memuat entitas spesifik dari kamus
                MotoGP.
              </p>
            )}
          </section>

          {/* Original Full Article Text */}
          <div className="mt-6 space-y-4 font-sans text-[15px] leading-7 text-zinc-800">
            {article.content
              .split(/\n+/)
              .map((p) => p.trim())
              .filter(Boolean)
              .map((para, idx) => (
                <p key={idx}>{para}</p>
              ))}
          </div>
        </article>
      </main>
    </div>
  );
}

