"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const poweredBy = ["X/Twitter API", "Filecoin/IPFS", "Lighthouse", "CoinGecko", "NLP Engine", "Clerk Auth"];

export function Hero() {
  return (
    <section className="relative pt-32 pb-24 px-6 overflow-hidden bg-grid hero-spotlight">
      <div className="absolute inset-0 hero-spotlight pointer-events-none" />

      <div className="relative max-w-4xl mx-auto text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 mb-6"
        >
          <span className="badge">🧠 Prescient Information Hub</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08 }}
          className="text-[52px] md:text-[72px] lg:text-[84px] font-bold tracking-tighter leading-[1.0] text-[#0a0a0a] mb-6"
        >
          Social intelligence.{" "}
          <span className="text-[#7c3aed]">Stored forever.</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="text-[18px] md:text-[20px] text-[#71717a] max-w-xl mx-auto mb-10 leading-relaxed"
        >
          Curated tweets from top influencers, scored by NLP sentiment analysis, 
          and permanently archived on Filecoin. Real-time insights for Crypto, Stocks, Tech & Geopolitics.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.22 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <Link
            href="/login"
            className="px-6 py-3 bg-[#0a0a0a] text-white text-[15px] font-semibold rounded-full hover:opacity-80 transition-opacity"
          >
            <span className="uppercase tracking-[0.08em]">Get started free</span>
          </Link>
          <a
            href="https://github.com/Juls95/prescient"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-[#f4f4f5] text-[#0a0a0a] text-[15px] font-semibold rounded-full border border-[#e4e4e7] hover:bg-[#ececec] transition-colors"
          >
            View on GitHub
          </a>
        </motion.div>

        {/* Powered by */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-16"
        >
          <p className="text-[13px] text-[#a1a1aa] mb-5 uppercase tracking-widest font-medium">
            Powered by
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8">
            {poweredBy.map((name) => (
              <span
                key={name}
                className="text-[14px] font-semibold text-[#a1a1aa] hover:text-[#71717a] transition-colors cursor-default"
              >
                {name}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
