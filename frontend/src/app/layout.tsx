import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { MainLayout } from "@/components/layout/MainLayout";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-geist-sans",
});

export const metadata: Metadata = {
  title: "FELETI-SMOK — Управление копчением",
  description:
    "Профессиональная платформа управления коптильным производством. Рецепты, программы, мониторинг, аналитика.",
  keywords: [
    "копчение",
    "коптильная камера",
    "FELETI",
    "рецепты копчения",
    "управление производством",
  ],
  authors: [{ name: "FELETI", url: "https://feleti-smok.by" }],
  metadataBase: new URL("https://feleti-smok.by"),
  openGraph: {
    title: "FELETI-SMOK",
    description: "Профессиональная платформа управления копчением",
    type: "website",
    locale: "ru_RU",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#1a1a1a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans min-h-screen bg-[#0a0a0a] text-white`}>
        <Providers>
          <MainLayout>{children}</MainLayout>
        </Providers>
      </body>
    </html>
  );
}
