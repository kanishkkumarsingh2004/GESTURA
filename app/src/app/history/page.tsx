"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import {
  getSavedSessions,
  deleteSession,
  clearAllSessions,
  saveSession,
  type RecognitionSession,
} from "@/lib/session-storage";
import { speech } from "@/lib/speech";
import {
  Clock,
  Volume2,
  Trash2,
  Download,
  Search,
  Sparkles,
  Calendar,
  Layers,
  ArrowRight,
  Check,
} from "lucide-react";

// Initial realistic demo sessions to demonstrate the UI when the user has not recorded live camera yet
const DEFAULT_SAMPLE_SESSIONS: RecognitionSession[] = [
  {
    id: "session_sample_01",
    title: "Classroom Assistance Session",
    startedAt: Date.now() - 3600000 * 2,
    endedAt: Date.now() - 3600000 * 2 + 180000,
    transcript: "Hello Good Thank you",
    source: "live_camera",
    events: [
      {
        id: "evt_1",
        gesture: "HELLO",
        text: "Hello",
        confidence: 0.94,
        timestamp: Date.now() - 3600000 * 2 + 10000,
        audioPlayed: true,
      },
      {
        id: "evt_2",
        gesture: "GOOD",
        text: "Good",
        confidence: 0.91,
        timestamp: Date.now() - 3600000 * 2 + 65000,
        audioPlayed: true,
      },
      {
        id: "evt_3",
        gesture: "THANK_YOU",
        text: "Thank you",
        confidence: 0.89,
        timestamp: Date.now() - 3600000 * 2 + 140000,
        audioPlayed: true,
      },
    ],
  },
  {
    id: "session_sample_02",
    title: "Clinic Consultation Session",
    startedAt: Date.now() - 86400000,
    endedAt: Date.now() - 86400000 + 240000,
    transcript: "Please Help Yes",
    source: "live_camera",
    events: [
      {
        id: "evt_4",
        gesture: "PLEASE",
        text: "Please",
        confidence: 0.92,
        timestamp: Date.now() - 86400000 + 20000,
        audioPlayed: true,
      },
      {
        id: "evt_5",
        gesture: "HELP",
        text: "Help",
        confidence: 0.96,
        timestamp: Date.now() - 86400000 + 90000,
        audioPlayed: true,
      },
      {
        id: "evt_6",
        gesture: "YES",
        text: "Yes",
        confidence: 0.88,
        timestamp: Date.now() - 86400000 + 180000,
        audioPlayed: true,
      },
    ],
  },
];

export default function HistoryPage() {
  const [sessions, setSessions] = useState<RecognitionSession[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Load sessions on mount; inject sample sessions if empty so interface is immediately explorable
  useEffect(() => {
    const loaded = getSavedSessions();
    if (loaded.length === 0) {
      DEFAULT_SAMPLE_SESSIONS.forEach((s) => saveSession(s));
      setSessions(DEFAULT_SAMPLE_SESSIONS);
      setSelectedSessionId(DEFAULT_SAMPLE_SESSIONS[0].id);
    } else {
      setSessions(loaded);
      setSelectedSessionId(loaded[0].id);
    }
  }, []);

  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const q = searchQuery.toLowerCase();
    return sessions.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        s.transcript.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q)
    );
  }, [sessions, searchQuery]);

  const activeSession = useMemo(() => {
    return sessions.find((s) => s.id === selectedSessionId) || sessions[0] || null;
  }, [sessions, selectedSessionId]);

  // Statistics
  const totalGestures = useMemo(() => {
    return sessions.reduce((acc, s) => acc + s.events.length, 0);
  }, [sessions]);

  const avgConfidence = useMemo(() => {
    const allConf = sessions.flatMap((s) => s.events.map((e) => e.confidence));
    if (allConf.length === 0) return 0;
    return (allConf.reduce((a, b) => a + b, 0) / allConf.length) * 100;
  }, [sessions]);

  // Actions
  const handleDelete = (id: string) => {
    deleteSession(id);
    const updated = sessions.filter((s) => s.id !== id);
    setSessions(updated);
    if (selectedSessionId === id && updated.length > 0) {
      setSelectedSessionId(updated[0].id);
    }
  };

  const handleClearAll = () => {
    if (confirm("Are you sure you want to clear all stored history?")) {
      clearAllSessions();
      setSessions([]);
      setSelectedSessionId(null);
    }
  };

  const handleReplay = (text: string) => {
    speech.speak(text, true);
  };

  const handleExport = (session: RecognitionSession) => {
    const jsonStr = JSON.stringify(session, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gestura_${session.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyTranscript = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-heading text-3xl sm:text-4xl font-bold tracking-tight text-white">
                Session History & Logs
              </h1>
              <Badge variant="yellow" size="sm">
                PERSISTENT LOGS
              </Badge>
            </div>
            <p className="text-text-secondary text-sm mt-1 max-w-2xl">
              Review, export, and audition transcripts from previous live studio recognition sessions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {sessions.length > 0 && (
              <Button onClick={handleClearAll} variant="ghost" size="sm">
                <Trash2 className="w-4 h-4 mr-1.5 text-text-muted" />
                <span>Clear History</span>
              </Button>
            )}

            <Link
              href="/studio"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-yellow-accent text-black font-semibold text-xs tracking-wide hover:bg-yellow-hover shadow-sm transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>New Session</span>
            </Link>
          </div>
        </div>

        {/* Aggregate Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-surface-card border border-surface-border">
            <span className="text-[11px] font-mono text-text-muted uppercase">TOTAL SESSIONS</span>
            <div className="font-heading text-2xl font-bold text-white mt-1">
              {sessions.length}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-surface-card border border-surface-border">
            <span className="text-[11px] font-mono text-text-muted uppercase">GESTURES TRANSLATED</span>
            <div className="font-heading text-2xl font-bold text-yellow-accent mt-1">
              {totalGestures}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-surface-card border border-surface-border">
            <span className="text-[11px] font-mono text-text-muted uppercase">AVG CONFIDENCE</span>
            <div className="font-heading text-2xl font-bold text-white mt-1">
              {avgConfidence > 0 ? `${avgConfidence.toFixed(1)}%` : "—"}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-surface-card border border-surface-border">
            <span className="text-[11px] font-mono text-text-muted uppercase">STORAGE LOCATION</span>
            <div className="font-mono text-sm text-status-success mt-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
              <span>Local Secure Storage</span>
            </div>
          </div>
        </div>

        {/* History Master-Detail Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* SESSIONS LIST (Col 5) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Search box */}
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter sessions or words..."
                className="w-full pl-10 pr-4 py-2 rounded-xl bg-surface-card border border-surface-border text-white text-xs placeholder:text-text-muted focus:border-yellow-accent outline-none"
              />
            </div>

            {/* List */}
            {filteredSessions.length === 0 ? (
              <div className="py-12 text-center text-text-muted text-xs p-6 rounded-xl bg-surface-card border border-surface-border">
                No sessions match your search criteria.
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {filteredSessions.map((session) => {
                  const isSelected = session.id === activeSession?.id;
                  const isSample = session.id.startsWith("session_sample");

                  return (
                    <div
                      key={session.id}
                      onClick={() => setSelectedSessionId(session.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? "bg-surface-elevated border-yellow-accent/60 shadow-md"
                          : "bg-surface-card border-surface-border hover:border-yellow-accent/30"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="space-y-0.5">
                          <h4 className="font-heading text-sm font-bold text-white">
                            {session.title}
                          </h4>
                          <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted">
                            <Calendar className="w-3 h-3 text-text-muted" />
                            <span>
                              {new Date(session.startedAt).toLocaleDateString([], {
                                month: "short",
                                day: "numeric",
                              })}{" "}
                              •{" "}
                              {new Date(session.startedAt).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                        </div>

                        {isSample ? (
                          <Badge variant="yellow" size="sm">
                            SAMPLE
                          </Badge>
                        ) : (
                          <Badge variant="neutral" size="sm">
                            {session.events.length} GESTURES
                          </Badge>
                        )}
                      </div>

                      {/* Snippet */}
                      <p className="text-xs text-text-secondary line-clamp-1 italic">
                        &ldquo;{session.transcript || "No transcript recorded"}&rdquo;
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ACTIVE SESSION DETAILS (Col 7) */}
          <div className="lg:col-span-7">
            {activeSession ? (
              <Card className="bg-surface-card border-surface-border space-y-6">
                {/* Detail Header */}
                <div className="flex items-start justify-between pb-4 border-b border-surface-border">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-heading text-xl font-bold text-white">
                        {activeSession.title}
                      </h3>
                      {activeSession.id.startsWith("session_sample") && (
                        <span className="text-[10px] font-mono text-yellow-accent px-2 py-0.5 rounded bg-yellow-dim border border-yellow-accent/30">
                          VERIFIED DEMO
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono text-text-muted">
                      ID: {activeSession.id} • Started{" "}
                      {new Date(activeSession.startedAt).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Top action buttons */}
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleExport(activeSession)}
                      className="p-2 rounded-lg bg-surface-elevated hover:bg-yellow-accent hover:text-black border border-surface-border text-text-secondary transition-colors"
                      title="Download JSON export"
                    >
                      <Download className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleDelete(activeSession.id)}
                      className="p-2 rounded-lg bg-surface-elevated hover:bg-status-error/20 hover:text-status-error border border-surface-border text-text-secondary transition-colors"
                      title="Delete this session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Recognized Transcript Banner */}
                <div className="p-4 rounded-xl bg-surface-secondary border border-surface-border space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-text-muted uppercase">
                    <span>COMPLETE TRANSCRIPT</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleReplay(activeSession.transcript)}
                        className="inline-flex items-center gap-1 text-yellow-accent hover:underline"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Replay Speech</span>
                      </button>
                      <button
                        onClick={() =>
                          handleCopyTranscript(activeSession.id, activeSession.transcript)
                        }
                        className="inline-flex items-center gap-1 text-text-secondary hover:text-white ml-2"
                      >
                        {copiedId === activeSession.id ? (
                          <Check className="w-3.5 h-3.5 text-status-success" />
                        ) : (
                          <Clock className="w-3.5 h-3.5" />
                        )}
                        <span>{copiedId === activeSession.id ? "Copied!" : "Copy"}</span>
                      </button>
                    </div>
                  </div>

                  <p className="font-heading text-lg sm:text-xl font-semibold text-white tracking-wide">
                    &ldquo;{activeSession.transcript || "No words translated"}&rdquo;
                  </p>
                </div>

                {/* Event Stream Breakdown */}
                <div className="space-y-3">
                  <span className="text-xs font-mono text-text-muted uppercase tracking-wider block">
                    CHRONOLOGICAL GESTURE SEQUENCE ({activeSession.events.length})
                  </span>

                  <div className="space-y-2">
                    {activeSession.events.map((evt, idx) => (
                      <div
                        key={evt.id || idx}
                        className="p-3 rounded-lg bg-surface-secondary/70 border border-surface-border flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs text-yellow-accent font-bold">
                            #{idx + 1}
                          </span>
                          <div>
                            <span className="font-heading font-bold text-white text-sm">
                              {evt.gesture}
                            </span>
                            <span className="text-xs text-text-muted ml-2 font-mono">
                              &ldquo;{evt.text}&rdquo;
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-xs font-mono">
                          <span className="text-text-muted">
                            {new Date(evt.timestamp).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                          <span className="text-yellow-accent">
                            {(evt.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center p-12 text-center text-text-muted rounded-xl bg-surface-card border border-surface-border">
                Select a session from the list to view its full transcript and chronological gesture breakdown.
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

