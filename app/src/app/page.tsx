"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { HandVisualizer } from "@/components/hand-visualizer";
import {
  Camera,
  Cpu,
  Volume2,
  Sparkles,
  ShieldCheck,
  Zap,
  ArrowRight,
  Layers,
  Activity,
  CheckCircle2,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1">
        {/* HERO SECTION */}
        <section className="relative overflow-hidden pt-12 pb-24 md:pt-20 md:pb-32 border-b border-surface-border">
          {/* Subtle grid background */}
          <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />

          {/* Accent glow in center */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-yellow-accent/5 rounded-full blur-[120px] pointer-events-none" />

          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left Column: Headlines & Call to Actions */}
              <div className="lg:col-span-7 space-y-8">
                {/* Status pill */}
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-card border border-surface-border text-xs font-mono text-yellow-accent">
                  <span className="w-2 h-2 rounded-full bg-yellow-accent animate-pulse" />
                  <span>NEXT-GEN VISION AI FOR ACCESSIBILITY</span>
                </div>

                {/* Hero Title */}
                <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.05]">
                  YOUR HANDS.
                  <br />
                  <span className="text-yellow-accent">YOUR VOICE.</span>
                  <br />
                  ONE CONNECTION.
                </h1>

                {/* Description */}
                <p className="text-text-secondary text-lg sm:text-xl max-w-2xl leading-relaxed">
                  Breaking communication barriers through intelligent gesture recognition.
                  Transform real-time vision frames into spoken audio and translated text with
                  millisecond precision.
                </p>

                {/* CTAs */}
                <div className="flex flex-wrap items-center gap-4 pt-2">
                  <Link
                    href="/studio"
                    className="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-lg bg-yellow-accent text-black font-semibold text-base tracking-wide hover:bg-yellow-hover shadow-lg shadow-yellow-accent/10 active:scale-[0.98] transition-all"
                  >
                    <span>START TRANSLATING</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>

                  <Link
                    href="/gestures"
                    className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg bg-surface-card border border-surface-border text-text-primary font-medium text-base hover:border-yellow-accent/40 active:scale-[0.98] transition-all"
                  >
                    <span>EXPLORE GESTURES</span>
                  </Link>
                </div>

                {/* Feature tags */}
                <div className="grid grid-cols-3 gap-4 pt-6 border-t border-surface-border/60 max-w-xl">
                  <div>
                    <div className="font-mono text-xl font-bold text-white">~18ms</div>
                    <div className="text-xs text-text-muted mt-0.5">Inference Latency</div>
                  </div>
                  <div>
                    <div className="font-mono text-xl font-bold text-yellow-accent">21 Points</div>
                    <div className="text-xs text-text-muted mt-0.5">Landmark Topology</div>
                  </div>
                  <div>
                    <div className="font-mono text-xl font-bold text-white">100% Private</div>
                    <div className="text-xs text-text-muted mt-0.5">In-Memory Frames</div>
                  </div>
                </div>
              </div>

              {/* Right Column: Hand Landmark Visualizer */}
              <div className="lg:col-span-5 flex justify-center">
                <div className="relative w-full max-w-md p-6 rounded-2xl bg-surface-card border border-surface-border shadow-2xl">
                  {/* Visualizer header */}
                  <div className="flex items-center justify-between pb-4 mb-4 border-b border-surface-border text-xs font-mono text-text-secondary">
                    <span className="flex items-center gap-2 text-yellow-accent">
                      <Activity className="w-3.5 h-3.5" />
                      MEDIAPIPE KINEMATICS
                    </span>
                    <span className="text-text-muted">ACTIVE TRACKING</span>
                  </div>

                  {/* Visualizer canvas */}
                  <HandVisualizer className="h-80 w-full" />

                  {/* Live Caption readout */}
                  <div className="mt-4 p-3 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-between">
                    <div>
                      <div className="text-[10px] font-mono text-text-muted uppercase">Detected Landmark State</div>
                      <div className="text-sm font-heading font-semibold text-white">
                        CONFIRMED GESTURE: <span className="text-yellow-accent">"HELLO"</span>
                      </div>
                    </div>
                    <Volume2 className="w-5 h-5 text-yellow-accent animate-pulse" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS SECTION */}
        <section className="py-24 border-b border-surface-border bg-surface-secondary/40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="text-xs font-mono text-yellow-accent uppercase tracking-widest">
                ARCHITECTURAL PIPELINE
              </span>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white mt-2">
                How GESTURA Translates Sign Language
              </h2>
              <p className="text-text-secondary text-base mt-4">
                From raw camera frames to synthesized spoken sentences in three synchronized stages.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Step 1 */}
              <div className="p-8 rounded-xl bg-surface-card border border-surface-border relative group hover:border-yellow-accent/40 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent mb-6">
                  <Camera className="w-6 h-6" />
                </div>
                <div className="font-mono text-xs text-yellow-accent/80 font-bold mb-2">01 / CAPTURE</div>
                <h3 className="font-heading text-xl font-bold text-white mb-3">Frame Normalization</h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  Browser camera streams high-rate video. Frames are cropped and normalized to 224×224 RGB tensors using OpenCV, without persisting raw footage.
                </p>
              </div>

              {/* Step 2 */}
              <div className="p-8 rounded-xl bg-surface-card border border-surface-border relative group hover:border-yellow-accent/40 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent mb-6">
                  <Cpu className="w-6 h-6" />
                </div>
                <div className="font-mono text-xs text-yellow-accent/80 font-bold mb-2">02 / INFERENCE</div>
                <h3 className="font-heading text-xl font-bold text-white mb-3">Neural Classification</h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  A VGG16 backbone extracts deep visual features. A temporal confirmation buffer stabilizes predictions over 5 consecutive frames to eradicate false positives.
                </p>
              </div>

              {/* Step 3 */}
              <div className="p-8 rounded-xl bg-surface-card border border-surface-border relative group hover:border-yellow-accent/40 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent mb-6">
                  <Volume2 className="w-6 h-6" />
                </div>
                <div className="font-mono text-xs text-yellow-accent/80 font-bold mb-2">03 / SYNTHESIS</div>
                <h3 className="font-heading text-xl font-bold text-white mb-3">Instant Speech</h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  Confirmed gestures are converted to natural human speech through the Web Speech API with duplicate suppression and transcript persistence.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* KEY FEATURES SECTION */}
        <section className="py-24 border-b border-surface-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              <div className="lg:col-span-5 space-y-6">
                <span className="text-xs font-mono text-yellow-accent uppercase tracking-widest">
                  ENGINEERED FOR ACCESSIBILITY
                </span>
                <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white leading-tight">
                  State-of-the-art accuracy with zero privacy compromises.
                </h2>
                <p className="text-text-secondary text-base leading-relaxed">
                  GESTURA was designed from first principles as an assistive communication companion.
                  Whether used in a classroom, clinic, or video call, the interface maintains rock-solid
                  stability.
                </p>

                <div className="space-y-4 pt-2">
                  {[
                    "Temporal confirmation buffer prevents flickering classifications",
                    "Dual-mode operation: Live streaming or single-frame snapshot audit",
                    "Full transcript history export with timestamped session logs",
                    "Client-only video pipeline ensures absolute biometric privacy",
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-yellow-accent shrink-0 mt-0.5" />
                      <span className="text-sm text-text-secondary">{item}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-4">
                  <Link
                    href="/about"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-yellow-accent hover:underline"
                  >
                    <span>Read complete architecture documentation</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>

              {/* Feature Cards Grid */}
              <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="p-6 rounded-xl bg-surface-card border border-surface-border">
                  <Zap className="w-6 h-6 text-yellow-accent mb-3" />
                  <h4 className="font-heading text-lg font-bold text-white mb-1">
                    Temporal Stabilization
                  </h4>
                  <p className="text-text-muted text-xs leading-relaxed">
                    Confidence thresholds paired with a 5-frame confirmation window ensure gestures are announced only when intentionally held.
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-surface-card border border-surface-border">
                  <ShieldCheck className="w-6 h-6 text-yellow-accent mb-3" />
                  <h4 className="font-heading text-lg font-bold text-white mb-1">
                    Zero-Footprint Privacy
                  </h4>
                  <p className="text-text-muted text-xs leading-relaxed">
                    Video frames exist only in transient memory during inference. No recordings, telemetry images, or biometric profiles leave your machine.
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-surface-card border border-surface-border">
                  <Layers className="w-6 h-6 text-yellow-accent mb-3" />
                  <h4 className="font-heading text-lg font-bold text-white mb-1">
                    Modular Model Backbone
                  </h4>
                  <p className="text-text-muted text-xs leading-relaxed">
                    PyTorch transfer learning architecture supports instant adaptation to expanded gesture datasets without breaking interface contracts.
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-surface-card border border-surface-border">
                  <Sparkles className="w-6 h-6 text-yellow-accent mb-3" />
                  <h4 className="font-heading text-lg font-bold text-white mb-1">
                    Speech & Text Synthesis
                  </h4>
                  <p className="text-text-muted text-xs leading-relaxed">
                    Immediate multi-modal translation converts visual hand signs into both formatted real-time text and high-fidelity browser voice.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA BANNER */}
        <section className="py-20 relative bg-surface-secondary/60">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-white">
              Ready to experience gesture translation in real-time?
            </h2>
            <p className="text-text-secondary text-base max-w-xl mx-auto">
              Launch the studio, activate your camera, and communicate with the assistance of computer vision AI.
            </p>
            <div className="pt-2">
              <Link
                href="/studio"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-yellow-accent text-black font-semibold text-base tracking-wide hover:bg-yellow-hover shadow-xl shadow-yellow-accent/15 transition-all"
              >
                <span>OPEN RECOGNITION STUDIO</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
