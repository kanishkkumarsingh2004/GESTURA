"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

const variants = {
  primary:
    "bg-yellow-accent text-black font-semibold hover:bg-yellow-hover shadow-sm active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none",
  secondary:
    "bg-surface-elevated text-text-primary border border-surface-border hover:border-text-secondary/40 active:scale-[0.98] disabled:opacity-50",
  outline:
    "border border-yellow-accent/40 text-yellow-accent hover:bg-yellow-dim active:scale-[0.98] disabled:opacity-50",
  ghost:
    "text-text-secondary hover:text-text-primary hover:bg-surface-elevated active:scale-[0.98]",
  danger:
    "border border-status-error/40 text-status-error hover:bg-status-error/10 active:scale-[0.98]",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs rounded-md gap-1.5",
  md: "px-4 py-2 text-sm rounded-lg gap-2",
  lg: "px-6 py-3 text-base rounded-lg gap-2.5",
  icon: "p-2 rounded-lg aspect-square justify-center",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = "",
      variant = "primary",
      size = "md",
      disabled,
      isLoading,
      children,
      ...props
    },
    ref
  ) => (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center font-medium transition-all duration-150 cursor-pointer ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <>
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
          <span>Loading...</span>
        </>
      ) : (
        children
      )}
    </button>
  )
);
Button.displayName = "Button";
