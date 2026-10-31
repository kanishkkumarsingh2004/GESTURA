"use client";

import NextLink from "next/link";

export function Link({
  children,
  href,
  className = "",
  ...props
}: {
  children: React.ReactNode;
  href: string;
  className?: string;
} & React.AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <NextLink
      href={href}
      className={className}
      {...(props as Record<string, unknown>)}
    >
      {children}
    </NextLink>
  );
}
