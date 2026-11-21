import type { Metadata } from "next";
import {
  Barlow_Condensed,
  JetBrains_Mono,
  Plus_Jakarta_Sans,
  Titillium_Web,
} from "next/font/google";
import "./globals.css";

const barlowCondensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

const titilliumWeb = Titillium_Web({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-titillium",
  display: "swap",
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MotoGP Entity-Aware Search Engine",
  description:
    "Mesin pencari berita MotoGP berbasis TF-IDF + Cosine Similarity dan Entity-Aware Search",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="id"
      className={`${barlowCondensed.variable} ${titilliumWeb.variable} ${plusJakartaSans.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-[#F5F5F3] font-sans text-[#111114] antialiased selection:bg-[#E10600] selection:text-white">
        {children}
      </body>
    </html>
  );
}
