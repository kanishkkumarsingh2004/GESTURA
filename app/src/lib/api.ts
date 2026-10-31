/**
 * API client for the Gesture Recognition FastAPI backend.
 *
 * All requests route through the Next.js rewrite (/api/:path* -> backend)
 * to avoid browser CORS restrictions, with the backend URL configured
 * strictly from environment variables.
 */

/**
 * Backend URL configured strictly from environment variables.
 * In Next.js, this is resolved from BACK_END_url, NEXT_PUBLIC_BACKEND_URL,
 * NEXT_PUBLIC_API_URL, or BACKEND_URL.
 */
export const BACKEND_URL = (
  process.env.BACK_END_url ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  ""
).replace(/\/+$/, "");

/**
 * Resolves the base URL for API requests.
 * In browser environments, requests default to '/api' (proxied by Next.js to BACKEND_URL)
 * to avoid CORS errors. On server-side execution (Node.js), requests use BACKEND_URL directly.
 */
export function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_DIRECT_API === "true" && BACKEND_URL) {
    return BACKEND_URL;
  }
  if (typeof window === "undefined" && BACKEND_URL) {
    return BACKEND_URL;
  }
  return "/api";
}

const BASE_URL = getBaseUrl();

const HEADERS: Record<string, string> = {
  Accept: "application/json",
};

async function request<T>(
  input: string,
  init?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${input}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { ...HEADERS, ...(init?.headers || {}) },
      ...init,
    });
  } catch (err) {
    if (!BACKEND_URL) {
      throw new Error(
        "Backend URL is not configured. Please set BACK_END_url in your .env file."
      );
    }
    throw err;
  }
  if (!res.ok) {
    if (res.status === 404 && !BACKEND_URL) {
      throw new Error(
        "Backend URL is not configured. Please set BACK_END_url in your .env file."
      );
    }
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail || "";
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export type GestureEntry = {
  class_id: number;
  class_name: string;
  text: string;
};

export type GesturesResponse = {
  classes: GestureEntry[];
  count: number;
};

export type ModelInfoResponse = {
  architecture: string;
  num_classes: number;
  class_names: string[];
  input_size: number[];
  device: string;
  loaded: boolean;
  metadata: Record<string, unknown>;
};

export type HealthResponse = {
  status: string;
  model_loaded: boolean;
  version: string;
};

export type AudioPlaybackInfo = {
  played: boolean;
  text?: string;
  gesture?: string;
  reason?: string;
};

export type StableEventInfo = {
  event_id: string;
  class_name: string;
  confidence: number;
  timestamp: number;
};

export type PredictResponse = {
  session_id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  probabilities: Record<string, number>;
  inference_time_ms: number;
  detection_enabled: boolean;
  audio_enabled: boolean;
  stable: boolean;
  stable_event: StableEventInfo | null;
  audio: AudioPlaybackInfo;
};

export type DetectionStatusResponse = {
  session_id: string;
  camera_connected: boolean;
  detection_enabled: boolean;
  audio_enabled: boolean;
  latest_prediction: string | null;
  latest_confidence: number | null;
  state: string;
  history_count: number;
};

export type AudioStatusResponse = {
  session_id: string;
  enabled: boolean;
  last_announced: string | null;
  queue_size: number;
};

export type HistoryResponse = {
  session_id: string;
  count: number;
  history: Array<{
    gesture: string;
    confidence: number;
    timestamp: number;
    audio_played: boolean;
  }>;
};

export type SessionControlResponse = {
  session_id: string;
  detection_enabled: boolean;
  camera_status: string;
};

export type AudioControlResponse = {
  session_id: string;
  audio_enabled: boolean;
};

export type GenericResponse = {
  session_id: string;
  status: string;
};

/* ------------------------------------------------------------------ */
/* Health                                                             */
/* ------------------------------------------------------------------ */

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

/* ------------------------------------------------------------------ */
/* Model                                                              */
/* ------------------------------------------------------------------ */

export async function getModelInfo(): Promise<ModelInfoResponse> {
  return request<ModelInfoResponse>("/model/info");
}

/* ------------------------------------------------------------------ */
/* Gestures                                                           */
/* ------------------------------------------------------------------ */

export async function getGestures(): Promise<GesturesResponse> {
  return request<GesturesResponse>("/gestures");
}

/* ------------------------------------------------------------------ */
/* Predict                                                            */
/* ------------------------------------------------------------------ */

export interface PredictOptions {
  file: File;
  sessionId?: string;
}

export async function predictImage({
  file,
  sessionId,
}: PredictOptions): Promise<PredictResponse> {
  const formData = new FormData();
  formData.append("image", file);
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/predict`, {
      method: "POST",
      body: formData,
      headers: {
        // Do not set Content-Type; the browser sets multipart boundary automatically.
        ...(sessionId ? { "X-Session-Id": sessionId } : {}),
      },
    });
  } catch (err) {
    if (!BACKEND_URL) {
      throw new Error(
        "Backend URL is not configured. Please set BACK_END_url in your .env file."
      );
    }
    throw err;
  }
  if (!res.ok) {
    if (res.status === 404 && !BACKEND_URL) {
      throw new Error(
        "Backend URL is not configured. Please set BACK_END_url in your .env file."
      );
    }
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail || "";
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Prediction failed: ${res.status}`);
  }
  return res.json();
}

/* ------------------------------------------------------------------ */
/* Session                                                            */
/* ------------------------------------------------------------------ */

export async function getSessionStatus(
  sessionId: string
): Promise<DetectionStatusResponse> {
  return request<DetectionStatusResponse>(`/session/${sessionId}/status`);
}

export async function startDetection(
  sessionId: string
): Promise<SessionControlResponse> {
  return request<SessionControlResponse>(
    `/session/${sessionId}/detection/start`,
    { method: "POST" }
  );
}

export async function stopDetection(
  sessionId: string
): Promise<SessionControlResponse> {
  return request<SessionControlResponse>(
    `/session/${sessionId}/detection/stop`,
    { method: "POST" }
  );
}

export async function enableAudio(
  sessionId: string
): Promise<AudioControlResponse> {
  return request<AudioControlResponse>(
    `/session/${sessionId}/audio/enable`,
    { method: "POST" }
  );
}

export async function disableAudio(
  sessionId: string
): Promise<AudioControlResponse> {
  return request<AudioControlResponse>(
    `/session/${sessionId}/audio/disable`,
    { method: "POST" }
  );
}

export async function getAudioStatus(
  sessionId: string
): Promise<AudioStatusResponse> {
  return request<AudioStatusResponse>(`/session/${sessionId}/audio/status`);
}

export async function getHistory(sessionId: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/session/${sessionId}/history`);
}

export async function clearHistory(
  sessionId: string
): Promise<GenericResponse> {
  return request<GenericResponse>(
    `/session/${sessionId}/history`,
    { method: "DELETE" }
  );
}

export async function resetSession(
  sessionId: string
): Promise<GenericResponse> {
  return request<GenericResponse>(
    `/session/${sessionId}/reset`,
    { method: "POST" }
  );
}

export async function removeSession(
  sessionId: string
): Promise<GenericResponse> {
  return request<GenericResponse>(
    `/session/${sessionId}`,
    { method: "DELETE" }
  );
}
