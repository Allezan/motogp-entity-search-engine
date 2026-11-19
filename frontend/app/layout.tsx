import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  description: "Mesin pencari berita MotoGP",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-gray-100 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}