import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "var(--font-titillium)", "sans-serif"],
        titillium: ["var(--font-titillium)", "var(--font-sans)", "sans-serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        carbon: {
          950: "#0B0B0E",
          900: "#141419",
          800: "#1E1E26",
        },
        crimson: {
          600: "#E10600",
          700: "#BE0500",
        },
      },
    },
  },
  plugins: [],
};

export default config;
