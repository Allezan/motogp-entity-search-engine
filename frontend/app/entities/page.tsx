import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import {
  serverGetEntities,
  serverGetHealth,
  serverGetIndexStatus,
} from "@/lib/server-api";
import { getCategoryTagStyle } from "@/lib/format";

export const dynamic = "force-dynamic";

const CATEGORIES = ["All", "Rider", "Team", "Manufacturer", "Circuit"];

type Props = {
  searchParams: {
    category?: string | string[];
    q?: string | string[];
  };
};

function first(val: string | string[] | undefined): string {
  if (Array.isArray(val)) return val[0] ?? "";
  return val ?? "";
}

export default async function EntitiesPage({ searchParams }: Props) {
  const categoryRaw = first(searchParams.category) || "All";
  const category = CATEGORIES.includes(categoryRaw) ? categoryRaw : "All";
  const filterQ = first(searchParams.q).trim();

  const [healthRes, indexRes, entsRes] = await Promise.allSettled([
    serverGetHealth(),
    serverGetIndexStatus(),
    serverGetEntities(category === "All" ? undefined : category),
  ]);

  const health = healthRes.status === "fulfilled" ? healthRes.value : null;
  const indexStatus = indexRes.status === "fulfilled" ? indexRes.value : null;
  const allEntities = entsRes.status === "fulfilled" ? entsRes.value : [];
  const loadError =
    entsRes.status === "rejected"
      ? entsRes.reason instanceof Error
        ? entsRes.reason.message
        : "Gagal memuat kamus entitas."
      : "";

  const qLower = filterQ.toLowerCase();
  const filtered = qLower
    ? allEntities.filter(
        (e) =>
          e.name.toLowerCase().includes(qLower) ||
          e.aliases.some((a) => a.toLowerCase().includes(qLower))
      )
    : allEntities;

  return (
    <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
      <header className="border-b-2 border-[#E10600] bg-[#0B0B0E]">
        <SiteHeader
          health={health}
          indexStatus={indexStatus}
          activeNav="entities"
        />

        <div className="mx-auto w-full max-w-6xl px-4 py-7 sm:px-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-widest text-[#E10600]">
                Entity Dictionary · 3-Source Verified
              </p>
              <h1 className="mt-1 font-display text-3xl font-extrabold uppercase tracking-[0.06em] text-white">
                Kamus Entitas MotoGP
              </h1>
              <p className="mt-1 max-w-2xl font-sans text-sm text-zinc-400">
                Daftar resmi pembalap, tim, pabrikan, dan sirkuit beserta
                variasi julukan, kode nomor balap, dan indeks artikel terkait.
              </p>
            </div>

            <Link
              href="/"
              prefetch={false}
              className="font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-300 transition-colors hover:text-white"
            >
              ← Kembali ke Pencarian
            </Link>
          </div>

          {/* Server-Side Filter Form & Category Tabs */}
          <div className="mt-6 flex flex-wrap items-end justify-between gap-4 border-b border-white/15 pb-0">
            <div className="flex flex-wrap items-center gap-5">
              {CATEGORIES.map((cat) => {
                const active = category === cat;
                const params = new URLSearchParams();
                if (cat !== "All") params.set("category", cat);
                if (filterQ) params.set("q", filterQ);
                const href = params.toString()
                  ? `/entities?${params.toString()}`
                  : "/entities";
                return (
                  <Link
                    key={cat}
                    prefetch={false}
                    href={href}
                    className={`relative pb-2.5 pt-1 font-display text-sm font-bold uppercase tracking-[0.1em] transition-colors ${
                      active
                        ? "text-white"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    {cat}
                    {active && (
                      <span className="absolute inset-x-0 -bottom-px h-[2px] bg-[#E10600]" />
                    )}
                  </Link>
                );
              })}
            </div>

            <form
              method="GET"
              action="/entities"
              className="mb-2 flex w-full max-w-sm items-stretch overflow-hidden rounded-sm border border-white/20 bg-white focus-within:border-[#E10600]"
            >
              {category !== "All" && (
                <input type="hidden" name="category" value={category} />
              )}
              <input
                key={filterQ}
                type="search"
                name="q"
                defaultValue={filterQ}
                placeholder="Filter nama / alias (Pecco, MM93, VR46)..."
                className="flex-1 bg-transparent px-3 py-1.5 font-sans text-xs text-[#111114] placeholder:text-zinc-400 outline-none"
              />
              <button
                type="submit"
                className="bg-[#E10600] px-4 font-display text-xs font-bold uppercase tracking-wider text-white hover:bg-[#BE0500]"
              >
                Filter
              </button>
            </form>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        {loadError && (
          <div className="rounded-sm border border-red-200 border-l-[3px] border-l-[#E10600] bg-white p-5 text-sm text-[#E10600]">
            {loadError}
          </div>
        )}

        {!loadError && (
          <>
            <div className="mb-4 flex items-center justify-between text-xs text-zinc-500">
              <p>
                Menampilkan{" "}
                <strong className="font-mono text-[#111114] tabular-nums">
                  {filtered.length}
                </strong>{" "}
                entitas
                {category !== "All" ? ` kategori ${category}` : ""}
                {filterQ ? ` untuk filter "${filterQ}"` : ""}
              </p>
              {filterQ && (
                <Link
                  prefetch={false}
                  href={
                    category !== "All"
                      ? `/entities?category=${encodeURIComponent(category)}`
                      : "/entities"
                  }
                  className="font-mono text-xs text-[#E10600] hover:underline"
                >
                  Reset filter ✕
                </Link>
              )}
            </div>

            {filtered.length === 0 ? (
              <div className="rounded-sm border border-zinc-200 bg-white p-10 text-center text-sm text-zinc-500">
                Tidak ada entitas yang cocok dengan filter tersebut.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((ent) => {
                  const cat = getCategoryTagStyle(ent.category);
                  return (
                    <Link
                      key={ent.entity_id}
                      prefetch={false}
                      href={`/entities/${encodeURIComponent(ent.entity_id)}`}
                      className={`group flex flex-col justify-between rounded-sm border border-zinc-200 border-l-[3px] bg-white p-4 transition-colors hover:border-zinc-400 ${cat.borderLeftClass}`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={`font-mono text-[10px] font-semibold tracking-wider ${cat.accentClass}`}
                          >
                            {cat.shortLabel}
                          </span>
                          <span className="font-mono text-[11px] tabular-nums text-zinc-400">
                            {ent.document_count} artikel
                          </span>
                        </div>
                        <h2 className="mt-1 font-titillium text-base font-bold text-[#111114] group-hover:text-[#E10600]">
                          {ent.name}
                        </h2>
                        {ent.description && (
                          <p className="mt-1 line-clamp-2 font-sans text-xs leading-relaxed text-zinc-500">
                            {ent.description}
                          </p>
                        )}
                      </div>

                      <div className="mt-3 border-t border-zinc-100 pt-2 font-mono text-[11px] text-zinc-400">
                        <span className="line-clamp-1">
                          {ent.aliases.slice(0, 4).join(" · ")}
                          {ent.aliases.length > 4
                            ? ` +${ent.aliases.length - 4}`
                            : ""}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

