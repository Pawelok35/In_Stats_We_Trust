import type { Metadata } from "next";
import { Space_Mono, Work_Sans } from "next/font/google";
import "./globals.css";

const displayFont = Space_Mono({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "700"],
});

const bodyFont = Work_Sans({
  variable: "--font-body",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "In Stats We Trust",
  description: "Retro dashboard for weekly NFL matchup reports.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        suppressHydrationWarning
        className={`${displayFont.variable} ${bodyFont.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
