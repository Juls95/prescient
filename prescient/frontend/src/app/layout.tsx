import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
});

export const metadata: Metadata = {
  title: "Traipp | Social Intelligence Hub Powered by AI Agents",
  description: "AI agents curate tweets, score sentiment with NLP, and permanently archive insights on Filecoin. Powered by X/Twitter API, CoinGecko, and Lighthouse.",
  keywords: ["social intelligence", "AI agents", "sentiment analysis", "Filecoin", "crypto", "NLP"],
  authors: [{ name: "Julian Ramirez" }],
  openGraph: {
    title: "Traipp | Social Intelligence Hub",
    description: "AI agents autonomously discover events, create markets, and resolve outcomes",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${geist.variable} font-sans antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
