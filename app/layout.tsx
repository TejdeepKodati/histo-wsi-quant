import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HistoWSI Quant | Whole Slide Pathology & Morphometry Engine",
  description: "High-resolution digital pathology WSI analytics, stain normalization, and deep learning nuclei morphometry platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        {children}
      </body>
    </html>
  );
}
