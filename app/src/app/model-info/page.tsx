"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { getModelInfo } from "@/lib/api";

export default function ModelInfoPage() {
  const [info, setInfo] = useState<{
    architecture: string;
    num_classes: number;
    class_names: string[];
    input_size: number[];
    device: string;
    loaded: boolean;
    metadata: Record<string, unknown>;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getModelInfo();
        setInfo(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load model info");
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
          <span className="font-bold text-lg tracking-tight">Model Info</span>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">Model Information</h1>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-900/20 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <button className="animate-pulse rounded-full bg-slate-800 h-10 w-10"></button>
          </div>
        ) : !info ? (
          <div className="h-64 flex flex-col items-center justify-center text-slate-500">
            No model information available
          </div>
        ) : (
          <div className="space-y-6">
            <Card>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Badge variant={info.loaded ? "success" : "danger"}>
                    {info.loaded ? "Loaded" : "Not loaded"}
                  </Badge>
                </div>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                  <div className="flex flex-col">
                    <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Architecture
                    </dt>
                    <dd className="text-white font-mono">{info.architecture}</dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Device
                    </dt>
                    <dd className="text-white font-mono">{info.device}</dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Classes
                    </dt>
                    <dd className="text-white font-mono">{info.num_classes}</dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Input Size
                    </dt>
                    <dd className="text-white font-mono">
                      {info.input_size[0]} × {info.input_size[1]}
                    </dd>
                  </div>
                </dl>
              </div>
            </Card>

            <Card>
              <div className="flex flex-col">
                <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Class Names
                </dt>
                <div className="flex flex-wrap gap-2">
                  {info.class_names.map((name) => (
                    <Badge key={name} variant="default">
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
