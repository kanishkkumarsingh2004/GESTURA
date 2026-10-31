"use client";

import { useEffect, useState } from "react";
import { Link } from "@/components/link";
import { Navbar } from "@/components/navbar";

export default function Home() {
  const [health, setHealth] = useState<{
    status: string;
    model_loaded: boolean;
    version: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/health");
        if (!res.ok) throw new Error("Health check failed");
        setHealth(await res.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-navy text-white">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-white mb-2">
            Gesture Recognition
          </h1>
          <p className="text-slate-400">
            Real-time hand gesture recognition and audio assistant. Connects to
            the FastAPI backend to recognize gestures from images.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate border border-slate-700 rounded-xl p-6">
            <div className="text-slate-400 text-sm font-medium mb-1">Status</div>
            <div className="text-xl font-mono text-white">
              {health?.status ?? "—"}
            </div>
          </div>
          <div className="bg-slate border border-slate-700 rounded-xl p-6">
            <div className="text-slate-400 text-sm font-medium mb-1">Model</div>
            <div className="text-xl font-mono text-white">
              {health?.model_loaded ? "Loaded" : "Not loaded"}
            </div>
          </div>
          <div className="bg-slate border border-slate-700 rounded-xl p-6">
            <div className="text-slate-400 text-sm font-medium mb-1">Version</div>
            <div className="text-xl font-mono text-white">{health?.version ?? "—"}</div>
          </div>
        </div>

        {error && (
          <div className="mt-6 p-4 rounded-lg bg-red-900/20 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          <a href="/predict" className="group relative">
            <div className="bg-slate border border-slate-700 rounded-xl p-8 overflow-hidden group-hover:border-electric-blue/50 transition-colors">
              <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                <svg
                  className="w-8 h-8 text-electric-blue"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Predict Gesture</h3>
              <p className="text-slate-400 text-sm mb-4">
                Upload an image to classify a hand gesture using the model.
              </p>
              <span className="inline-flex items-center gap-1 text-electric-blue text-sm font-medium">
                Go to Predict <span>→</span>
              </span>
            </div>
          </a>

          <a href="/gestures" className="group relative">
            <div className="bg-slate border border-slate-700 rounded-xl p-8 overflow-hidden group-hover:border-electric-blue/50 transition-colors">
              <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                <svg
                  className="w-8 h-8 text-electric-blue"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Gestures</h3>
              <p className="text-slate-400 text-sm mb-4">
                View all supported gesture classes and their spoken phrases.
              </p>
              <span className="inline-flex items-center gap-1 text-electric-blue text-sm font-medium">
                View Gestures <span>→</span>
              </span>
            </div>
          </a>
        </div>
      </main>
    </div>
  );
}
