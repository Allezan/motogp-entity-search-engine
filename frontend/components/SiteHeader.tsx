import Link from "next/link";
import type { HealthResponse, IndexStatus } from "@/lib/types";

type Props = {
  health?: HealthResponse | null;
  indexStatus?: IndexStatus | null;
  activeNav?: "search" | "entities";
};

export default function SiteHeader({
  health = null,
  indexStatus = null,
  activeNav = "search",
}: Props) {
  return (
    <nav className="relative z-10 w-full border-b border-white/10">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
        <Link
          href="/"
          prefetch={false}
          className="inline-flex items-baseline gap-2 text-left transition-opacity hover:opacity-85"
        >
          <span className="font-display text-base font-extrabold uppercase tracking-[0.14em] text-white">
            MotoGP
          </span>
          <span className="font-display text-sm font-bold text-[#E10600]">
            /
          </span>
          <span className="font-display text-xs font-semibold uppercase tracking-[0.16em] text-zinc-400">
            Entity-Aware Search
          </span>
        </Link>

        <div className="flex items-center gap-4">
          {indexStatus?.num_documents && (
            <span
              title={`Engine: ${health?.engine || "v5-from-scratch"} | DB: ${health?.database || "artifact"} | 100% Pure SSR`}
              className="hidden font-mono text-[11px] uppercase tracking-wider text-zinc-400 tabular-nums sm:inline"
            >
              {indexStatus.num_documents} Berita · {indexStatus.num_entities}{" "}
              Entitas
            </span>
          )}

          <Link
            href="/entities"
            prefetch={false}
            className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 font-display text-xs font-bold uppercase tracking-[0.12em] transition-colors ${
              activeNav === "entities"
                ? "border-[#E10600] bg-[#E10600] text-white"
                : "border-white/25 text-white hover:border-[#E10600] hover:bg-[#E10600]"
            }`}
          >
            <span>Kamus Entitas</span>
            {indexStatus?.num_entities && (
              <span className="font-mono text-[11px] font-normal text-zinc-200 tabular-nums">
                {indexStatus.num_entities}
              </span>
            )}
          </Link>
        </div>
      </div>
    </nav>
  );
}

