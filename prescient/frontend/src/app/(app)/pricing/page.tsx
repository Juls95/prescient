"use client";

import { useState } from "react";
import { Check, Zap, Crown, Building2 } from "lucide-react";

const plans = [
  {
    name: "Explorer",
    icon: Zap,
    price: { monthly: 0, yearly: 0 },
    description: "Get started with AI-powered market intelligence",
    features: [
      "Top 10 coin watchlist",
      "Basic price alerts",
      "Community market access",
      "Daily discovery summaries",
      "5 market votes per day",
    ],
    cta: "Current Plan",
    highlighted: false,
    badge: null,
  },
  {
    name: "Pro",
    icon: Crown,
    price: { monthly: 29, yearly: 290 },
    description: "Advanced analytics and unlimited market participation",
    features: [
      "Unlimited watchlist coins",
      "Real-time sentiment analysis",
      "Priority market access",
      "Hourly discovery signals",
      "Unlimited market votes",
      "Custom alerts & notifications",
      "Uniswap v4 direct integration",
      "Filecoin evidence browser",
    ],
    cta: "Upgrade to Pro",
    highlighted: true,
    badge: "Most Popular",
  },
  {
    name: "Institution",
    icon: Building2,
    price: { monthly: 199, yearly: 1990 },
    description: "Enterprise-grade tools for professional traders",
    features: [
      "Everything in Pro",
      "API access (10K req/day)",
      "Custom market creation",
      "Bulk Dune queries",
      "Dedicated agent instance",
      "White-label dashboard",
      "Priority support (SLA)",
      "Custom data pipelines",
    ],
    cta: "Contact Sales",
    highlighted: false,
    badge: null,
  },
];

export default function PricingPage() {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");

  return (
    <div>
      <div className="text-center mb-10">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Pricing</h1>
        <p className="text-[#666] mt-1">Choose the plan that fits your trading strategy</p>

        <div className="inline-flex items-center gap-1 bg-white border border-[#e5e5e5] rounded-lg p-1 mt-6">
          <button
            onClick={() => setBilling("monthly")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
              billing === "monthly" ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBilling("yearly")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
              billing === "yearly" ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
            }`}
          >
            Yearly <span className="text-[#7c3aed] text-xs ml-1">Save 17%</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {plans.map((plan) => {
          const Icon = plan.icon;
          const price = plan.price[billing];
          return (
            <div
              key={plan.name}
              className={`relative bg-white rounded-2xl border p-6 flex flex-col ${
                plan.highlighted ? "border-[#7c3aed] shadow-lg shadow-[#7c3aed]/5" : "border-[#e5e5e5]"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[#7c3aed] text-white text-xs font-medium rounded-full">
                  {plan.badge}
                </div>
              )}

              <div className="flex items-center gap-2 mb-2">
                <Icon size={20} className={plan.highlighted ? "text-[#7c3aed]" : "text-[#999]"} />
                <h3 className="text-lg font-semibold text-[#0a0a0a]">{plan.name}</h3>
              </div>

              <p className="text-sm text-[#666] mb-4">{plan.description}</p>

              <div className="mb-6">
                <span className="text-3xl font-bold text-[#0a0a0a]">${price}</span>
                {price > 0 && <span className="text-sm text-[#999]">/{billing === "monthly" ? "mo" : "yr"}</span>}
              </div>

              <button
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition mb-6 ${
                  plan.highlighted
                    ? "bg-[#7c3aed] text-white hover:opacity-90"
                    : "bg-[#0a0a0a] text-white hover:opacity-85"
                } ${plan.price.monthly === 0 ? "opacity-60 cursor-default" : ""}`}
                disabled={plan.price.monthly === 0}
              >
                {plan.cta}
              </button>

              <ul className="space-y-2.5 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-[#444]">
                    <Check size={16} className="text-[#7c3aed] mt-0.5 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      <div className="text-center mt-10">
        <p className="text-sm text-[#999]">
          All plans include Filecoin-verified evidence storage and ERC-8004 receipt tracking.
        </p>
      </div>
    </div>
  );
}
