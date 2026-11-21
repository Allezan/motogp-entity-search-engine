import Link from "next/link";
import { notFound } from "next/navigation";
import SiteHeader from "@/components/SiteHeader";
import {
  serverGetEntityDetail,
  serverGetHealth,
  serverGetIndexStatus,
} from "@/lib/server-api";
import { formatDateId, getCategoryTagStyle } from "@/lib/format";

export const dynamic = "force-dynamic";

type Props = {
  params: { entityId: string };
};

export default async function EntityDetailPage({ params }: Props) {
  const [healthRes, indexRes, entRes] = await Promise.allSettled([
    serverGetHealth(),
    serverGetIndexStatus(),
    serverGetEntityDetail(params.entityId),
  ]);

  const health = healthRes.status === "fulfilled" ? healthRes.value : null;
  const indexStatus = indexRes.status === "fulfilled" ? indexRes.value : null;

  if (entRes.status === "rejected") {
    const msg =
      entRes.reason instanceof Error ? entRes.reason.message : "";
    if (msg.includes("(404)") || msg.toLowerCase().includes("not found")) {
      notFound();
    }
    return (
      <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
        <header className="border-b-2 border-[#E10600] bg-[#0B0B0E]">
          <SiteHeader
            health={health}
            indexStatus={indexStatus}
            activeNav="entities"
          />
        </header>
        <main className="mx-auto w-full max-w-3xl px-4 py-10">
          <div className="rounded-sm border border-red-200 border-l-[3px] border-l-[#E10600] bg-white p-6">
            <p className="font-titillium text-base font-bold text-[#E10600]">
              Gagal memuat profil entitas: {msg || "Backend tidak tersedia."}
            </p>
            <Link
              href="/entities"
              className="mt-4 inline-block font-display text-xs font-bold uppercase tracking-wider text-[#111114] hover:text-[#E10600]"
            >
              ← Kembali ke Kamus Entitas
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const entity = entRes.value;
  const cat = getCategoryTagStyle(entity.category);

  return (
    <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
      <header className="border-b-2 border-[#E10600] bg-[#0B0B0E]">
        <SiteHeader
          health={health}
          indexStatus={indexStatus}
          activeNav="entities"
        />
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-7 sm:px-6">
        <div className="mb-4 flex items-center justify-between">
          <Link
            href="/entities"
            className="font-display text-xs font-bold uppercase tracking-[0.1em] text-zinc-600 transition-colors hover:text-[#E10600]"
          >
            ← Semua Kamus Entitas
          </Link>
          <Link
            href="/"
            className="font-display text-xs font-bold uppercase tracking-[0.1em] text-zinc-500 transition-colors hover:text-[#111114]"
          >
            Pencarian Utama
          </Link>
        </div>

        {/* Entity Profile Sheet */}
        <section
          className={`rounded-sm border border-zinc-200 border-l-4 bg-white p-6 sm:p-8 ${cat.borderLeftClass}`}
        >
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-200 pb-5">
            <div>
              <div className="flex items-center gap-2 font-mono text-[11px]">
                <span className={`font-semibold tracking-wider ${cat.accentClass}`}>
                  {cat.shortLabel}
                </span>
                {entity.verification_status && (
                  <>
                    <span className="text-zinc-300">·</span>
                    <span className="uppercase text-emerald-700">
                      {entity.verification_status}
                    </span>
                  </>
                )}
              </div>
              <h1 className="mt-1 font-titillium text-3xl font-bold text-[#111114]">
                {entity.name}
              </h1>
            </div>

            <Link
              href={`/?q=${encodeURIComponent(entity.name)}`}
              className="rounded-sm bg-[#E10600] px-5 py-2.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-white transition-colors hover:bg-[#BE0500]"
            >
              Cari Berita tentang {entity.name} →
            </Link>
          </div>

          {entity.description && (
            <p className="mt-4 font-sans text-sm leading-relaxed text-zinc-700">
              {entity.description}
            </p>
          )}

          {entity.source_url && (
            <a
              href={entity.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-block font-mono text-xs text-[#E10600] hover:underline"
            >
              Referensi Resmi: {entity.source_url} ↗
            </a>
          )}

          {/* Aliases */}
          <div className="mt-6">
            <h2 className="mb-2.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-500">
              Variasi Nama / Alias & Julukan ({entity.aliases.length})
            </h2>
            <div className="flex flex-wrap gap-1.5">
              {entity.aliases.map((al) => (
                <Link
                  key={al}
                  href={`/?q=${encodeURIComponent(al)}`}
                  title={`Cari berita memakai alias "${al}"`}
                  className="rounded-sm border border-zinc-200 bg-[#FAF9F7] px-2.5 py-1 font-mono text-xs text-zinc-700 transition-colors hover:border-[#E10600] hover:bg-white hover:text-[#E10600]"
                >
                  {al}
                </Link>
              ))}
            </div>
          </div>

          {/* Related Articles */}
          <div className="mt-7">
            <h2 className="mb-3 font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-500">
              Artikel Terkait di Korpus ({entity.documents.length})
            </h2>
            {entity.documents.length > 0 ? (
              <div className="divide-y divide-zinc-200 rounded-sm border border-zinc-200">
                {entity.documents.map((d) => (
                  <div
                    key={d.doc_id}
                    className="flex items-start justify-between gap-4 bg-white p-3.5 transition-colors hover:bg-[#FAF9F7]"
                  >
                    <div className="min-w-0">
                      <Link
                        href={`/articles/${encodeURIComponent(d.doc_id)}?from=${encodeURIComponent(`/entities/${entity.entity_id}`)}`}
                        className="font-titillium text-sm font-bold text-[#111114] hover:text-[#E10600]"
                      >
                        {d.title}
                      </Link>
                      <p className="mt-0.5 text-xs text-zinc-500">
                        <span className="font-display font-bold uppercase tracking-wide text-zinc-600">
                          {d.media}
                        </span>
                        {d.published_at
                          ? ` · ${formatDateId(d.published_at)}`
                          : ""}
                      </p>
                    </div>
                    <span className="shrink-0 font-mono text-[11px] tabular-nums text-zinc-500">
                      {d.mention_count}× disebut
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-sm border border-dashed border-zinc-300 bg-[#FAF9F7] p-4 text-xs text-zinc-500">
                Entitas pengayaan resmi dari grid/kalender motogp.com (belum
                muncul di 60 korpus saat ini, namun siap mengenali kueri
                pengguna).
              </p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

