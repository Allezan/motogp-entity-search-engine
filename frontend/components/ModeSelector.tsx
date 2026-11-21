import Link from "next/link";
import type { ViewMode } from "@/lib/types";
import { buildSearchHref } from "@/components/SearchBar";

const WEIGHT_PRESETS = [
  { label: "α 0.8 / β 0.2", tag: "Default v5", alpha: 0.8, beta: 0.2 },
  { label: "α 0.9 / β 0.1", tag: "Teks Dominan", alpha: 0.9, beta: 0.1 },
  { label: "α 0.7 / β 0.3", tag: "Entitas Kuat", alpha: 0.7, beta: 0.3 },
];

type Props = {
  query: string;
  viewMode: ViewMode;
  alpha: number;
  beta: number;
  showDetails: boolean;
};

export default function ModeSelector({
  query,
  viewMode,
  alpha,
  beta,
  showDetails,
}: Props) {
  const modes: { id: ViewMode; label: string; desc: string }[] = [
    { id: "entity", label: "Entity-Aware", desc: "TF-IDF + Kamus Entitas" },
    { id: "baseline", label: "Baseline TF-IDF", desc: "TF-IDF + Cosine Murni" },
    {
      id: "compare",
      label: "Compare",
      desc: "Bandingkan Baseline vs Entity-Aware",
    },
  ];

  return (
    <div className="w-full max-w-2xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/15">
        {/* Editorial Underline Tabs (Pure SSR Links) */}
        <div
          role="tablist"
          aria-label="Mode pencarian"
          className="flex items-center gap-6"
        >
          {modes.map((m) => {
            const active = viewMode === m.id;
            return (
              <Link
                key={m.id}
                href={buildSearchHref({
                  q: query,
                  mode: m.id,
                  alpha,
                  beta,
                  details: showDetails,
                })}
                role="tab"
                aria-selected={active}
                title={m.desc}
                className={`relative pb-2.5 pt-1 font-display text-sm font-bold uppercase tracking-[0.1em] transition-colors ${
                  active ? "text-white" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {m.label}
                {active && (
                  <span className="absolute inset-x-0 -bottom-px h-[2px] bg-[#E10600]" />
                )}
              </Link>
            );
          })}
        </div>

        {/* Toggle IR Telemetry Details via SSR URL query param (Zero JS) */}
        <Link
          href={buildSearchHref({
            q: query,
            mode: viewMode,
            alpha,
            beta,
            details: !showDetails,
          })}
          className={`mb-1.5 inline-flex items-center gap-1.5 rounded-sm border px-2.5 py-1 font-mono text-[11px] transition-colors ${
            showDetails
              ? "border-[#E10600]/80 bg-[#141419] text-white"
              : "border-white/15 bg-transparent text-zinc-400 hover:border-white/30 hover:text-zinc-200"
          }`}
        >
          <span>Pengaturan IR</span>
          {viewMode !== "baseline" && (
            <span className="text-zinc-500">
              · {alpha}/{beta}
            </span>
          )}
          <span className="text-[10px] leading-none">
            {showDetails ? "▴" : "▾"}
          </span>
        </Link>
      </div>

      {/* Server-Rendered Collapsible IR Weight Tray */}
      {showDetails && (
        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-3 rounded-sm border border-white/12 bg-[#141419]/95 px-3.5 py-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Bobot Hybrid:
            </span>
            {WEIGHT_PRESETS.map((p) => {
              const active =
                Math.abs(alpha - p.alpha) < 0.001 &&
                Math.abs(beta - p.beta) < 0.001;
              if (viewMode === "baseline") {
                return (
                  <span
                    key={p.label}
                    className="cursor-not-allowed rounded-sm border border-white/10 px-2.5 py-1 font-mono text-[11px] text-zinc-500 opacity-50"
                  >
                    {p.label} ({p.tag})
                  </span>
                );
              }
              return (
                <Link
                  key={p.label}
                  href={buildSearchHref({
                    q: query,
                    mode: viewMode,
                    alpha: p.alpha,
                    beta: p.beta,
                    details: true,
                  })}
                  className={`rounded-sm border px-2.5 py-1 font-mono text-[11px] transition-colors ${
                    active
                      ? "border-[#E10600] bg-[#E10600]/15 text-white"
                      : "border-white/15 text-zinc-300 hover:border-white/35 hover:text-white"
                  }`}
                >
                  {p.label} <span className="text-zinc-400">({p.tag})</span>
                </Link>
              );
            })}
          </div>
          <span className="font-mono text-[11px] text-zinc-500">
            Engine: v5 From-Scratch · Pure SSR
          </span>
        </div>
      )}
    </div>
  );
}
