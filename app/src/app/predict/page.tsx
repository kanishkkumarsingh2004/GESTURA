"use client";

import { useState, useCallback } from "react";
import { Image as LucideImage, X, Loader2 } from "lucide-react";
import { Card } from "@/components/card";
import { Button } from "@/components/button";
import { Badge } from "@/components/badge";
import { predictImage } from "@/lib/api";

type PredictionResult = {
  class_name: string;
  confidence: number;
  probabilities: Record<string, number>;
  inference_time_ms: number;
  stable: boolean;
  session_id: string;
};

export default function PredictPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
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
        setResult({
          class_name: data.class_name,
          confidence: data.confidence,
          probabilities: data.probabilities,
          inference_time_ms: data.inference_time_ms,
          stable: data.stable,
          session_id: data.session_id,
        });
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Prediction failed");
      } finally {
        setLoading(false);
      }
    },
    [file, sessionId]
  );

  return (
    <div className="min-h-screen bg-navy text-white">
      <nav className="sticky top-0 z-50 border-b border-slate-800 bg-navy/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 text-slate-300 hover:text-white">
            <span className="text-electric-blue">←</span>
            <span className="font-medium">Back</span>
          </a>
          <span className="font-bold text-lg tracking-tight">Predict</span>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload area */}
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">Upload Image</h2>
              <p className="text-sm text-slate-400">
                Upload a photo of a hand gesture. The model will classify it and
                return confidence scores.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <label className="block">
                  <span className="text-sm font-medium text-slate-300 mb-2 block">
                    Session ID (optional)
                  </span>
                  <input
                    type="text"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    placeholder="Auto-generated if left empty"
                    className="w-full bg-navy border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-electric-blue outline-none transition-colors"
                  />
                </label>
                <div
                  onClick={() => document.getElementById("file-input")?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    file
                      ? "border-electric-blue/50 bg-slate/50"
                      : "border-slate-700 hover:border-slate-500"
                  }`}
                >
                  {preview ? (
                    <>
                      <img src={preview} alt="Preview" className="mx-auto max-h-48 rounded-lg object-cover" />
                      <button
                        type="button"
                        onClick={removeFile}
                        className="mt-3 text-red-400 hover:text-red-300 text-sm"
                      >
                        <X className="w-4 h-4 inline mr-1" /> Remove
                      </button>
                    </>
                  ) : (
                    <>
                      <LucideImage className="w-12 h-12 mx-auto text-slate-500 mb-2" />
                      <p className="text-sm text-slate-400 mb-1">Click to upload</p>
                      <p className="text-xs text-slate-500">
                        PNG, JPG, WEBP (max 10 MB)
                      </p>
                      <input
                        id="file-input"
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </>
                  )}
                </div>
                <Button
                  type="submit"
                  disabled={!file || loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Classifying...
                    </>
                  ) : (
                    "Classify Gesture"
                  )}
                </Button>
              </form>
            </div>
          </Card>

          {/* Results */}
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">Result</h2>
              {error && (
                <div className="p-3 rounded-lg bg-red-900/20 border border-red-500/30 text-red-400 text-sm">
                  {error}
                </div>
              )}
              {!result && !loading && (
                <div className="h-32 flex items-center justify-center rounded-lg border border-dashed border-slate-700 text-slate-500 text-sm">
                  Prediction will appear here
                </div>
              )}
              {loading && (
                <div className="h-32 flex flex-col items-center justify-center gap-2">
                  <Loader2 className="w-8 h-8 animate-spin text-electric-blue" />
                  <span className="text-slate-400 text-sm">Classifying...</span>
                </div>
              )}
              {result && (
                <div className="space-y-4 pt-2">
                  <div className="flex items-center gap-3">
                    <Badge variant="success">
                      {result.stable ? "Stable" : "Unstable"}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      Session: {result.session_id.slice(0, 8)}…
                    </span>
                  </div>
                  <div className="text-3xl font-bold text-white">
                    {result.class_name}
                  </div>
                  <div className="text-lg text-electric-blue">
                    {Math.round(result.confidence * 100)}% confidence
                  </div>
                  <div className="text-xs text-slate-500 font-mono">
                    {result.inference_time_ms.toFixed(1)} ms inference
                  </div>
                  <div className="mt-4 border-t border-slate-700 pt-4">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      Class Probabilities
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(result.probabilities).map(
                        ([name, prob]) => (
                          <div key={name} className="flex items-center gap-3">
                            <span className="text-sm text-slate-300 w-20">
                              {name}
                            </span>
                            <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-electric-blue"
                                style={{ width: `${prob * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono text-slate-400 w-12 text-right">
                              {(prob * 100).toFixed(1)}%
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
