"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Button } from "@/components/button";
import { Badge } from "@/components/badge";
import {
  getSessionStatus,
  startDetection,
  stopDetection,
  enableAudio,
  disableAudio,
  getAudioStatus,
  getHistory,
  clearHistory,
  resetSession,
  removeSession,
  type DetectionStatusResponse,
  type AudioStatusResponse,
} from "@/lib/api";
import { Sparkles, RefreshCw, AlertCircle, ArrowRight } from "lucide-react";

function randomId() {
  return "session_" + Math.random().toString(36).slice(2, 8);
}

export default function SessionPage() {
  const [sessionId, setSessionId] = useState(randomId());
  const [status, setStatus] = useState<DetectionStatusResponse | null>(null);
  const [audio, setAudio] = useState<AudioStatusResponse | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, a, h] = await Promise.all([
        getSessionStatus(sessionId),
        getAudioStatus(sessionId),
        getHistory(sessionId),
      ]);
      setStatus(s);
      setAudio(a);
      setHistory(h.history);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect to backend session state. Ensure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleAction = useCallback(
    async (fn: () => Promise<any>) => {
      setError(null);
      try {
        await fn();
        await fetchAll();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Action failed");
      }
    },
    [fetchAll]
  );

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
          <div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Backend Session Diagnostics
            </h1>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Low-level REST coordinator for per-session detection queues and stabilization resets.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/studio"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-yellow-accent text-black font-semibold text-xs"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Open Studio</span>
            </Link>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-center gap-3">
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-card border border-surface-border text-white text-xs font-mono w-64"
          />
          <Button onClick={() => setSessionId(randomId())} variant="secondary" size="sm">
            Generate New ID
          </Button>
          <Button onClick={fetchAll} variant="secondary" size="sm" isLoading={loading}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-surface-card border-surface-border space-y-4">
            <h3 className="font-heading text-base font-bold text-white pb-2 border-b border-surface-border">
              Detection Controls
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-text-muted">Detection Status:</span>
                <span className="text-white">{status?.detection_enabled ? "ACTIVE" : "INACTIVE"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Camera Stream:</span>
                <span className="text-white">{status?.state ?? "DISCONNECTED"}</span>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                onClick={() => handleAction(() => startDetection(sessionId))}
                variant="primary"
                size="sm"
              >
                Start Detection
              </Button>
              <Button
                onClick={() => handleAction(() => stopDetection(sessionId))}
                variant="secondary"
                size="sm"
              >
                Stop Detection
              </Button>
            </div>
          </Card>

          <Card className="bg-surface-card border-surface-border space-y-4">
            <h3 className="font-heading text-base font-bold text-white pb-2 border-b border-surface-border">
              Audio Queue Controls
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-text-muted">Audio Synthesis:</span>
                <span className="text-white">{audio?.enabled ? "ENABLED" : "DISABLED"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Queue Size:</span>
                <span className="text-white">{audio?.queue_size ?? 0}</span>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                onClick={() => handleAction(() => enableAudio(sessionId))}
                variant="primary"
                size="sm"
              >
                Enable Audio
              </Button>
              <Button
                onClick={() => handleAction(() => disableAudio(sessionId))}
                variant="secondary"
                size="sm"
              >
                Disable Audio
              </Button>
            </div>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}
