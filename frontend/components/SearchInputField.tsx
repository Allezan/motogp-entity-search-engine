"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  initialQuery: string;
};

export default function SearchInputField({ initialQuery }: Props) {
  const [value, setValue] = useState(initialQuery);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setValue(initialQuery);
  }, [initialQuery]);

  return (
    <div className="relative flex flex-1 items-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
        className="pointer-events-none absolute left-3.5 h-4 w-4 text-zinc-400"
      >
        <path
          fillRule="evenodd"
          d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.452 4.391l3.328 3.329a.75.75 0 1 1-1.06 1.06l-3.329-3.328A7 7 0 0 1 2 9Z"
          clipRule="evenodd"
        />
      </svg>

      <input
        ref={inputRef}
        type="text"
        name="q"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        required
        placeholder="Cari berita MotoGP — pembalap, julukan, tim, atau sirkuit..."
        aria-label="Kata kunci pencarian berita MotoGP"
        className="w-full bg-transparent py-3 pl-10 pr-9 font-sans text-sm text-[#111114] placeholder:text-zinc-400 outline-none"
      />

      {value && (
        <button
          type="button"
          onClick={() => {
            setValue("");
            inputRef.current?.focus();
          }}
          aria-label="Hapus teks pencarian"
          title="Hapus teks"
          className="absolute right-2.5 flex h-6 w-6 items-center justify-center rounded-sm text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-700"
        >
          ✕
        </button>
      )}
    </div>
  );
}

