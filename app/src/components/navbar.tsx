"use client";

import Link from "next/link";

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-navy/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-electric-blue">✋</span>
            <span className="font-bold text-xl tracking-tight">Gesture Recognition</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/" className="px-3 py-2 rounded-md text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Dashboard
            </Link>
            <Link href="/predict" className="px-3 py-2 rounded-md text-sm font-medium text-electric-blue hover:bg-electric-blue/10 transition-colors">
              Predict
            </Link>
            <Link href="/gestures" className="px-3 py-2 rounded-md text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Gestures
            </Link>
            <Link href="/model-info" className="px-3 py-2 rounded-md text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Model Info
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
