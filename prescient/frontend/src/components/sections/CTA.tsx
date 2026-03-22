"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function CTA() {
  return (
    <section className="py-24 px-6 border-t border-[#e4e4e7]">
      <div className="max-w-5xl mx-auto jet-card p-10 md:p-14 text-center relative overflow-hidden">
        <div className="absolute inset-0 hero-spotlight pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="relative"
        >
          <h2 className="text-[36px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] mb-4">
            Start tracking social intelligence today.
          </h2>
          <p className="text-[16px] text-[#71717a] max-w-2xl mx-auto mb-8">
            Sign in to explore real-time sentiment scores, AI-classified signals, and permanently archived tweet data across Crypto, Stocks, Tech & Geopolitics.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-7 py-3 rounded-full bg-[#0a0a0a] text-white text-[15px] font-semibold hover:opacity-85 transition-opacity"
          >
            G e t  s t a r t e d  f r e e
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
