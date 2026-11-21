export function RacingProgressBar() {
  return (
    <div
      role="status"
      aria-label="Memuat data"
      className="relative h-[2px] w-full overflow-hidden bg-zinc-200"
    >
      <div className="animate-racing-sweep h-full w-1/3 bg-[#E10600]" />
    </div>
  );
}

function ResultCardSkeleton() {
  return (
    <div className="rounded-sm border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-2.5">
        <div className="flex items-center gap-2.5">
          <div className="h-5 w-6 animate-pulse rounded-sm bg-zinc-200" />
          <div className="h-3.5 w-px bg-zinc-200" />
          <div className="h-3 w-36 animate-pulse rounded-sm bg-zinc-200" />
        </div>
        <div className="h-3 w-44 animate-pulse rounded-sm bg-zinc-100" />
      </div>
      <div className="space-y-2.5 px-4 py-4">
        <div className="h-4 w-4/5 animate-pulse rounded-sm bg-zinc-200" />
        <div className="h-3 w-full animate-pulse rounded-sm bg-zinc-100" />
        <div className="h-3 w-2/3 animate-pulse rounded-sm bg-zinc-100" />
      </div>
      <div className="flex items-center justify-between border-t border-zinc-100 bg-[#FAF9F7] px-4 py-2">
        <div className="h-4 w-32 animate-pulse rounded-sm bg-zinc-200/70" />
        <div className="h-3 w-24 animate-pulse rounded-sm bg-zinc-200/70" />
      </div>
    </div>
  );
}

export function SearchResultsSkeleton({
  isCompare = false,
}: {
  isCompare?: boolean;
}) {
  return (
    <div className={isCompare ? "space-y-5" : "mx-auto max-w-4xl space-y-4"}>
      <div className="overflow-hidden rounded-sm border border-zinc-200 border-l-[3px] border-l-[#E10600] bg-white">
        <RacingProgressBar />
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-400">
              Memproses Kueri &amp; Skor IR
            </span>
            <div className="h-5 w-28 animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-5 w-24 animate-pulse rounded-sm bg-zinc-100" />
          </div>
          <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
            TF-IDF · Entity Index
          </span>
        </div>
      </div>

      {isCompare ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {[0, 1].map((col) => (
            <div key={col} className="space-y-3">
              <div className="h-14 animate-pulse rounded-sm border border-zinc-200 bg-white" />
              <ResultCardSkeleton />
              <ResultCardSkeleton />
              <ResultCardSkeleton />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <ResultCardSkeleton />
          <ResultCardSkeleton />
          <ResultCardSkeleton />
          <ResultCardSkeleton />
        </div>
      )}
    </div>
  );
}

export function ArticleDetailSkeleton() {
  return (
    <div className="min-h-screen bg-[#F5F5F3]">
      <div className="h-14 w-full bg-[#0B0B0E]" />
      <RacingProgressBar />
      <main className="mx-auto max-w-4xl px-4 py-7 sm:px-6">
        <div className="mb-4 h-4 w-44 animate-pulse rounded-sm bg-zinc-200" />
        <div className="space-y-4 rounded-sm border border-zinc-200 border-t-2 border-t-[#111114] bg-white p-8">
          <div className="h-3 w-40 animate-pulse rounded-sm bg-zinc-200" />
          <div className="h-7 w-11/12 animate-pulse rounded-sm bg-zinc-200" />
          <div className="h-7 w-2/3 animate-pulse rounded-sm bg-zinc-200" />
          <div className="h-20 animate-pulse rounded-sm border border-zinc-100 bg-[#FAF9F7]" />
          <div className="space-y-2.5 pt-2">
            <div className="h-3.5 w-full animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-3.5 w-full animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-3.5 w-5/6 animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-3.5 w-full animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-3.5 w-4/5 animate-pulse rounded-sm bg-zinc-100" />
          </div>
        </div>
      </main>
    </div>
  );
}

export function EntitiesDirectorySkeleton() {
  return (
    <div className="min-h-screen bg-[#F5F5F3]">
      <div className="h-44 w-full bg-[#0B0B0E]" />
      <RacingProgressBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <div className="mb-4 h-4 w-48 animate-pulse rounded-sm bg-zinc-200" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
            <div
              key={n}
              className="h-32 animate-pulse rounded-sm border border-zinc-200 border-l-[3px] border-l-zinc-300 bg-white p-4"
            />
          ))}
        </div>
      </main>
    </div>
  );
}

export function EntityDetailSkeleton() {
  return (
    <div className="min-h-screen bg-[#F5F5F3]">
      <div className="h-14 w-full bg-[#0B0B0E]" />
      <RacingProgressBar />
      <main className="mx-auto max-w-4xl px-4 py-7 sm:px-6">
        <div className="mb-4 h-4 w-40 animate-pulse rounded-sm bg-zinc-200" />
        <div className="space-y-5 rounded-sm border border-zinc-200 border-l-4 border-l-[#E10600] bg-white p-8">
          <div className="flex items-start justify-between gap-4 border-b border-zinc-100 pb-5">
            <div className="space-y-2">
              <div className="h-3 w-28 animate-pulse rounded-sm bg-zinc-200" />
              <div className="h-8 w-64 animate-pulse rounded-sm bg-zinc-200" />
            </div>
            <div className="h-9 w-40 animate-pulse rounded-sm bg-zinc-200" />
          </div>
          <div className="h-4 w-3/4 animate-pulse rounded-sm bg-zinc-100" />
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <div
                key={n}
                className="h-7 w-24 animate-pulse rounded-sm bg-zinc-100"
              />
            ))}
          </div>
          <div className="space-y-2 pt-2">
            <div className="h-14 animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-14 animate-pulse rounded-sm bg-zinc-100" />
            <div className="h-14 animate-pulse rounded-sm bg-zinc-100" />
          </div>
        </div>
      </main>
    </div>
  );
}

