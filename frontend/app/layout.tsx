import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MotoGP News Search",
  description: "Mesin pencari berita MotoGP",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body className="bg-white text-gray-900 antialiased">{children}</body>
    </html>
  );
}
