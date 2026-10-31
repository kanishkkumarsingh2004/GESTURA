"use client";

import { useEffect, useState, useCallback } from "react";
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

function randomId() {
  return Math.random().toString(36).slice(2, 10);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleAction = useCallback(async (fn: () => Promise<any>) => {
    setError(null);
    try {
      await fn();
      await fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }, [fetchAll]);

  return (
    <div className="min-h-screen bg-navy text-white">
      <nav className="sticky top-0 z-50 border-b border-slate-800 bg-navy/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 text-slate-300 hover:text-white">
            <span className="text-electric-blue">←</span>
            <span className="font-medium">Back</span>
          </a>
          <span className="font-bold text-lg tracking-tight">Session</span>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">Session Management</h1>
          <div className="flex items-center gap-1">
            <span className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">
              {sessionId.slice(0, 8)}…
            </span>
            <button
              onClick={() => setSessionId(randomId())}
              className="text-xs text-slate-400 hover:text-white underline"
            >
              New session
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-900/20 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Status cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <div className="space-y-2">
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Detection</dt>
              <dd className="flex items-center gap-2">
                <Badge
                  variant={status?.detection_enabled ? "success" : "default"}
                >
                  {status?.detection_enabled ? "Enabled" : "Disabled"}
                </Badge>
              </dd>
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">Camera</dt>
              <dd className="text-white font-mono">
                {status?.camera_connected ? "Connected" : "Disconnected"}
              </dd>
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">State</dt>
              <dd className="text-white font-mono text-sm">{status?.state ?? "—"}</dd>
            </div>
          </Card>
          <Card>
            <div className="space-y-2">
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Audio</dt>
              <dd className="flex items-center gap-2">
                <Badge variant={audio?.enabled ? "success" : "default"}>
                  {audio?.enabled ? "Enabled" : "Disabled"}
                </Badge>
              </dd>
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">Last Announced</dt>
              <dd className="text-white font-mono text-sm">{audio?.last_announced ?? "—"}</dd>
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">Queue</dt>
              <dd className="text-white font-mono text-sm">{audio?.queue_size ?? 0}</dd>
            </div>
          </Card>
          <Card>
            <div className="space-y-2">
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Latest Prediction</dt>
              <dd className="text-white font-mono text-lg">
                {status?.latest_prediction ?? "—"}
              </dd>
              <dt className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">Confidence</dt>
              <dd className="text-electric-blue font-mono text-sm">
                {status?.latest_confidence != null
                  ? (status.latest_confidence * 100).toFixed(1) + "%"
                  : "—"}
              </dd>
            </div>
          </Card>
        </div>

        {/* Controls */}
        <Card>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <Button
                onClick={() =>
                  handleAction(() =>
                    status?.detection_enabled
                      ? stopDetection(sessionId)
                      : startDetection(sessionId)
                  )
                }
              >
                {status?.detection_enabled ? "Stop Detection" : "Start Detection"}
              </Button>
              <Button
                onClick={() =>
                  handleAction(() =>
                    audio?.enabled ? disableAudio(sessionId) : enableAudio(sessionId)
                  )
                }
                variant="outline"
              >
                {audio?.enabled ? "Disable Audio" : "Enable Audio"}
              </Button>
            </div>
          </div>
        </Card>

        {/* History */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Prediction History</h2>
              <p className="text-sm text-slate-400">
                {history.length} entries in this session
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => handleAction(() => clearHistory(sessionId))}
                disabled={history.length === 0}
              >
                Clear History
              </Button>
              <Button variant="outline" onClick={() => handleAction(() => resetSession(sessionId))}>
                Reset Session
              </Button>
            </div>
          </div>

          {history.length === 0 ? (
            <div className="h-32 flex flex-col items-center justify-center text-slate-500">
              No predictions yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="pb-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Gesture</th>
                    <th className="pb-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Confidence</th>
                    <th className="pb-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Time</th>
                    <th className="pb-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Audio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {history.map((entry, i) => (
                    <tr key={i} className="hover:bg-slate/30 transition-colors">
                      <td className="py-3 text-white font-mono">{entry.gesture}</td>
                      <td className="py-3 text-electric-blue font-mono">
                        {(entry.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 text-xs text-slate-500 font-mono">
                        {new Date(entry.timestamp * 1000).toLocaleTimeString()}
                      </td>
                      <td className="py-3">
                        <Badge variant={entry.audio_played ? "success" : "default"}>
                          {entry.audio_played ? "Played" : "—"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <div className="flex items-center gap-3 mt-4">
          <Button
            variant="danger"
            onClick={() =>
              handleAction(() => removeSession(sessionId))
            }
          >
            Remove Session
          </Button>
        </div>
      </main>
    </div>
  );
}
