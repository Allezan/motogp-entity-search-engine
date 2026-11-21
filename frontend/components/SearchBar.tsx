import Link from "next/link";
import type { ViewMode } from "@/lib/types";
import SearchInputField from "@/components/SearchInputField";

const EXAMPLE_QUERIES = [
  { label: "Pecco Silverstone", query: "pecco keluhkan fisik di silverstone" },
  { label: "El Diablo → HRC", query: "el diablo pindah ke hrc" },
  { label: "Tim The Doctor 2027", query: "pembalap baru tim the doctor 2027" },
  { label: "MM93 Aragon", query: "marc marquez tercepat fp1 motorland aragon" },
  {
    label: "Helm MotoGP vs F1",
    query: "perbedaan spesifikasi helm balap motogp dan f1",
  },
];

export function buildSearchHref(opts: {
  q?: string;
  mode?: ViewMode;
  alpha?: number;
  beta?: number;
  details?: boolean;
}): string {
  const params = new URLSearchParams();
  const trimmed = (opts.q || "").trim();
  if (trimmed) params.set("q", trimmed);
  if (opts.mode && opts.mode !== "entity") params.set("mode", opts.mode);
  if (
    opts.alpha !== undefined &&
    opts.beta !== undefined &&
    (Math.abs(opts.alpha - 0.8) > 0.001 || Math.abs(opts.beta - 0.2) > 0.001)
  ) {
    params.set("alpha", String(opts.alpha));
    params.set("beta", String(opts.beta));
  }
  if (opts.details) params.set("details", "1");
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

type Props = {
  query: string;
  mode: ViewMode;
  alpha: number;
  beta: number;
  showDetails: boolean;
  compact?: boolean;
};

export default function SearchBar({
  query,
  mode,
  alpha,
  beta,
  showDetails,
  compact = false,
}: Props) {
  const nonDefaultWeights =
    Math.abs(alpha - 0.8) > 0.001 || Math.abs(beta - 0.2) > 0.001;

  return (
    <div className="w-full max-w-2xl">
      <form
        method="GET"
        action="/"
        className="flex w-full items-stretch overflow-hidden rounded-sm border border-white/25 bg-white shadow-sm transition-colors focus-within:border-[#E10600]"
      >
        {mode !== "entity" && (
          <input type="hidden" name="mode" value={mode} />
        )}
        {nonDefaultWeights && (
          <>
            <input type="hidden" name="alpha" value={String(alpha)} />
            <input type="hidden" name="beta" value={String(beta)} />
          </>
        )}
        {showDetails && <input type="hidden" name="details" value="1" />}

        <SearchInputField initialQuery={query} />

        <button
          type="submit"
          className="shrink-0 bg-[#E10600] px-7 font-display text-sm font-bold uppercase tracking-[0.14em] text-white transition-colors hover:bg-[#BE0500]"
        >
          Cari
        </button>
      </form>

      {!compact && (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            Kueri Uji:
          </span>
          {EXAMPLE_QUERIES.map((item) => (
            <Link
              key={item.query}
              prefetch={false}
              href={buildSearchHref({
                q: item.query,
                mode,
                alpha,
                beta,
                details: showDetails,
              })}
              className="rounded-sm border border-white/20 bg-[#0B0B0E]/65 px-2.5 py-1 font-sans text-xs font-medium text-zinc-200 transition-colors hover:border-[#E10600] hover:bg-[#E10600] hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
