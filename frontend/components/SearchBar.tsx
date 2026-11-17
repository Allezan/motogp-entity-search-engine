"use client";

type Props = {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export default function SearchBar({ value, loading, onChange, onSubmit }: Props) {
  return (
    <form
      className="flex w-full gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Cari berita MotoGP..."
        className="flex-1 rounded-full border border-gray-300 px-5 py-3 text-base outline-none focus:border-red-600"
      />
      <button
        type="submit"
        disabled={loading || value.trim() === ""}
        className="rounded-full bg-red-600 px-6 py-3 font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Cari
      </button>
    </form>
  );
}
