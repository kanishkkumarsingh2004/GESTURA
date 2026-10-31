"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/card";
import { Button } from "@/components/button";
import { Badge } from "@/components/badge";
import { getGestures } from "@/lib/api";

export default function GesturesPage() {
  const [gestures, setGestures] = useState<{ class_id: number; class_name: string; text: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getGestures();
        setGestures(data.classes);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load gestures");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-navy text-white">
      <nav className="sticky top-0 z-50 border-b border-slate-800 bg-navy/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 text-slate-300 hover:text-white">
            <span className="text-electric-blue">←</span>
            <span className="font-medium">Back</span>
          </a>
          <span className="font-bold text-lg tracking-tight">Gestures</span>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Supported Gestures</h1>
          {error && (
            <span className="text-red-400 text-sm">{error}</span>
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <button className="animate-pulse rounded-full bg-slate-800 h-10 w-10"></button>
          </div>
        ) : gestures.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-slate-500">
            No gestures available
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {gestures.map((g) => (
              <Card key={g.class_id} padding="md">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-mono text-slate-400 mb-1">
                      Class {g.class_id}
                    </div>
                    <div className="text-lg font-bold text-white">{g.class_name}</div>
                    <div className="text-sm text-electric-blue">{g.text}</div>
                  </div>
                  <Badge variant="info">{g.class_name}</Badge>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
