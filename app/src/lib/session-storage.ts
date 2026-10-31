export interface RecognizedGestureEvent {
  id: string;
  gesture: string;
  text: string;
  confidence: number;
  timestamp: number;
  inferenceTimeMs?: number;
  audioPlayed: boolean;
}

export interface RecognitionSession {
  id: string;
  title: string;
  startedAt: number;
  endedAt?: number;
  events: RecognizedGestureEvent[];
  transcript: string;
  source: "live_camera" | "image_upload" | "backend_sync";
}

const STORAGE_KEY = "gestura_session_history_v1";

export function getSavedSessions(): RecognitionSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveSession(session: RecognitionSession): void {
  if (typeof window === "undefined") return;
  try {
    const existing = getSavedSessions();
    const updated = [session, ...existing.filter((s) => s.id !== session.id)].slice(0, 50);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error("Failed to save session to storage:", err);
  }
}

export function deleteSession(sessionId: string): void {
  if (typeof window === "undefined") return;
  try {
    const existing = getSavedSessions();
    const filtered = existing.filter((s) => s.id !== sessionId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (err) {
    console.error("Failed to delete session:", err);
  }
}

export function clearAllSessions(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

