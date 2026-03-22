"use client";

import { motion } from "framer-motion";

const steps = [
  {
    title: "Sign in & explore",
    description: "Create an account with Clerk. Browse the dashboard to see live sentiment scores across all curated groups.",
  },
  {
    title: "Automated collection",
    description: "Our pipeline fetches tweets from 11 curated influencers daily, scores them with NLP, and stores results to Filecoin.",
  },
  {
    title: "Deep-dive intelligence",
    description: "Click into any asset for AI classification: bullish/bearish signals, price targets, engagement metrics, and all raw tweets.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6 bg-[#fafafa]">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-[38px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] mb-12 max-w-2xl"
        >
          How Traipp works.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="jet-card p-6"
            >
              <div className="text-[12px] font-semibold tracking-wide text-[#a1a1aa] mb-2">STEP {i + 1}</div>
              <h3 className="text-[19px] font-semibold text-[#0a0a0a] mb-2">{step.title}</h3>
              <p className="text-[14px] text-[#71717a] leading-relaxed">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
