"use client";

import { useState, useEffect, useRef, useMemo, ChangeEvent, DragEvent } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import {
  uploadContributionVideo,
  extractContributionFrames,
  getContribution,
  getContributionFrames,
  deleteContributionFrame,
  submitContribution,
  listContributions,
  reviewContribution,
  getFrameImageUrl,
  type ContributionMetadata,
  type FrameMetadata,
  type QualityReport,
  type ContributionSummary,
} from "@/lib/api";
import {
  UploadCloud,
  FileVideo,
  Film,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Trash2,
  ZoomIn,
  Send,
  Layers,
  ArrowRight,
  RefreshCw,
  Eye,
  Sliders,
  Info,
  ShieldCheck,
  Tag,
  BookOpen,
} from "lucide-react";

const POPULAR_LANGUAGES = [
  { code: "ISL", label: "Indian Sign Language (ISL)" },
  { code: "ASL", label: "American Sign Language (ASL)" },
  { code: "BSL", label: "British Sign Language (BSL)" },
  { code: "Auslan", label: "Australian Sign Language" },
  { code: "Other", label: "Other / Custom" },
];

const POPULAR_CATEGORIES = [
  "Greetings",
  "Survival & Emergency",
  "Common Phrases",
  "Alphabet & Numbers",
  "Emotions & Sentiments",
  "Custom",
];

export default function ContributePage() {
  const [activeTab, setActiveTab] = useState<"contribute" | "browse">("contribute");

  // Step 1: Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Active contribution pipeline state
  const [contributionId, setContributionId] = useState<string | null>(null);
  const [contributionMeta, setContributionMeta] = useState<ContributionMetadata | null>(null);

  // Step 2: Extraction state
  const [sampleInterval, setSampleInterval] = useState<number>(5);
  const [maxFrames, setMaxFrames] = useState<number>(40);
  const [isExtracting, setIsExtracting] = useState(false);
  const [frames, setFrames] = useState<FrameMetadata[]>([]);
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [inspectingFrame, setInspectingFrame] = useState<FrameMetadata | null>(null);

  // Step 3: Gesture Metadata form
  const [gestureName, setGestureName] = useState("");
  const [meaning, setMeaning] = useState("");
  const [signLanguage, setSignLanguage] = useState("ISL");
  const [customLanguage, setCustomLanguage] = useState("");
  const [category, setCategory] = useState("Greetings");
  const [customCategory, setCustomCategory] = useState("");
  const [gestureType, setGestureType] = useState<"static" | "dynamic">("dynamic");
  const [description, setDescription] = useState("");
  const [contributorId, setContributorId] = useState("");

  // Step 4: Submission lifecycle
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionComplete, setSubmissionComplete] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Browse submissions state
  const [communitySubmissions, setCommunitySubmissions] = useState<ContributionSummary[]>([]);
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [activeReviewItem, setActiveReviewItem] = useState<ContributionMetadata | null>(null);
  const [isModerating, setIsModerating] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cleanup object URLs on unmount
  useEffect(() => {
    return () => {
      if (videoPreviewUrl) {
        URL.revokeObjectURL(videoPreviewUrl);
      }
    };
  }, [videoPreviewUrl]);

  // Load submissions list when browsing tab is active
  useEffect(() => {
    if (activeTab === "browse") {
      fetchSubmissions();
    }
  }, [activeTab, statusFilter]);

  const fetchSubmissions = async () => {
    setIsLoadingSubmissions(true);
    try {
      const res = await listContributions(statusFilter === "all" ? undefined : statusFilter);
      setCommunitySubmissions(res.contributions || []);
    } catch (err: any) {
      console.error("Failed to load community submissions:", err);
    } finally {
      setIsLoadingSubmissions(false);
    }
  };

  // Drag-and-drop handlers
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setErrorMsg(null);
    const validExtensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Unsupported video format (${ext}). Supported formats: ${validExtensions.join(", ")}`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg(`File size ${(file.size / (1024 * 1024)).toFixed(1)} MB exceeds the 50 MB limit.`);
      return;
    }

    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
    }
    const preview = URL.createObjectURL(file);
    setSelectedFile(file);
    setVideoPreviewUrl(preview);
    // Reset subsequent steps
    setContributionId(null);
    setContributionMeta(null);
    setFrames([]);
    setQualityReport(null);
    setSubmissionComplete(false);
  };

  const handleRemoveFile = () => {
    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
    }
    setSelectedFile(null);
    setVideoPreviewUrl(null);
    setContributionId(null);
    setContributionMeta(null);
    setFrames([]);
    setQualityReport(null);
    setSubmissionComplete(false);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Upload video
  const handleUploadVideo = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMsg(null);
    setUploadProgress(20);

    try {
      setUploadProgress(50);
      const res = await uploadContributionVideo(selectedFile);
      setUploadProgress(100);
      setContributionId(res.contribution_id);

      // Fetch full draft metadata
      const meta = await getContribution(res.contribution_id);
      setContributionMeta(meta);

      // Auto-trigger frame extraction with default settings
      await runFrameExtraction(res.contribution_id, sampleInterval, maxFrames);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload video");
    } finally {
      setIsUploading(false);
    }
  };

  // Frame extraction
  const runFrameExtraction = async (cid: string, interval: number, max: number) => {
    setIsExtracting(true);
    setErrorMsg(null);
    try {
      const res = await extractContributionFrames(cid, interval, max);
      setFrames(res.frames || []);
      setQualityReport(res.quality_report);

      // Refresh metadata
      const meta = await getContribution(cid);
      setContributionMeta(meta);
    } catch (err: any) {
      setErrorMsg(err.message || "Frame extraction failed");
    } finally {
      setIsExtracting(false);
    }
  };

  // Delete / Exclude single frame
  const handleDeleteFrame = async (frameId: string) => {
    if (!contributionId) return;
    try {
      const res = await deleteContributionFrame(contributionId, frameId);
      setFrames((prev) =>
        prev.map((f) => (f.frame_id === frameId ? { ...f, status: "removed" } : f))
      );
      if (contributionMeta) {
        setContributionMeta({
          ...contributionMeta,
          usable_frame_count: res.usable_count,
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to remove frame");
    }
  };

  // Count active frames
  const usableFramesCount = useMemo(() => {
    return frames.filter((f) => f.status === "active").length;
  }, [frames]);

  // Submit contribution
  const handleSubmit = async () => {
    if (!contributionId) return;
    const finalLang = signLanguage === "Other" ? customLanguage.trim() : signLanguage;
    const finalCat = category === "Custom" ? customCategory.trim() : category;

    if (!gestureName.trim()) {
      setErrorMsg("Please enter a gesture name.");
      return;
    }
    if (!meaning.trim()) {
      setErrorMsg("Please enter the meaning or translation.");
      return;
    }
    if (!finalLang) {
      setErrorMsg("Please specify the sign language.");
      return;
    }
    if (!finalCat) {
      setErrorMsg("Please select or enter a category.");
      return;
    }
    if (usableFramesCount < 3) {
      setErrorMsg("At least 3 valid active frames are required for submission.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const updated = await submitContribution(contributionId, {
        gesture_name: gestureName,
        meaning,
        sign_language: finalLang,
        category: finalCat,
        gesture_type: gestureType,
        description: description.trim() || null,
        contributor_id: contributorId.trim() || "anonymous",
      });
      setContributionMeta(updated);
      setSubmissionComplete(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Submission failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reset to start a new contribution
  const handleStartNew = () => {
    handleRemoveFile();
    setGestureName("");
    setMeaning("");
    setSignLanguage("ISL");
    setCustomLanguage("");
    setCategory("Greetings");
    setCustomCategory("");
    setGestureType("dynamic");
    setDescription("");
    setContributorId("");
    setSubmissionComplete(false);
    setErrorMsg(null);
  };

  // Moderation action
  const handleModerate = async (cid: string, approve: boolean, reason?: string) => {
    setIsModerating(true);
    try {
      await reviewContribution(cid, approve, reason);
      await fetchSubmissions();
      if (activeReviewItem?.contribution_id === cid) {
        const refreshed = await getContribution(cid);
        setActiveReviewItem(refreshed);
      }
    } catch (err: any) {
      alert("Moderation error: " + (err.message || String(err)));
    } finally {
      setIsModerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header & Mode Switch */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="yellow" dot size="sm">
                COMMUNITY DATASET PIPELINE
              </Badge>
              <Badge variant="outline" size="sm">
                ML TRAINING ACCELERATOR
              </Badge>
            </div>
            <h1 className="font-heading font-bold text-3xl sm:text-4xl tracking-tight text-text-primary">
              Contribute a Gesture
            </h1>
            <p className="text-sm text-text-secondary mt-1 max-w-2xl">
              Upload sign language video samples to expand GESTURA&apos;s recognition vocabulary.
              Our computer vision pipeline validates clarity, extracts key frames, and pre-processes
              samples for future model training.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-surface-card p-1.5 rounded-lg border border-surface-border self-start md:self-auto">
            <button
              onClick={() => setActiveTab("contribute")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === "contribute"
                  ? "bg-yellow-accent text-black font-semibold shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              New Contribution
            </button>
            <button
              onClick={() => setActiveTab("browse")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === "browse"
                  ? "bg-yellow-accent text-black font-semibold shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Browse Dataset ({communitySubmissions.length})
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error flex items-start gap-3 animate-fadeIn">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-sm font-medium">{errorMsg}</div>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-status-error/60 hover:text-status-error transition-colors"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: CONTRIBUTION WORKFLOW                                              */}
        {/* ========================================================================= */}
        {activeTab === "contribute" && (
          <div className="space-y-8">
            {submissionComplete ? (
              /* Success Confirmation Card */
              <Card elevated className="border-yellow-accent/40 bg-surface-card text-center p-8 sm:p-12 space-y-6 max-w-3xl mx-auto animate-fadeIn">
                <div className="w-16 h-16 rounded-full bg-yellow-accent/10 border border-yellow-accent/40 flex items-center justify-center mx-auto text-yellow-accent">
                  <ShieldCheck className="w-8 h-8" />
                </div>
                <div className="space-y-2">
                  <Badge variant="yellow" size="md">
                    PENDING APPROVAL
                  </Badge>
                  <h2 className="font-heading font-bold text-2xl sm:text-3xl text-text-primary">
                    Contribution Submitted Successfully!
                  </h2>
                  <p className="text-sm text-text-secondary max-w-lg mx-auto">
                    Thank you for contributing to GESTURA. Your gesture sample has been recorded in the community staging dataset with{" "}
                    <span className="text-yellow-accent font-semibold">{usableFramesCount} usable frames</span>.
                  </p>
                </div>

                {contributionMeta && (
                  <div className="bg-surface-elevated/80 border border-surface-border rounded-xl p-4 text-left max-w-md mx-auto space-y-2 font-mono text-xs text-text-secondary">
                    <div className="flex justify-between">
                      <span className="text-text-muted">Contribution ID:</span>
                      <span className="text-yellow-accent">{contributionMeta.contribution_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Gesture Name:</span>
                      <span className="text-text-primary font-semibold">{contributionMeta.gesture_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Sign Language:</span>
                      <span>{contributionMeta.sign_language}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Category:</span>
                      <span>{contributionMeta.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Gesture Type:</span>
                      <span className="uppercase">{contributionMeta.gesture_type}</span>
                    </div>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
                  <Button variant="primary" onClick={handleStartNew}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Contribute Another Gesture
                  </Button>
                  <Button variant="secondary" onClick={() => setActiveTab("browse")}>
                    <Eye className="w-4 h-4 mr-2" />
                    View in Dataset Catalog
                  </Button>
                </div>
              </Card>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Upload, Settings, Frames (7 cols) */}
                <div className="lg:col-span-7 space-y-6">
                  {/* SECTION A: Video Upload */}
                  <Card elevated className="space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-yellow-accent/20 text-yellow-accent font-mono text-xs flex items-center justify-center font-bold">
                          1
                        </span>
                        <h2 className="font-heading font-semibold text-lg text-text-primary">
                          Video Recording Upload
                        </h2>
                      </div>
                      <Badge variant="neutral" size="sm">
                        Max 50 MB • 0.3s - 60s
                      </Badge>
                    </div>

                    {!selectedFile ? (
                      <div
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 ${
                          isDragging
                            ? "border-yellow-accent bg-yellow-accent/5 scale-[1.01]"
                            : "border-surface-border hover:border-yellow-accent/50 hover:bg-surface-elevated/40"
                        }`}
                      >
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="video/mp4,video/quicktime,video/webm,video/x-msvideo,video/x-matroska"
                          onChange={handleFileInputChange}
                          className="hidden"
                        />
                        <div className="w-14 h-14 rounded-2xl bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent shadow-inner">
                          <UploadCloud className="w-7 h-7" />
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-text-primary">
                            Drag & drop your gesture video here, or{" "}
                            <span className="text-yellow-accent underline underline-offset-2">browse files</span>
                          </p>
                          <p className="text-xs text-text-muted">
                            Supported: MP4, MOV, WebM, AVI, MKV (Clear hand visibility recommended)
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="relative rounded-xl overflow-hidden bg-black border border-surface-border aspect-video flex items-center justify-center group">
                          {videoPreviewUrl && (
                            <video
                              src={videoPreviewUrl}
                              controls
                              className="w-full h-full object-contain"
                            />
                          )}
                          <button
                            onClick={handleRemoveFile}
                            className="absolute top-3 right-3 p-2 rounded-lg bg-black/70 hover:bg-status-error/80 text-white transition-colors backdrop-blur-sm"
                            title="Remove video"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {/* File Details bar */}
                        <div className="p-3 bg-surface-elevated rounded-lg border border-surface-border flex flex-wrap items-center justify-between gap-3 text-xs">
                          <div className="flex items-center gap-2 min-w-0">
                            <FileVideo className="w-4 h-4 text-yellow-accent flex-shrink-0" />
                            <span className="font-mono truncate max-w-[200px] sm:max-w-xs text-text-primary font-medium">
                              {selectedFile.name}
                            </span>
                            <span className="text-text-muted">
                              ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                            </span>
                          </div>

                          {!contributionId && (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={handleUploadVideo}
                              isLoading={isUploading}
                            >
                              <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
                              Process Video & Extract
                            </Button>
                          )}
                        </div>

                        {contributionMeta && (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                            <div className="p-2.5 bg-surface-elevated rounded-lg border border-surface-border">
                              <span className="text-[10px] text-text-muted uppercase font-mono block">Duration</span>
                              <span className="text-xs font-mono font-bold text-yellow-accent">
                                {contributionMeta.video_duration_seconds}s
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-elevated rounded-lg border border-surface-border">
                              <span className="text-[10px] text-text-muted uppercase font-mono block">FPS</span>
                              <span className="text-xs font-mono font-bold text-text-primary">
                                {contributionMeta.video_fps}
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-elevated rounded-lg border border-surface-border">
                              <span className="text-[10px] text-text-muted uppercase font-mono block">Resolution</span>
                              <span className="text-xs font-mono font-bold text-text-primary">
                                {contributionMeta.video_resolution[0]}x{contributionMeta.video_resolution[1]}
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-elevated rounded-lg border border-surface-border">
                              <span className="text-[10px] text-text-muted uppercase font-mono block">Total Video Frames</span>
                              <span className="text-xs font-mono font-bold text-text-primary">
                                {contributionMeta.total_video_frames}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </Card>

                  {/* SECTION C & D: Frame Extraction Controls & Quality Inspection */}
                  {contributionId && (
                    <Card elevated className="space-y-5 animate-fadeIn">
                      <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-yellow-accent/20 text-yellow-accent font-mono text-xs flex items-center justify-center font-bold">
                            2
                          </span>
                          <h2 className="font-heading font-semibold text-lg text-text-primary">
                            Frame Extraction & Quality Audit
                          </h2>
                        </div>
                        <Badge variant="yellow" size="sm">
                          {usableFramesCount} Active Frames
                        </Badge>
                      </div>

                      {/* Sampling controls */}
                      <div className="p-4 bg-surface-elevated rounded-xl border border-surface-border space-y-4">
                        <div className="flex items-center justify-between text-xs font-medium text-text-secondary">
                          <span className="flex items-center gap-1.5">
                            <Sliders className="w-3.5 h-3.5 text-yellow-accent" />
                            Sampling Interval:
                          </span>
                          <span className="font-mono text-yellow-accent font-bold">
                            Every {sampleInterval} frames (~{((contributionMeta?.video_fps || 25) / sampleInterval).toFixed(1)} fps)
                          </span>
                        </div>
                        <input
                          type="range"
                          min={1}
                          max={15}
                          value={sampleInterval}
                          onChange={(e) => setSampleInterval(Number(e.target.value))}
                          disabled={isExtracting}
                          className="w-full accent-yellow-accent cursor-pointer"
                        />

                        <div className="flex items-center justify-between text-xs font-medium text-text-secondary">
                          <span>Max Frame Ceiling:</span>
                          <span className="font-mono text-yellow-accent font-bold">{maxFrames} frames</span>
                        </div>
                        <input
                          type="range"
                          min={5}
                          max={60}
                          step={5}
                          value={maxFrames}
                          onChange={(e) => setMaxFrames(Number(e.target.value))}
                          disabled={isExtracting}
                          className="w-full accent-yellow-accent cursor-pointer"
                        />

                        <Button
                          variant="secondary"
                          size="sm"
                          className="w-full"
                          onClick={() => runFrameExtraction(contributionId, sampleInterval, maxFrames)}
                          isLoading={isExtracting}
                        >
                          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                          Re-run CV Quality Audit & Extraction
                        </Button>
                      </div>

                      {/* Quality Report Metrics */}
                      {qualityReport && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            <div className="p-2.5 bg-surface-secondary rounded-lg border border-surface-border text-center">
                              <span className="text-[10px] text-text-muted font-mono uppercase block">Extracted</span>
                              <span className="text-sm font-mono font-bold text-text-primary">
                                {qualityReport.total_frames_extracted}
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-secondary rounded-lg border border-surface-border text-center">
                              <span className="text-[10px] text-text-muted font-mono uppercase block">Usable (Active)</span>
                              <span className="text-sm font-mono font-bold text-status-success">
                                {usableFramesCount}
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-secondary rounded-lg border border-surface-border text-center">
                              <span className="text-[10px] text-text-muted font-mono uppercase block">Blurry Detected</span>
                              <span className={`text-sm font-mono font-bold ${qualityReport.blurry_frames_count > 0 ? "text-yellow-accent" : "text-text-muted"}`}>
                                {qualityReport.blurry_frames_count}
                              </span>
                            </div>
                            <div className="p-2.5 bg-surface-secondary rounded-lg border border-surface-border text-center">
                              <span className="text-[10px] text-text-muted font-mono uppercase block">Duplicate/Static</span>
                              <span className={`text-sm font-mono font-bold ${qualityReport.duplicate_frames_count > 0 ? "text-yellow-accent" : "text-text-muted"}`}>
                                {qualityReport.duplicate_frames_count}
                              </span>
                            </div>
                          </div>

                          {qualityReport.warnings.length > 0 && (
                            <div className="p-3 bg-yellow-dim/50 rounded-lg border border-yellow-accent/30 text-xs text-yellow-accent space-y-1">
                              <div className="flex items-center gap-1.5 font-semibold">
                                <Info className="w-3.5 h-3.5" />
                                Automated Quality Advisory:
                              </div>
                              <ul className="list-disc pl-5 space-y-0.5 text-text-secondary">
                                {qualityReport.warnings.map((w, idx) => (
                                  <li key={idx}>{w}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Frame Grid */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs text-text-secondary">
                          <span>Frame Previews (Click to inspect or exclude unsuitable frames)</span>
                          <span className="font-mono text-text-muted">
                            {usableFramesCount} of {frames.length} selected
                          </span>
                        </div>

                        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 max-h-[420px] overflow-y-auto pr-1">
                          {frames.map((frame) => {
                            const isRemoved = frame.status === "removed";
                            const thumbUrl = getFrameImageUrl(contributionId, frame.frame_id, true);

                            return (
                              <div
                                key={frame.frame_id}
                                className={`relative rounded-lg overflow-hidden border transition-all group ${
                                  isRemoved
                                    ? "opacity-30 border-surface-border bg-black/40 grayscale"
                                    : frame.is_blurry
                                    ? "border-yellow-accent/50 bg-surface-elevated"
                                    : "border-surface-border bg-surface-elevated hover:border-yellow-accent"
                                }`}
                              >
                                <img
                                  src={thumbUrl}
                                  alt={frame.frame_id}
                                  className="w-full aspect-square object-cover"
                                  loading="lazy"
                                />

                                {/* Frame badge overlays */}
                                <div className="absolute top-1 left-1 bg-black/70 px-1 py-0.5 rounded text-[9px] font-mono text-text-primary">
                                  #{frame.frame_index}
                                </div>

                                {frame.is_blurry && !isRemoved && (
                                  <div className="absolute bottom-1 left-1 bg-yellow-accent/90 text-black font-bold px-1 py-0.2 rounded text-[8px] uppercase tracking-wider">
                                    Blur
                                  </div>
                                )}

                                {frame.is_duplicate && !isRemoved && (
                                  <div className="absolute bottom-1 right-1 bg-surface-elevated/90 text-text-muted px-1 py-0.2 rounded text-[8px]">
                                    Dup
                                  </div>
                                )}

                                {/* Hover actions */}
                                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 p-1">
                                  <button
                                    onClick={() => setInspectingFrame(frame)}
                                    className="p-1.5 rounded-md bg-white/20 hover:bg-white/40 text-white transition-colors"
                                    title="Inspect frame"
                                  >
                                    <ZoomIn className="w-3.5 h-3.5" />
                                  </button>
                                  {!isRemoved ? (
                                    <button
                                      onClick={() => handleDeleteFrame(frame.frame_id)}
                                      className="p-1.5 rounded-md bg-status-error/80 hover:bg-status-error text-white transition-colors"
                                      title="Exclude frame"
                                    >
                                      <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                  ) : (
                                    <span className="text-[10px] text-text-muted font-mono">Excluded</span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </Card>
                  )}
                </div>

                {/* Right Column: Gesture Metadata & Submit (5 cols) */}
                <div className="lg:col-span-5 space-y-6">
                  <Card elevated className="space-y-5 sticky top-20">
                    <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-yellow-accent/20 text-yellow-accent font-mono text-xs flex items-center justify-center font-bold">
                          3
                        </span>
                        <h2 className="font-heading font-semibold text-lg text-text-primary">
                          Gesture Annotation
                        </h2>
                      </div>
                      <Badge variant="outline" size="sm">
                        Metadata Form
                      </Badge>
                    </div>

                    <div className="space-y-4 text-xs">
                      {/* Gesture Name */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium flex items-center justify-between">
                          <span>Gesture Label / Name *</span>
                          <span className="text-text-muted font-mono text-[10px]">UPPERCASE</span>
                        </label>
                        <input
                          type="text"
                          value={gestureName}
                          onChange={(e) => setGestureName(e.target.value.toUpperCase())}
                          placeholder="e.g. NAMASTE, THANK_YOU, WATER"
                          className="w-full px-3 py-2 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent font-mono text-sm"
                        />
                      </div>

                      {/* English Meaning / Translation */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium">
                          Meaning / English Translation *
                        </label>
                        <input
                          type="text"
                          value={meaning}
                          onChange={(e) => setMeaning(e.target.value)}
                          placeholder="e.g. Traditional respectful greeting or salutation"
                          className="w-full px-3 py-2 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent text-sm"
                        />
                      </div>

                      {/* Sign Language Selection */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium">
                          Sign Language Dialect *
                        </label>
                        <div className="grid grid-cols-2 gap-1.5">
                          {POPULAR_LANGUAGES.map((lang) => (
                            <button
                              key={lang.code}
                              type="button"
                              onClick={() => setSignLanguage(lang.code)}
                              className={`px-2.5 py-1.5 rounded-lg text-left transition-colors border text-[11px] font-medium truncate ${
                                signLanguage === lang.code
                                  ? "border-yellow-accent bg-yellow-dim text-yellow-accent"
                                  : "border-surface-border bg-surface-elevated text-text-secondary hover:text-text-primary"
                              }`}
                            >
                              {lang.code}
                            </button>
                          ))}
                        </div>
                        {signLanguage === "Other" && (
                          <input
                            type="text"
                            value={customLanguage}
                            onChange={(e) => setCustomLanguage(e.target.value)}
                            placeholder="Specify Sign Language (e.g. LSF, DGS)"
                            className="w-full mt-2 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent text-xs"
                          />
                        )}
                      </div>

                      {/* Category */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium">
                          Category *
                        </label>
                        <select
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-surface-elevated border border-surface-border text-text-primary focus:outline-none focus:border-yellow-accent text-xs"
                        >
                          {POPULAR_CATEGORIES.map((cat) => (
                            <option key={cat} value={cat}>
                              {cat}
                            </option>
                          ))}
                        </select>
                        {category === "Custom" && (
                          <input
                            type="text"
                            value={customCategory}
                            onChange={(e) => setCustomCategory(e.target.value)}
                            placeholder="Enter custom category"
                            className="w-full mt-2 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent text-xs"
                          />
                        )}
                      </div>

                      {/* Static vs Dynamic Toggle */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium flex items-center justify-between">
                          <span>Gesture Motion Dynamics</span>
                          <span className="text-text-muted text-[10px]">Model Architecture Hint</span>
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={() => setGestureType("static")}
                            className={`p-2 rounded-lg border text-left transition-all ${
                              gestureType === "static"
                                ? "border-yellow-accent bg-yellow-dim text-yellow-accent"
                                : "border-surface-border bg-surface-elevated text-text-secondary"
                            }`}
                          >
                            <span className="font-semibold block text-xs">Static Pose</span>
                            <span className="text-[10px] text-text-muted">Single pose (VGG16 spatial)</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setGestureType("dynamic")}
                            className={`p-2 rounded-lg border text-left transition-all ${
                              gestureType === "dynamic"
                                ? "border-yellow-accent bg-yellow-dim text-yellow-accent"
                                : "border-surface-border bg-surface-elevated text-text-secondary"
                            }`}
                          >
                            <span className="font-semibold block text-xs">Dynamic Motion</span>
                            <span className="text-[10px] text-text-muted">Trajectory (CNN+LSTM)</span>
                          </button>
                        </div>
                      </div>

                      {/* Description / Context */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium">
                          Notes / Usage Context (Optional)
                        </label>
                        <textarea
                          rows={2}
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          placeholder="Describe hand placement, orientation, or regional context..."
                          className="w-full px-3 py-2 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent text-xs"
                        />
                      </div>

                      {/* Contributor Pseudonym */}
                      <div className="space-y-1.5">
                        <label className="text-text-secondary font-medium">
                          Contributor Handle (Optional)
                        </label>
                        <input
                          type="text"
                          value={contributorId}
                          onChange={(e) => setContributorId(e.target.value)}
                          placeholder="anonymous / your handle"
                          className="w-full px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-yellow-accent text-xs"
                        />
                      </div>
                    </div>

                    {/* Submission summary bar & CTA */}
                    <div className="pt-3 border-t border-surface-border space-y-3">
                      <div className="flex items-center justify-between text-xs text-text-secondary font-mono">
                        <span>Quality Threshold:</span>
                        <span className={usableFramesCount >= 3 ? "text-status-success font-bold" : "text-status-error font-bold"}>
                          {usableFramesCount >= 3 ? "Ready (≥ 3 frames)" : "Insufficient (< 3 frames)"}
                        </span>
                      </div>

                      <Button
                        variant="primary"
                        size="md"
                        className="w-full font-semibold shadow-md shadow-yellow-accent/10"
                        onClick={handleSubmit}
                        disabled={!contributionId || usableFramesCount < 3 || isSubmitting}
                        isLoading={isSubmitting}
                      >
                        <Send className="w-4 h-4 mr-2" />
                        Submit to Moderation Queue
                      </Button>

                      <p className="text-[11px] text-text-muted text-center leading-relaxed">
                        Submitted gestures undergo automated deduplication and human-in-the-loop review before being promoted to model training sets.
                      </p>
                    </div>
                  </Card>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: BROWSE COMMUNITY DATASET                                           */}
        {/* ========================================================================= */}
        {activeTab === "browse" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-card p-4 rounded-xl border border-surface-border">
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-secondary font-medium">Filter by Status:</span>
                <div className="flex items-center gap-1.5">
                  {["all", "pending_approval", "approved", "rejected"].map((st) => (
                    <button
                      key={st}
                      onClick={() => setStatusFilter(st)}
                      className={`px-3 py-1 rounded-md text-xs font-mono transition-colors ${
                        statusFilter === st
                          ? "bg-yellow-accent text-black font-semibold"
                          : "bg-surface-elevated text-text-secondary hover:text-text-primary"
                      }`}
                    >
                      {st.replace("_", " ").toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <Button variant="ghost" size="sm" onClick={fetchSubmissions}>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Refresh
              </Button>
            </div>

            {isLoadingSubmissions ? (
              <div className="py-16 text-center text-text-muted space-y-2">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-yellow-accent" />
                <p className="text-xs font-mono">Loading community contributions...</p>
              </div>
            ) : communitySubmissions.length === 0 ? (
              <Card elevated className="text-center py-16 space-y-3">
                <Film className="w-10 h-10 text-text-muted mx-auto" />
                <h3 className="font-heading font-semibold text-text-primary">No Contributions Found</h3>
                <p className="text-xs text-text-secondary max-w-sm mx-auto">
                  {statusFilter === "all"
                    ? "No gesture samples have been submitted yet. Be the first contributor!"
                    : `No contributions matching status '${statusFilter}'.`}
                </p>
                <Button variant="primary" size="sm" onClick={() => setActiveTab("contribute")}>
                  <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
                  Upload First Sample
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {communitySubmissions.map((item) => {
                  const statusVariant =
                    item.status === "approved"
                      ? "success"
                      : item.status === "rejected"
                      ? "error"
                      : "yellow";

                  return (
                    <Card
                      key={item.contribution_id}
                      hoverEffect
                      className="p-5 space-y-4 border-surface-border bg-surface-card flex flex-col justify-between"
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="font-heading font-bold text-base text-text-primary block">
                              {item.gesture_name || "DRAFT SAMPLE"}
                            </span>
                            <span className="text-xs text-text-secondary line-clamp-1">
                              {item.meaning || "Awaiting submission details"}
                            </span>
                          </div>
                          <Badge variant={statusVariant} size="sm">
                            {item.status.replace("_", " ").toUpperCase()}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-3 gap-1.5 pt-2 border-t border-surface-border text-center">
                          <div className="p-1.5 bg-surface-elevated rounded border border-surface-border">
                            <span className="text-[9px] text-text-muted font-mono block">LANG</span>
                            <span className="text-xs font-bold text-yellow-accent font-mono truncate block">
                              {item.sign_language || "N/A"}
                            </span>
                          </div>
                          <div className="p-1.5 bg-surface-elevated rounded border border-surface-border">
                            <span className="text-[9px] text-text-muted font-mono block">FRAMES</span>
                            <span className="text-xs font-bold text-text-primary font-mono block">
                              {item.usable_frame_count}
                            </span>
                          </div>
                          <div className="p-1.5 bg-surface-elevated rounded border border-surface-border">
                            <span className="text-[9px] text-text-muted font-mono block">DURATION</span>
                            <span className="text-xs font-bold text-text-primary font-mono block">
                              {item.video_duration_seconds}s
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-surface-border flex items-center justify-between text-xs">
                        <span className="font-mono text-[10px] text-text-muted truncate max-w-[120px]">
                          {item.contribution_id}
                        </span>

                        <div className="flex items-center gap-1.5">
                          {item.status === "pending_approval" && (
                            <>
                              <button
                                onClick={() => handleModerate(item.contribution_id, true)}
                                disabled={isModerating}
                                className="px-2 py-1 rounded bg-status-success/20 hover:bg-status-success/40 text-status-success font-medium text-[11px] transition-colors"
                                title="Approve into training dataset"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleModerate(item.contribution_id, false, "Does not meet dataset quality criteria")}
                                disabled={isModerating}
                                className="px-2 py-1 rounded bg-status-error/20 hover:bg-status-error/40 text-status-error font-medium text-[11px] transition-colors"
                                title="Reject sample"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* FRAME INSPECTOR MODAL                                                     */}
        {/* ========================================================================= */}
        {inspectingFrame && contributionId && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
            <div className="bg-surface-card border border-surface-border rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl space-y-4 p-6">
              <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-yellow-accent">
                    {inspectingFrame.frame_id}
                  </span>
                  <Badge variant={inspectingFrame.is_blurry ? "yellow" : "success"} size="sm">
                    Sharpness: {inspectingFrame.sharpness_score}
                  </Badge>
                </div>
                <button
                  onClick={() => setInspectingFrame(null)}
                  className="p-1 rounded-lg text-text-muted hover:text-text-primary transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-surface-border flex items-center justify-center">
                <img
                  src={getFrameImageUrl(contributionId, inspectingFrame.frame_id, false)}
                  alt={inspectingFrame.frame_id}
                  className="max-h-full max-w-full object-contain"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 bg-surface-elevated rounded-lg">
                  <span className="text-[10px] text-text-muted font-mono block">TIMESTAMP</span>
                  <span className="font-mono font-bold text-text-primary">
                    {inspectingFrame.timestamp_ms.toFixed(1)} ms
                  </span>
                </div>
                <div className="p-2 bg-surface-elevated rounded-lg">
                  <span className="text-[10px] text-text-muted font-mono block">RESOLUTION</span>
                  <span className="font-mono font-bold text-text-primary">
                    {inspectingFrame.width}x{inspectingFrame.height}
                  </span>
                </div>
                <div className="p-2 bg-surface-elevated rounded-lg">
                  <span className="text-[10px] text-text-muted font-mono block">BLUR STATUS</span>
                  <span className={`font-mono font-bold ${inspectingFrame.is_blurry ? "text-yellow-accent" : "text-status-success"}`}>
                    {inspectingFrame.is_blurry ? "BLURRY" : "SHARP"}
                  </span>
                </div>
                <div className="p-2 bg-surface-elevated rounded-lg">
                  <span className="text-[10px] text-text-muted font-mono block">DUPLICATE</span>
                  <span className="font-mono font-bold text-text-primary">
                    {inspectingFrame.is_duplicate ? "YES" : "NO"}
                  </span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                {inspectingFrame.status === "active" ? (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                      handleDeleteFrame(inspectingFrame.frame_id);
                      setInspectingFrame(null);
                    }}
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                    Exclude This Frame
                  </Button>
                ) : (
                  <Badge variant="neutral">Frame Already Excluded</Badge>
                )}
                <Button variant="secondary" size="sm" onClick={() => setInspectingFrame(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

