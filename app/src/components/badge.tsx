import { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "yellow" | "success" | "error" | "neutral" | "outline";
  size?: "sm" | "md";
  className?: string;
  dot?: boolean;
}

const variants = {
  yellow: "bg-yellow-dim text-yellow-accent border border-yellow-accent/30",
  success: "bg-status-success/10 text-status-success border border-status-success/30",
  error: "bg-status-error/10 text-status-error border border-status-error/30",
  neutral: "bg-surface-elevated text-text-secondary border border-surface-border",
  outline: "bg-transparent text-text-secondary border border-surface-border",
};

const sizes = {
  sm: "px-2 py-0.5 text-xs font-mono",
  md: "px-2.5 py-1 text-xs font-medium",
};

export function Badge({
  children,
  variant = "neutral",
  size = "sm",
  className = "",
  dot = false,
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            variant === "yellow"
              ? "bg-yellow-accent animate-pulse"
              : variant === "success"
              ? "bg-status-success animate-pulse"
              : variant === "error"
              ? "bg-status-error"
              : "bg-text-secondary"
          }`}
        />
      )}
      {children}
    </span>
  );
}
