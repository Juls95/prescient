"use client";

import { clsx } from "clsx";
import { motion } from "framer-motion";

interface ButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  className?: string;
  onClick?: () => void;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  onClick,
}: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center rounded-full font-semibold tracking-tight transition-all duration-200";

  const variants = {
    primary: "bg-[#0a0a0a] text-white shadow-[0_1px_2px_rgba(0,0,0,0.05)] ring-1 ring-inset ring-white/10 hover:opacity-85",
    secondary: "bg-[#f4f4f5] text-[#0a0a0a] border border-[#e4e4e7] hover:bg-[#ececec]",
    ghost: "bg-transparent text-[#71717a] hover:text-[#0a0a0a]",
  };

  const sizes = {
    sm: "px-4 py-2 text-[14px]",
    md: "px-5 py-2.5 text-[14px]",
    lg: "px-6 py-3 text-[15px]",
  };

  return (
    <motion.button
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.99 }}
      className={clsx(baseStyles, variants[variant], sizes[size], className)}
      onClick={onClick}
    >
      {children}
    </motion.button>
  );
}
