export function getCategoryTagStyle(category?: string | null): {
  shortLabel: string;
  accentClass: string;
  borderLeftClass: string;
} {
  switch ((category || "").toLowerCase()) {
    case "rider":
      return {
        shortLabel: "RIDER",
        accentClass: "text-[#E10600]",
        borderLeftClass: "border-l-[#E10600]",
      };
    case "team":
      return {
        shortLabel: "TEAM",
        accentClass: "text-blue-700",
        borderLeftClass: "border-l-blue-700",
      };
    case "manufacturer":
      return {
        shortLabel: "MFG",
        accentClass: "text-amber-700",
        borderLeftClass: "border-l-amber-600",
      };
    case "circuit":
      return {
        shortLabel: "CIRCUIT",
        accentClass: "text-emerald-700",
        borderLeftClass: "border-l-emerald-700",
      };
    default:
      return {
        shortLabel: "ENTITY",
        accentClass: "text-zinc-600",
        borderLeftClass: "border-l-zinc-500",
      };
  }
}

export function formatDateId(dateStr?: string | null): string {
  if (!dateStr) return "";
  const parsed = new Date(dateStr);
  if (Number.isNaN(parsed.getTime())) return dateStr;
  return parsed.toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatRank(rank: number): string {
  return String(rank).padStart(2, "0");
}
