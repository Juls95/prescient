import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
});

export const metadata: Metadata = {
  title: "Prescient | Autonomous Prediction Markets Powered by AI Agents",
  description: "AI agents autonomously discover events, create markets, and resolve outcomes using on-chain data and social signals. Powered by Dune Analytics and Uniswap v4.",
  keywords: ["prediction markets", "AI agents", "DeFi", "Uniswap", "Dune Analytics", "Base", "blockchain"],
  authors: [{ name: "Julian Ramirez" }],
  openGraph: {
    title: "Prescient | Autonomous Prediction Markets",
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
