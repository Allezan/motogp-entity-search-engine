import { Suspense } from "react";
import Image from "next/image";
import SiteHeader from "@/components/SiteHeader";
import SearchBar, { buildSearchHref } from "@/components/SearchBar";
import ModeSelector from "@/components/ModeSelector";
import SearchResultsSection from "@/components/SearchResultsSection";
import { SearchResultsSkeleton } from "@/components/LoadingSkeletons";
import { serverGetHealth, serverGetIndexStatus } from "@/lib/server-api";
import type { HealthResponse, IndexStatus, ViewMode } from "@/lib/types";

export const dynamic = "force-dynamic";

type RawSearchParams = {
  q?: string | string[];
  mode?: string | string[];
  alpha?: string | string[];
  beta?: string | string[];
  details?: string | string[];
};

function firstParam(val: string | string[] | undefined): string {
  if (Array.isArray(val)) return val[0] ?? "";
  return val ?? "";
}

function parseViewMode(raw: string): ViewMode {
  if (raw === "baseline" || raw === "compare" || raw === "entity") {
    return raw;
  }
  return "entity";
}

function parseWeight(raw: string, fallback: number): number {
  if (!raw) return fallback;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0 || n > 1) return fallback;
  return n;
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: RawSearchParams;
}) {
  const query = firstParam(searchParams.q).trim();
  const mode = parseViewMode(firstParam(searchParams.mode));
  const alpha = parseWeight(firstParam(searchParams.alpha), 0.8);
  const beta = parseWeight(firstParam(searchParams.beta), 0.2);
  const showDetails = firstParam(searchParams.details) === "1";

  const currentSearchHref = buildSearchHref({
    q: query,
    mode,
    alpha,
    beta,
    details: showDetails,
  });

  const [healthRes, indexRes] = await Promise.allSettled([
    serverGetHealth(),
    serverGetIndexStatus(),
  ]);

  const health: HealthResponse | null =
    healthRes.status === "fulfilled" ? healthRes.value : null;
  const indexStatus: IndexStatus | null =
    indexRes.status === "fulfilled" ? indexRes.value : null;

  const started = query.length > 0;
  const suspenseKey = `${query}|${mode}|${alpha}|${beta}|${showDetails}`;

  return (
    <div className="flex min-h-screen flex-col bg-[#F5F5F3]">
      {/* Masthead / Hero */}
      <header
        className={
          started
            ? "relative w-full overflow-hidden border-b-2 border-[#E10600] bg-[#0B0B0E] pb-5"
            : "relative flex min-h-screen w-full flex-col justify-between overflow-hidden bg-[#0B0B0E]"
        }
      >
        {!started && (
          <>
            <Image
              src="/bg-header.jpg"
              alt="Latar belakang lintasan MotoGP"
              fill
              priority
              className="object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-b from-[#0B0B0E]/85 via-[#0B0B0E]/65 to-[#0B0B0E]/90" />
          </>
        )}

        <SiteHeader
          health={health}
          indexStatus={indexStatus}
          activeNav="search"
        />

        {/* Hero / Search Controls */}
        <div
          className={`relative z-10 mx-auto flex w-full max-w-4xl flex-col items-center px-4 sm:px-6 ${
            started ? "mt-5 gap-4" : "my-auto gap-7 py-14"
          }`}
        >
          <div className="flex flex-col items-center text-center">
            <Image
              src="/motogp-logo.png"
              alt="Logo MotoGP"
              className="brightness-0 invert"
              width={started ? 156 : 270}
              height={started ? 64 : 110}
              priority
            />
            {!started && (
              <p className="mt-4 max-w-xl font-sans text-sm leading-relaxed text-zinc-200 sm:text-[15px]">
                Mesin pencari berita MotoGP dengan{" "}
                <strong className="font-semibold text-white">
                  Entity-Aware Search
                </strong>{" "}
                — mengenali nama pembalap, julukan (<em>Pecco</em>,{" "}
                <em>El Diablo</em>, <em>The Doctor</em>), tim, pabrikan, dan
                sirkuit.
              </p>
            )}
          </div>

          <SearchBar
            query={query}
            mode={mode}
            alpha={alpha}
            beta={beta}
            showDetails={showDetails}
            compact={started}
          />

          <ModeSelector
            query={query}
            viewMode={mode}
            alpha={alpha}
            beta={beta}
            showDetails={showDetails}
          />
        </div>

        {!started && (
          <footer className="relative z-10 border-t border-white/10 py-4 text-center font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            Information Retrieval · 100% Server-Side Rendered · Baseline TF-IDF
            (From-Scratch) vs Entity-Aware Search
          </footer>
        )}
      </header>

      {/* Streaming SSR Results with Motorsport Telemetry Skeleton */}
      {started && (
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
          <Suspense
            key={suspenseKey}
            fallback={<SearchResultsSkeleton isCompare={mode === "compare"} />}
          >
            <SearchResultsSection
              query={query}
              mode={mode}
              alpha={alpha}
              beta={beta}
              showDetails={showDetails}
              currentSearchHref={currentSearchHref}
            />
          </Suspense>
        </main>
      )}
    </div>
  );
}
