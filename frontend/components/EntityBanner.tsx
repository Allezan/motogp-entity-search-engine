import Link from "next/link";
import type { RecognizedEntity } from "@/lib/types";
import { getCategoryTagStyle } from "@/lib/format";

type Props = {
  recognizedEntities: RecognizedEntity[];
  entityFallback: boolean;
  preprocessedQuery: string;
  showIrDetails: boolean;
  isBaselineOnly?: boolean;
  alpha?: number | null;
  beta?: number | null;
};

export default function EntityBanner({
  recognizedEntities,
  entityFallback,
  preprocessedQuery,
  showIrDetails,
  isBaselineOnly = false,
  alpha,
  beta,
}: Props) {
  const accentBorder =
    entityFallback && !isBaselineOnly
      ? "border-l-amber-600"
      : isBaselineOnly
        ? "border-l-zinc-500"
        : "border-l-[#E10600]";

  return (
    <div
      className={`rounded-sm border border-zinc-200 border-l-[3px] bg-white px-4 py-3 ${accentBorder}`}
    >
      {/* Row 1: Detected Entities (Direct SSR Links to /entities/[id]) */}
      <div className="flex flex-wrap items-center gap-2.5">
        <span className="font-display text-xs font-bold uppercase tracking-[0.12em] text-zinc-500">
          Entitas Kueri
        </span>
        <span className="text-zinc-300">|</span>

        {recognizedEntities.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2">
            {recognizedEntities.map((ent) => {
              const cat = getCategoryTagStyle(ent.category);
              const aliasDiffers =
                ent.matched_text.toLowerCase() !== ent.name.toLowerCase();
              return (
                <Link
                  key={ent.entity_id}
                  href={`/entities/${encodeURIComponent(ent.entity_id)}`}
                  title={`Buka profil & artikel terkait ${ent.name}`}
                  className={`group inline-flex items-center gap-2 rounded-sm border border-zinc-200 border-l-2 bg-[#FAF9F7] px-2.5 py-1 text-left transition-colors hover:border-zinc-400 hover:bg-white ${cat.borderLeftClass}`}
                >
                  <span
                    className={`font-mono text-[10px] font-semibold tracking-wider ${cat.accentClass}`}
                  >
                    {cat.shortLabel}
                  </span>
                  <span className="font-titillium text-xs font-bold text-[#111114] group-hover:text-[#E10600]">
                    {ent.name}
                  </span>
                  {aliasDiffers && (
                    <span className="font-mono text-[10px] text-zinc-400">
                      ← &ldquo;{ent.matched_text}&rdquo;
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ) : (
          <span className="font-sans text-xs font-medium text-amber-800">
            Tidak ada entitas MotoGP terdeteksi
          </span>
        )}
      </div>

      {/* Fallback or Baseline Notice */}
      {entityFallback && !isBaselineOnly && (
        <p className="mt-2 font-sans text-xs text-amber-800">
          <strong>Fallback aktif:</strong> Karena kueri tidak memuat entitas
          dari kamus MotoGP (E<sub>Q</sub> = ∅), sistem otomatis memakai
          peringkat <strong>Baseline TF-IDF</strong> murni.
        </p>
      )}

      {isBaselineOnly && (
        <p className="mt-2 font-sans text-xs text-zinc-500">
          Mode <strong>Baseline TF-IDF</strong> — peringkat dihitung murni dari
          Cosine Similarity teks tanpa skor entitas.
        </p>
      )}

      {/* Row 2: Optional IR Telemetry Details */}
      {showIrDetails && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 pt-2.5 font-mono text-[11px] text-zinc-500">
          <div className="flex items-center gap-2">
            <span className="uppercase tracking-wider text-zinc-400">
              Token:
            </span>
            <code className="rounded-sm bg-zinc-100 px-2 py-0.5 text-zinc-700">
              {preprocessedQuery || "—"}
            </code>
          </div>

          {!isBaselineOnly && !entityFallback && alpha != null && beta != null && (
            <div className="tabular-nums text-zinc-600">
              S_final = {alpha}·S_text + {beta}·S_entity
            </div>
          )}
        </div>
      )}
    </div>
  );
}
