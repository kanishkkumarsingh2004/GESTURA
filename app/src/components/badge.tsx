"use client";

import { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variants = {
  default: "bg-slate-700 text-slate-200",
  success: "bg-green-900/20 border border-green-500/30 text-green-400",
  warning: "bg-amber-900/20 border border-amber-500/30 text-amber-400",
  danger: "bg-red-900/20 border border-red-500/30 text-red-400",
  info: "bg-blue-900/20 border border-blue-500/30 text-blue-400",
};

export function Badge({
  children,
  className = "",
  variant = "default",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider transition-colors ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
