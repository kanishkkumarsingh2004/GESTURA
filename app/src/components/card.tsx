import { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
  elevated?: boolean;
  hoverEffect?: boolean;
}

export function Card({
  children,
  className = "",
  elevated = false,
  hoverEffect = false,
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-xl border ${
        elevated
          ? "bg-surface-elevated border-surface-border"
          : "bg-surface-card border-surface-border"
      } ${
        hoverEffect
          ? "transition-all duration-200 hover:border-yellow-accent/40 hover:shadow-lg hover:shadow-black/40"
          : ""
      } p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
