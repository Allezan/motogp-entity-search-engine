import type { SearchResult } from "@/lib/types";

export default function ResultItem({ result }: { result: SearchResult }) {
  return (
    <a
      href={result.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-md hover:bg-gray-100"
    >
      <h2 className="text-lg font-semibold text-red-700">{result.title}</h2>
      <p className="mt-1 line-clamp-3 text-sm text-gray-600">{result.content}</p>
    </a>
  );
}
