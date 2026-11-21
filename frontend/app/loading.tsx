import {
  RacingProgressBar,
  SearchResultsSkeleton,
} from "@/components/LoadingSkeletons";

export default function Loading() {
  return (
    <div className="min-h-screen bg-[#F5F5F3]">
      <div className="h-36 w-full bg-[#0B0B0E]" />
      <RacingProgressBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <SearchResultsSkeleton />
      </main>
    </div>
  );
}
