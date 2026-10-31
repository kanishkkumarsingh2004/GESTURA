"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Button } from "@/components/button";
import { Badge } from "@/components/badge";
import { predictImage, type PredictResponse } from "@/lib/api";
import { speech } from "@/lib/speech";
import {
  Image as LucideImage,
  X,
  UploadCloud,
  Volume2,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Clock,
  Layers,
} from "lucide-react";

export default function PredictPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0] ?? null;
      setFile(f);
      setError(null);
      setResult(null);
      if (f) {
        setPreview(URL.createObjectURL(f));
      } else {
        setPreview(null);
      }
    },
    []
  );

  const removeFile = useCallback(() => {
    setFile(null);
    setPreview(null);
    if (preview) URL.revokeObjectURL(preview);
    setError(null);
    setResult(null);
  }, [preview]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file) return;
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        const data = await predictImage({
          file,
          sessionId: sessionId || undefined,
        });
        setResult(data);
        if (data.class_name && data.class_name !== "NONE") {
          speech.speak(data.class_name.replace(/_/g, " "));
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Classification failed. Ensure the FastAPI backend is online."
        );
      } finally {
        setLoading(false);
      }
    },
    [file, sessionId]
  );

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Banner with Studio Link */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
          <div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Single Image Classification Audit
            </h1>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Upload an image frame to audit gesture recognition probabilities and inference latency.
            </p>
          </div>

          <Link
            href="/studio"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-yellow-accent text-black font-semibold text-xs tracking-wide hover:bg-yellow-hover transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Live Studio</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* UPLOAD FORM (Col 6) */}
          <div className="md:col-span-6 space-y-6">
            <Card className="bg-surface-card border-surface-border">
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase text-text-muted">
                    GESTURE IMAGE FRAME
                  </label>

                  {!preview ? (
                    <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-surface-border hover:border-yellow-accent/40 rounded-xl cursor-pointer bg-surface-secondary/50 transition-colors">
                      <UploadCloud className="w-10 h-10 text-yellow-accent/80 mb-2" />
                      <span className="text-sm font-medium text-white">Select image frame</span>
                      <span className="text-xs text-text-muted mt-1">JPG, PNG, WebP up to 10 MB</span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </label>
                  ) : (
                    <div className="relative rounded-xl overflow-hidden border border-surface-border aspect-video bg-black">
                      <img
                        src={preview}
                        alt="Preview"
                        className="w-full h-full object-contain"
                      />
                      <button
                        type="button"
                        onClick={removeFile}
                        className="absolute top-2 right-2 p-1.5 rounded-full bg-black/80 hover:bg-status-error text-white transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-mono uppercase text-text-muted">
                    OPTIONAL SESSION ID
                  </label>
                  <input
                    type="text"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    placeholder="e.g. test_session_1"
                    className="w-full px-3 py-2 rounded-lg bg-surface-elevated border border-surface-border text-white text-xs font-mono placeholder:text-text-muted focus:border-yellow-accent outline-none"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={!file}
                  isLoading={loading}
                  variant="primary"
                  className="w-full py-2.5"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Run Neural Classification
                </Button>
              </form>
            </Card>

            {error && (
              <div className="p-4 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs flex items-start gap-3">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* PREDICTION RESULTS (Col 6) */}
          <div className="md:col-span-6 space-y-6">
            <Card className="bg-surface-card border-surface-border h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-surface-border text-xs">
                  <span className="font-mono text-text-muted uppercase">AUDIT RESULT</span>
                  {result && (
                    <Badge variant="yellow" size="sm">
                      CONFIRMED
                    </Badge>
                  )}
                </div>

                {!result ? (
                  <div className="py-16 text-center text-text-muted text-xs">
                    Upload an image and run classification to view predicted class, confidence, and
                    full probability distribution.
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Big recognized gesture */}
                    <div className="text-center p-6 rounded-xl bg-surface-secondary border border-surface-border">
                      <div className="text-[10px] font-mono text-text-muted uppercase tracking-widest mb-1">
                        PREDICTED CLASS
                      </div>
                      <div className="font-heading text-4xl font-bold text-yellow-accent tracking-wide uppercase">
                        {result.class_name}
                      </div>

                      <div className="mt-4 flex items-center justify-center gap-6 text-xs font-mono text-text-secondary">
                        <div>
                          CONFIDENCE:{" "}
                          <span className="text-white font-bold">
                            {(result.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          LATENCY:{" "}
                          <span className="text-white font-bold">
                            {result.inference_time_ms.toFixed(1)} ms
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Top probabilities */}
                    {result.probabilities && (
                      <div className="space-y-3">
                        <div className="text-xs font-mono text-text-muted uppercase">
                          TOP CLASS PROBABILITIES
                        </div>
                        <div className="space-y-2">
                          {Object.entries(result.probabilities)
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 5)
                            .map(([cls, prob]) => (
                              <div key={cls} className="space-y-1">
                                <div className="flex justify-between text-xs font-mono">
                                  <span className="text-text-primary">{cls}</span>
                                  <span className="text-text-secondary">
                                    {(prob * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <div className="h-1.5 w-full rounded-full bg-surface-elevated overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${
                                      cls === result.class_name
                                        ? "bg-yellow-accent"
                                        : "bg-surface-border"
                                    }`}
                                    style={{ width: `${Math.min(100, prob * 100)}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
