"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getHealth, BACKEND_URL } from "@/lib/api";
import { Menu, X, Activity, Sparkles } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"online" | "offline" | "checking">("checking");

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await getHealth();
        if (isMounted) {
          setBackendStatus(res.status === "ok" || res.model_loaded ? "online" : "offline");
        }
      } catch {
        if (isMounted) {
          setBackendStatus("offline");
        }
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  const navLinks = [
    { href: "/studio", label: "Studio" },
    { href: "/gestures", label: "Gesture Library" },
    { href: "/history", label: "History" },
    { href: "/about", label: "About" },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-surface-border bg-background/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-surface-card border border-surface-border flex items-center justify-center group-hover:border-yellow-accent/60 transition-colors">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                className="w-5 h-5 text-yellow-accent"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0" />
                <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2" />
                <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8" />
                <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15" />
              </svg>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="font-heading font-bold text-lg tracking-wider text-text-primary">
                  GESTURA
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-accent" />
              </div>
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest -mt-1">
                VISION AI
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? "text-yellow-accent bg-surface-card border border-yellow-accent/20"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Right Action & Status */}
          <div className="hidden md:flex items-center gap-3">
            {/* Backend connection indicator */}
            <div
              title={
                backendStatus === "online"
                  ? `Backend API connected (${BACKEND_URL || "proxy"})`
                  : `Backend offline. Operating in client workspace mode.`
              }
              className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-card border border-surface-border text-xs font-mono"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "online"
                    ? "bg-status-success animate-pulse"
                    : backendStatus === "checking"
                    ? "bg-yellow-accent animate-pulse"
                    : "bg-status-warning"
                }`}
              />
              <span className="text-text-secondary">
                {backendStatus === "online"
                  ? "API Connected"
                  : backendStatus === "checking"
                  ? "Connecting..."
                  : "Standalone"}
              </span>
            </div>

            {/* Launch Studio CTA */}
            {pathname !== "/studio" && (
              <Link
                href="/studio"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-yellow-accent text-black font-semibold text-xs tracking-wide hover:bg-yellow-hover shadow-sm transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Launch Studio</span>
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded-lg bg-surface-card border border-surface-border text-text-secondary hover:text-text-primary"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-b border-surface-border bg-surface-secondary px-4 py-3 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm font-medium ${
                pathname === link.href
                  ? "text-yellow-accent bg-surface-card"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 border-t border-surface-border flex items-center justify-between">
            <span className="text-xs font-mono text-text-muted">
              Status: {backendStatus === "online" ? "API Connected" : "Standalone"}
            </span>
            <Link
              href="/studio"
              onClick={() => setMobileOpen(false)}
              className="px-3 py-1.5 rounded-lg bg-yellow-accent text-black text-xs font-semibold"
            >
              Open Studio
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
