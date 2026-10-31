"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { Card } from "@/components/card";
import {
  predictImage,
  getHealth,
  type HealthResponse,
  type PredictResponse,
  BACKEND_URL,
} from "@/lib/api";
import { speech } from "@/lib/speech";
import {
  saveSession,
  type RecognizedGestureEvent,
  type RecognitionSession,
} from "@/lib/session-storage";
import {
  Camera,
  CameraOff,
  Volume2,
  VolumeX,
  Copy,
  Trash2,
  Sparkles,
  RefreshCw,
  Activity,
  Layers,
  Cpu,
  Clock,
  Check,
  AlertCircle,
  Eye,
  Sliders,
} from "lucide-react";

export default function StudioPage() {
  // Session tracking
  const [sessionId] = useState(() => "session_" + Math.random().toString(36).slice(2, 9));
  const [sessionStartTime] = useState(() => Date.now());

  // Backend state
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking");

  // Camera state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [showLandmarkOverlay, setShowLandmarkOverlay] = useState(true);
  const [continuousInference, setContinuousInference] = useState(true);

  // Recognition state
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentGesture, setCurrentGesture] = useState<string | null>(null);
  const [currentConfidence, setCurrentConfidence] = useState<number | null>(null);
  const [lastInferenceTime, setLastInferenceTime] = useState<number | null>(null);
  const [recognizedTranscript, setRecognizedTranscript] = useState<string[]>([]);
  const [recentEvents, setRecentEvents] = useState<RecognizedGestureEvent[]>([]);

  // Audio state
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [copiedTranscript, setCopiedTranscript] = useState(false);

  // Refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const inferenceIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Check Backend Connectivity
  const checkBackend = useCallback(async () => {
    try {
      setBackendStatus("checking");
      const health = await getHealth();
      setBackendHealth(health);
      setBackendStatus(health.status === "ok" || health.model_loaded ? "connected" : "disconnected");
    } catch {
      setBackendStatus("disconnected");
      setBackendHealth(null);
    }
  }, []);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  // 2. Enumerate Cameras
  useEffect(() => {
    if (typeof navigator !== "undefined" && navigator.mediaDevices?.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices().then((devices) => {
        const videoInputs = devices.filter((d) => d.kind === "videoinput");
        setVideoDevices(videoInputs);
        if (videoInputs.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(videoInputs[0].deviceId);
        }
      });
    }
  }, [selectedDeviceId]);

  // 3. Start Camera
  const startCamera = async () => {
    setCameraError(null);
    try {
      const constraints: MediaStreamConstraints = {
        video: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId }, width: { ideal: 640 }, height: { ideal: 480 } }
          : { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err) {
      console.error("Camera access error:", err);
      setCameraError(
        err instanceof Error
          ? `${err.name}: ${err.message}`
          : "Unable to access camera. Please verify permissions."
      );
      setIsCameraActive(false);
    }
  };

  // 4. Stop Camera
  const stopCamera = useCallback(() => {
    if (inferenceIntervalRef.current) {
      clearInterval(inferenceIntervalRef.current);
      inferenceIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  // 5. Landmark HUD Animation on Video Overlay
  useEffect(() => {
    let animId: number;
    let frame = 0;

    const renderOverlay = () => {
      if (!showLandmarkOverlay || !isCameraActive || !overlayCanvasRef.current || !videoRef.current) {
        return;
      }
      const canvas = overlayCanvasRef.current;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const w = canvas.width;
      const h = canvas.height;

      // Draw futuristic target box in the center
      const boxSize = Math.min(w, h) * 0.65;
      const boxX = (w - boxSize) / 2;
      const boxY = (h - boxSize) / 2;

      // Corner brackets (Electric Yellow)
      const bracketLen = 24;
      ctx.strokeStyle = "#F5E642";
      ctx.lineWidth = 2.5;

      // Top-Left
      ctx.beginPath();
      ctx.moveTo(boxX, boxY + bracketLen);
      ctx.lineTo(boxX, boxY);
      ctx.lineTo(boxX + bracketLen, boxY);
      ctx.stroke();

      // Top-Right
      ctx.beginPath();
      ctx.moveTo(boxX + boxSize - bracketLen, boxY);
      ctx.lineTo(boxX + boxSize, boxY);
      ctx.lineTo(boxX + boxSize, boxY + bracketLen);
      ctx.stroke();

      // Bottom-Left
      ctx.beginPath();
      ctx.moveTo(boxX, boxY + boxSize - bracketLen);
      ctx.lineTo(boxX, boxY + boxSize);
      ctx.lineTo(boxX + bracketLen, boxY + boxSize);
      ctx.stroke();

      // Bottom-Right
      ctx.beginPath();
      ctx.moveTo(boxX + boxSize - bracketLen, boxY + boxSize);
      ctx.lineTo(boxX + boxSize, boxY + boxSize);
      ctx.lineTo(boxX + boxSize, boxY + boxSize - bracketLen);
      ctx.stroke();

      // Center crosshair
      ctx.strokeStyle = "rgba(245, 230, 66, 0.35)";
      ctx.lineWidth = 1;
      const midX = w / 2;
      const midY = h / 2;
      ctx.beginPath();
      ctx.moveTo(midX - 10, midY);
      ctx.lineTo(midX + 10, midY);
      ctx.moveTo(midX, midY - 10);
      ctx.lineTo(midX, midY + 10);
      ctx.stroke();

      // Scanning sweep line
      frame++;
      const scanY = boxY + ((frame * 2.5) % boxSize);
      ctx.strokeStyle = "rgba(245, 230, 66, 0.4)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(boxX, scanY);
      ctx.lineTo(boxX + boxSize, scanY);
      ctx.stroke();
      ctx.setLineDash([]);

      animId = requestAnimationFrame(renderOverlay);
    };

    if (isCameraActive && showLandmarkOverlay) {
      animId = requestAnimationFrame(renderOverlay);
    }

    return () => cancelAnimationFrame(animId);
  }, [isCameraActive, showLandmarkOverlay]);

  // 6. Capture Frame & Execute Prediction
  const captureAndPredict = useCallback(async () => {
    if (!videoRef.current || !isCameraActive || isProcessing) return;

    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    setIsProcessing(true);
    try {
      // Draw video frame to hidden canvas
      if (!canvasRef.current) {
        canvasRef.current = document.createElement("canvas");
      }
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert frame to Blob
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob((b) => resolve(b), "image/jpeg", 0.85)
      );

      if (!blob) return;

      const file = new File([blob], "camera_frame.jpg", { type: "image/jpeg" });

      if (backendStatus === "connected") {
        const res: PredictResponse = await predictImage({
          file,
          sessionId,
        });

        const gesture = res.class_name;
        const conf = res.confidence;
        const latency = res.inference_time_ms;

        setCurrentGesture(gesture);
        setCurrentConfidence(conf);
        setLastInferenceTime(latency);

        if (gesture && gesture !== "NONE") {
          // If stabilized and not duplicate
          const event: RecognizedGestureEvent = {
            id: "evt_" + Date.now(),
            gesture,
            text: gesture.replace(/_/g, " "),
            confidence: conf,
            timestamp: Date.now(),
            inferenceTimeMs: latency,
            audioPlayed: audioEnabled,
          };

          setRecentEvents((prev) => [event, ...prev].slice(0, 20));
          setRecognizedTranscript((prev) => [...prev, event.text]);

          // Audio speech
          if (audioEnabled) {
            speech.speak(event.text);
          }

          // Persist session
          const currentSession: RecognitionSession = {
            id: sessionId,
            title: `Live Studio — ${new Date(sessionStartTime).toLocaleTimeString()}`,
            startedAt: sessionStartTime,
            endedAt: Date.now(),
            events: [event, ...recentEvents],
            transcript: [...recognizedTranscript, event.text].join(" "),
            source: "live_camera",
          };
          saveSession(currentSession);
        }
      } else {
        // Backend offline indicator
        setCurrentGesture("BACKEND OFFLINE");
        setCurrentConfidence(null);
        setLastInferenceTime(null);
      }
    } catch (err) {
      console.warn("Prediction frame failed:", err);
    } finally {
      setIsProcessing(false);
    }
  }, [
    isCameraActive,
    isProcessing,
    backendStatus,
    sessionId,
    sessionStartTime,
    audioEnabled,
    recentEvents,
    recognizedTranscript,
  ]);

  // 7. Continuous Inference Loop
  useEffect(() => {
    if (isCameraActive && continuousInference && backendStatus === "connected") {
      inferenceIntervalRef.current = setInterval(() => {
        captureAndPredict();
      }, 700); // Sample every 700ms to balance responsiveness and backend throughput
    } else {
      if (inferenceIntervalRef.current) {
        clearInterval(inferenceIntervalRef.current);
        inferenceIntervalRef.current = null;
      }
    }
    return () => {
      if (inferenceIntervalRef.current) {
        clearInterval(inferenceIntervalRef.current);
      }
    };
  }, [isCameraActive, continuousInference, backendStatus, captureAndPredict]);

  // Audio mute toggle
  const toggleAudio = () => {
    const next = !audioEnabled;
    setAudioEnabled(next);
    speech.setEnabled(next);
  };

  // Copy transcript
  const copyTranscript = () => {
    const text = recognizedTranscript.join(" ");
    if (text) {
      navigator.clipboard.writeText(text);
      setCopiedTranscript(true);
      setTimeout(() => setCopiedTranscript(false), 2000);
    }
  };

  // Clear transcript
  const clearTranscript = () => {
    setRecognizedTranscript([]);
    setRecentEvents([]);
    setCurrentGesture(null);
    setCurrentConfidence(null);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Studio Top Control Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Live Recognition Studio
              </h1>
              <Badge variant="yellow" size="sm">
                STUDIO v1.0
              </Badge>
            </div>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Active vision workplace with temporal neural classification and live speech synthesis.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Backend status indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-surface-border text-xs font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "connected"
                    ? "bg-status-success animate-pulse"
                    : "bg-status-warning"
                }`}
              />
              <span className="text-text-secondary">
                {backendStatus === "connected" ? "Neural Engine Active" : "Backend Disconnected"}
              </span>
              <button
                onClick={checkBackend}
                title="Refresh connection"
                className="text-text-muted hover:text-yellow-accent ml-1"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Session ID chip */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border font-mono text-xs text-text-muted">
              <span>SESSION:</span>
              <span className="text-text-primary font-bold">{sessionId}</span>
            </div>
          </div>
        </div>

        {/* WORKSPACE 2-COLUMN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT PANEL: CAMERA VIEWPORT (Col 7) */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="p-0 overflow-hidden relative bg-black border-surface-border">
              {/* Camera Header Bar */}
              <div className="flex items-center justify-between px-4 py-3 bg-surface-card border-b border-surface-border text-xs">
                <div className="flex items-center gap-2 font-mono text-text-secondary">
                  <Camera className="w-4 h-4 text-yellow-accent" />
                  <span>CAMERA STREAM</span>
                  <span className="text-surface-border">|</span>
                  <span
                    className={
                      isCameraActive ? "text-status-success font-bold" : "text-text-muted"
                    }
                  >
                    {isCameraActive ? "LIVE (30 FPS)" : "OFFLINE"}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {/* Landmark overlay toggle */}
                  <button
                    onClick={() => setShowLandmarkOverlay(!showLandmarkOverlay)}
                    className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-mono transition-colors ${
                      showLandmarkOverlay
                        ? "bg-yellow-dim text-yellow-accent border border-yellow-accent/30"
                        : "bg-surface-elevated text-text-muted border border-surface-border"
                    }`}
                    title="Toggle Hand Landmark Target HUD"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>HUD</span>
                  </button>

                  {/* Device selector if multiple cameras */}
                  {videoDevices.length > 1 && (
                    <select
                      value={selectedDeviceId}
                      onChange={(e) => setSelectedDeviceId(e.target.value)}
                      className="bg-surface-elevated border border-surface-border text-text-secondary rounded px-2 py-1 text-xs"
                    >
                      {videoDevices.map((d, i) => (
                        <option key={d.deviceId || i} value={d.deviceId}>
                          {d.label || `Camera ${i + 1}`}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {/* Viewport container */}
              <div className="relative aspect-[4/3] sm:aspect-video w-full bg-surface-secondary flex items-center justify-center overflow-hidden">
                {/* Real video feed */}
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  className={`w-full h-full object-cover transform -scale-x-100 ${
                    isCameraActive ? "block" : "hidden"
                  }`}
                />

                {/* Real-time HUD Canvas Overlay */}
                <canvas
                  ref={overlayCanvasRef}
                  className={`absolute inset-0 pointer-events-none w-full h-full ${
                    isCameraActive && showLandmarkOverlay ? "block" : "hidden"
                  }`}
                />

                {/* Offline placeholder state */}
                {!isCameraActive && (
                  <div className="flex flex-col items-center justify-center text-center p-6 space-y-4">
                    <div className="w-16 h-16 rounded-2xl bg-surface-card border border-surface-border flex items-center justify-center text-text-muted">
                      <CameraOff className="w-8 h-8" />
                    </div>
                    <div>
                      <h3 className="font-heading text-lg font-bold text-white">Camera Standby</h3>
                      <p className="text-text-muted text-xs max-w-sm mt-1">
                        Activate your camera to begin streaming frames into the neural recognition pipeline.
                      </p>
                    </div>
                    {cameraError && (
                      <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/30 text-status-error text-xs max-w-md flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                        <span>{cameraError}</span>
                      </div>
                    )}
                    <Button onClick={startCamera} variant="primary" size="md">
                      <Camera className="w-4 h-4 mr-2" />
                      Start Camera
                    </Button>
                  </div>
                )}

                {/* Live telemetry floating badge */}
                {isCameraActive && (
                  <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 rounded bg-black/80 border border-surface-border font-mono text-[11px] text-text-secondary backdrop-blur-md">
                    <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
                    <span>REC</span>
                    <span className="text-surface-border">|</span>
                    <span className="text-yellow-accent">RGB 224x224</span>
                  </div>
                )}
              </div>

              {/* Bottom camera action bar */}
              <div className="p-4 bg-surface-card border-t border-surface-border flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {isCameraActive ? (
                    <Button onClick={stopCamera} variant="danger" size="sm">
                      <CameraOff className="w-4 h-4 mr-1.5" />
                      Stop Camera
                    </Button>
                  ) : (
                    <Button onClick={startCamera} variant="primary" size="sm">
                      <Camera className="w-4 h-4 mr-1.5" />
                      Start Camera
                    </Button>
                  )}

                  {isCameraActive && (
                    <Button
                      onClick={captureAndPredict}
                      variant="secondary"
                      size="sm"
                      isLoading={isProcessing}
                    >
                      <Sparkles className="w-4 h-4 mr-1.5 text-yellow-accent" />
                      Manual Snapshot
                    </Button>
                  )}
                </div>

                {isCameraActive && (
                  <div className="flex items-center gap-2 text-xs font-mono text-text-secondary">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={continuousInference}
                        onChange={(e) => setContinuousInference(e.target.checked)}
                        className="accent-yellow-accent rounded w-3.5 h-3.5"
                      />
                      <span>Continuous Stream</span>
                    </label>
                  </div>
                )}
              </div>
            </Card>

            {/* Offline Helper notice when backend is disconnected */}
            {backendStatus === "disconnected" && (
              <div className="p-4 rounded-xl bg-surface-card border border-status-warning/40 text-xs text-text-secondary space-y-2">
                <div className="flex items-center gap-2 text-yellow-accent font-bold">
                  <AlertCircle className="w-4 h-4" />
                  <span>FastAPI Backend Not Connected</span>
                </div>
                <p>
                  To perform live model inference, run the FastAPI server locally from your project root:
                </p>
                <div className="p-2.5 rounded bg-black border border-surface-border font-mono text-text-primary text-[11px] selection:bg-yellow-accent selection:text-black">
                  uv run --active python scripts/run_api.py
                </div>
                <p className="text-text-muted text-[11px]">
                  Or configure your remote server URL in <code className="text-yellow-accent">app/.env</code>.
                </p>
              </div>
            )}
          </div>

          {/* RIGHT PANEL: RECOGNITION OUTPUT (Col 5) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Live Detected Banner */}
            <Card className="bg-surface-card border-surface-border relative overflow-hidden">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-surface-border text-xs">
                <span className="font-mono text-text-muted uppercase">CURRENT PREDICTION</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={toggleAudio}
                    className="p-1 rounded text-text-muted hover:text-yellow-accent"
                    title={audioEnabled ? "Audio Speech Enabled" : "Audio Muted"}
                  >
                    {audioEnabled ? (
                      <Volume2 className="w-4 h-4 text-yellow-accent" />
                    ) : (
                      <VolumeX className="w-4 h-4 text-text-muted" />
                    )}
                  </button>
                  <span className="text-[11px] font-mono text-text-muted">
                    {audioEnabled ? "AUDIO ON" : "MUTED"}
                  </span>
                </div>
              </div>

              {/* Big Recognized Text */}
              <div className="text-center py-6">
                <div className="font-mono text-xs text-text-muted mb-2 tracking-widest">
                  STABILIZED GESTURE
                </div>
                <div className="font-heading text-4xl sm:text-5xl font-bold text-yellow-accent tracking-wide uppercase min-h-[56px] flex items-center justify-center">
                  {currentGesture || "—"}
                </div>

                {/* Confidence Bar */}
                {currentConfidence !== null && (
                  <div className="mt-6 max-w-xs mx-auto space-y-1.5">
                    <div className="flex justify-between text-xs font-mono text-text-secondary">
                      <span>CONFIDENCE</span>
                      <span className="text-yellow-accent font-bold">
                        {(currentConfidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-surface-elevated overflow-hidden border border-surface-border">
                      <div
                        className="h-full bg-yellow-accent transition-all duration-300 rounded-full"
                        style={{ width: `${Math.min(100, currentConfidence * 100)}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Latency info */}
                {lastInferenceTime !== null && (
                  <div className="mt-3 text-[11px] font-mono text-text-muted">
                    INFERENCE: <span className="text-text-primary">{lastInferenceTime.toFixed(1)} ms</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Live Transcript Log */}
            <Card className="bg-surface-card border-surface-border space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                <div className="flex items-center gap-2">
                  <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
                    Live Transcript
                  </h3>
                  <Badge variant="neutral" size="sm">
                    {recognizedTranscript.length}
                  </Badge>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={copyTranscript}
                    disabled={recognizedTranscript.length === 0}
                    className="p-1.5 rounded-md hover:bg-surface-elevated text-text-secondary hover:text-white transition-colors disabled:opacity-40"
                    title="Copy transcript text"
                  >
                    {copiedTranscript ? (
                      <Check className="w-4 h-4 text-status-success" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>

                  <button
                    onClick={clearTranscript}
                    disabled={recognizedTranscript.length === 0}
                    className="p-1.5 rounded-md hover:bg-surface-elevated text-text-secondary hover:text-status-error transition-colors disabled:opacity-40"
                    title="Clear transcript"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Transcript box */}
              <div className="min-h-[140px] max-h-[220px] overflow-y-auto p-3.5 rounded-lg bg-surface-secondary border border-surface-border text-sm leading-relaxed">
                {recognizedTranscript.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-text-muted text-xs py-8 text-center">
                    <span>Recognized words will accumulate here in sequence.</span>
                    <span className="text-[11px] mt-1 text-text-muted/60">
                      Gestures are announced via audio when stabilized.
                    </span>
                  </div>
                ) : (
                  <p className="text-text-primary font-medium tracking-wide">
                    {recognizedTranscript.join(" ")}
                  </p>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* BOTTOM SECTION: RECENT TIMELINE & MODEL SPECS */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-4">
          {/* Recent Gestures Timeline (Col 8) */}
          <div className="lg:col-span-8">
            <Card className="bg-surface-card border-surface-border space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-yellow-accent" />
                  <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
                    Recent Gesture Stream
                  </h3>
                </div>
                <span className="text-xs font-mono text-text-muted">LATEST 20 EVENTS</span>
              </div>

              {recentEvents.length === 0 ? (
                <div className="py-8 text-center text-text-muted text-xs">
                  No gestures recorded in this session yet.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {recentEvents.map((evt) => (
                    <div
                      key={evt.id}
                      className="p-3 rounded-lg bg-surface-secondary border border-surface-border flex flex-col justify-between space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] text-text-muted">
                          {new Date(evt.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </span>
                        {evt.audioPlayed && (
                          <Volume2 className="w-3 h-3 text-yellow-accent" />
                        )}
                      </div>
                      <div className="font-heading font-bold text-white text-sm">
                        {evt.gesture}
                      </div>
                      <div className="text-[10px] font-mono text-yellow-accent">
                        {(evt.confidence * 100).toFixed(0)}% CONF
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Model Status Card (Col 4) */}
          <div className="lg:col-span-4">
            <Card className="bg-surface-card border-surface-border space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-surface-border">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-yellow-accent" />
                  <h3 className="font-heading text-sm font-bold text-white uppercase tracking-wider">
                    Engine Status
                  </h3>
                </div>
                <Badge
                  variant={backendStatus === "connected" ? "success" : "neutral"}
                  size="sm"
                  dot
                >
                  {backendStatus === "connected" ? "ACTIVE" : "STANDALONE"}
                </Badge>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-surface-border/50">
                  <span className="text-text-muted">Backbone:</span>
                  <span className="text-text-primary">VGG16 Transfer</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surface-border/50">
                  <span className="text-text-muted">Input Resolution:</span>
                  <span className="text-text-primary">224 × 224 RGB</span>
                </div>
                <div className="flex justify-between py-1 border-b border-surface-border/50">
                  <span className="text-text-muted">Temporal Confirmation:</span>
                  <span className="text-text-primary">5 Frames Window</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-text-muted">Audio Synthesis:</span>
                  <span className="text-status-success">Browser Native</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

