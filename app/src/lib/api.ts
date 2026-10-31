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

/* ------------------------------------------------------------------ */
/* Contributions (Community Dataset Pipeline)                         */
/* ------------------------------------------------------------------ */

export type FrameMetadata = {
  frame_id: string;
  filename: string;
  thumb_filename: string;
  timestamp_ms: number;
  frame_index: number;
  width: number;
  height: number;
  sharpness_score: number;
  is_blurry: boolean;
  is_duplicate: boolean;
  is_dark: boolean;
  status: "active" | "removed";
};

export type QualityReport = {
  total_frames_extracted: number;
  usable_frames_count: number;
  blurry_frames_count: number;
  duplicate_frames_count: number;
  dark_frames_count: number;
  warnings: string[];
};

export type ContributionMetadata = {
  contribution_id: string;
  status: "uploaded" | "extracted" | "pending_approval" | "approved" | "rejected";
  video_filename: string;
  video_duration_seconds: number;
  video_fps: number;
  video_resolution: [number, number];
  total_video_frames: number;
  country?: string;
  region?: string | null;
  state?: string | null;
  district_city?: string | null;
  sign_language_type?: string | null;
  variety_name?: string | null;
  gesture_name?: string | null;
  meaning?: string | null;
  sign_language?: string | null;
  category?: string | null;
  description?: string | null;
  gesture_type?: "static" | "dynamic" | "unknown" | null;
  contributor_id?: string | null;
  sample_interval: number;
  usable_frame_count: number;
  quality_report?: QualityReport | null;
  rejection_reason?: string | null;
  created_at: number;
  updated_at: number;
};

export type ContributionUploadResponse = {
  contribution_id: string;
  video_filename: string;
  duration_seconds: number;
  fps: number;
  resolution: [number, number];
  total_video_frames: number;
  status: string;
};

export type ExtractFramesResponse = {
  contribution_id: string;
  sample_interval: number;
  total_extracted: number;
  usable_count: number;
  quality_report: QualityReport;
  frames: FrameMetadata[];
};

export type FrameListResponse = {
  contribution_id: string;
  total_frames: number;
  active_frames: number;
  frames: FrameMetadata[];
};

export type SubmitContributionRequest = {
  country?: string;
  region: string;
  state: string;
  district_city?: string | null;
  sign_language_type: string;
  variety_name?: string | null;
  gesture_name: string;
  meaning: string;
  category: string;
  description?: string | null;
  gesture_type?: "static" | "dynamic" | "unknown";
  contributor_id?: string | null;
  sign_language?: string | null;
};

export type ContributionSummary = {
  contribution_id: string;
  country?: string | null;
  region?: string | null;
  state?: string | null;
  district_city?: string | null;
  sign_language_type?: string | null;
  variety_name?: string | null;
  gesture_name?: string | null;
  meaning?: string | null;
  sign_language?: string | null;
  category?: string | null;
  gesture_type?: string | null;
  video_duration_seconds: number;
  usable_frame_count: number;
  status: string;
  created_at: number;
};

export type ContributionListResponse = {
  count: number;
  contributions: ContributionSummary[];
};

export async function uploadContributionVideo(
  file: File
): Promise<ContributionUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/contributions/upload`, {
      method: "POST",
      body: formData,
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
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: string };
      detail = body.detail || "";
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Video upload failed: ${res.status}`);
  }
  return res.json();
}

export async function extractContributionFrames(
  contributionId: string,
  sampleInterval: number = 5,
  maxFrames: number = 40
): Promise<ExtractFramesResponse> {
  return request<ExtractFramesResponse>(
    `/contributions/${contributionId}/extract`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sample_interval: sampleInterval,
        max_frames: maxFrames,
      }),
    }
  );
}

export async function getContribution(
  contributionId: string
): Promise<ContributionMetadata> {
  return request<ContributionMetadata>(`/contributions/${contributionId}`);
}

export async function getContributionFrames(
  contributionId: string
): Promise<FrameListResponse> {
  return request<FrameListResponse>(`/contributions/${contributionId}/frames`);
}

export function getFrameImageUrl(
  contributionId: string,
  frameId: string,
  thumb: boolean = false
): string {
  return `${BASE_URL}/contributions/${contributionId}/frames/${frameId}${
    thumb ? "/thumb" : ""
  }`;
}

export async function deleteContributionFrame(
  contributionId: string,
  frameId: string
): Promise<{
  contribution_id: string;
  frame_id: string;
  status: string;
  usable_count: number;
}> {
  return request<{
    contribution_id: string;
    frame_id: string;
    status: string;
    usable_count: number;
  }>(`/contributions/${contributionId}/frames/${frameId}`, {
    method: "DELETE",
  });
}

export async function submitContribution(
  contributionId: string,
  data: SubmitContributionRequest
): Promise<ContributionMetadata> {
  return request<ContributionMetadata>(
    `/contributions/${contributionId}/submit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  );
}

export async function listContributions(
  status?: string,
  region?: string
): Promise<ContributionListResponse> {
  const params = new URLSearchParams();
  if (status && status !== "all") params.append("status", status);
  if (region && region !== "all") params.append("region", region);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request<ContributionListResponse>(`/contributions${query}`);
}

export async function reviewContribution(
  contributionId: string,
  approved: boolean,
  rejectionReason?: string
): Promise<ContributionMetadata> {
  return request<ContributionMetadata>(
    `/contributions/${contributionId}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        approved,
        rejection_reason: rejectionReason,
      }),
    }
  );
}
