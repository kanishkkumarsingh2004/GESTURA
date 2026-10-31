"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { getModelInfo, type ModelInfoResponse } from "@/lib/api";
import { Cpu, Layers, HardDrive, Sparkles, AlertCircle } from "lucide-react";

export default function ModelInfoPage() {
  const [info, setInfo] = useState<ModelInfoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getModelInfo();
        setInfo(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to connect to backend model registry. Start FastAPI to query active checkpoints."
        );
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
          <div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Neural Model Specifications
            </h1>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Architecture telemetry, input tensor dimensions, and active checkpoint parameters.
            </p>
          </div>

          <Link
            href="/studio"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-yellow-accent text-black font-semibold text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Studio</span>
          </Link>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Specs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-surface-card border-surface-border space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
              <Cpu className="w-4 h-4 text-yellow-accent" />
              <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
                Architecture & Device
              </h3>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Backbone:</span>
                <span className="text-white">{info?.architecture ?? "vgg16 (PyTorch)"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Target Device:</span>
                <span className="text-white">{info?.device ?? "cuda / cpu auto"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Weights Loaded:</span>
                <span className={info?.loaded ? "text-status-success" : "text-yellow-accent"}>
                  {info?.loaded ? "TRUE (Ready)" : "Lazy on first inference"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-text-muted">Input Shape:</span>
                <span className="text-white">
                  {info?.input_size ? `${info.input_size.join(" × ")}` : "3 × 224 × 224 (RGB)"}
                </span>
              </div>
            </div>
          </Card>

          <Card className="bg-surface-card border-surface-border space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
              <Layers className="w-4 h-4 text-yellow-accent" />
              <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
                Classification Head
              </h3>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Number of Classes:</span>
                <span className="text-yellow-accent font-bold">{info?.num_classes ?? 22}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Vocabulary Core:</span>
                <span className="text-white">10 Spoken Phrases + NONE</span>
              </div>
              <div className="flex justify-between py-1 border-b border-surface-border/40">
                <span className="text-text-muted">Loss Function:</span>
                <span className="text-white">CrossEntropyLoss</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-text-muted">Optimizer:</span>
                <span className="text-white">AdamW (lr=0.0001, wd=0.0001)</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Classes List */}
        {info?.class_names && (
          <Card className="bg-surface-card border-surface-border space-y-3">
            <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
              Registered Class Indices ({info.class_names.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {info.class_names.map((name, i) => (
                <span
                  key={name}
                  className="px-2.5 py-1 rounded bg-surface-secondary border border-surface-border text-xs font-mono text-text-secondary"
                >
                  <span className="text-yellow-accent mr-1.5">#{i}</span>
                  {name}
                </span>
              ))}
            </div>
          </Card>
        )}
      </main>

      <Footer />
    </div>
  );
}
