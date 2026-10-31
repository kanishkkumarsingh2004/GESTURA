import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import {
  Sparkles,
  Shield,
  Eye,
  Layers,
  Cpu,
  ArrowRight,
  Heart,
  Volume2,
  Terminal,
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        {/* Header */}
        <div className="space-y-4 text-center max-w-3xl mx-auto">
          <Badge variant="yellow" size="md">
            PROJECT OVERVIEW & MANIFESTO
          </Badge>
          <h1 className="font-heading text-4xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            About GESTURA
          </h1>
          <p className="text-text-secondary text-base sm:text-lg leading-relaxed">
            GESTURA is an intelligent, vision-based assistive application designed to bridge the
            communication chasm between non-verbal individuals, sign language users, and the wider world.
          </p>
        </div>

        {/* Mission & Problem Statement */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card className="bg-surface-card border-surface-border space-y-4 p-8">
            <div className="w-10 h-10 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent">
              <Heart className="w-5 h-5" />
            </div>
            <h3 className="font-heading text-xl font-bold text-white">The Mission</h3>
            <p className="text-text-secondary text-sm leading-relaxed">
              Millions of deaf, hard-of-hearing, and speech-impaired individuals rely daily on
              hand sign languages. Because general populations rarely understand these grammars,
              social and professional isolation remains widespread.
            </p>
            <p className="text-text-secondary text-sm leading-relaxed">
              GESTURA provides an instantaneous, accessible bridge — converting physical hand signs into
              both synthesized voice and readable text without requiring expensive specialty hardware.
            </p>
          </Card>

          <Card className="bg-surface-card border-surface-border space-y-4 p-8">
            <div className="w-10 h-10 rounded-lg bg-surface-elevated border border-surface-border flex items-center justify-center text-yellow-accent">
              <Eye className="w-5 h-5" />
            </div>
            <h3 className="font-heading text-xl font-bold text-white">The Engineering Vision</h3>
            <p className="text-text-secondary text-sm leading-relaxed">
              Traditional computer vision demos often rely on static image uploads or suffer from
              severe temporal jitter. GESTURA couples a deep convolutional neural network with a
              robust temporal state machine to eliminate false triggers.
            </p>
            <p className="text-text-secondary text-sm leading-relaxed">
              Every camera frame is processed strictly in volatile memory. We reject persistent video
              logging and biometric telemetry, ensuring dignity and uncompromising privacy for every user.
            </p>
          </Card>
        </div>

        {/* How the System Works (Architecture Deep Dive) */}
        <div className="p-8 rounded-2xl bg-surface-card border border-surface-border space-y-8">
          <div>
            <span className="text-xs font-mono text-yellow-accent uppercase tracking-widest">
              END-TO-END PIPELINE
            </span>
            <h3 className="font-heading text-2xl font-bold text-white mt-1">
              How the System Operates
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-surface-secondary border border-surface-border space-y-2">
              <div className="font-mono text-xs text-yellow-accent font-bold">STAGE 01</div>
              <h4 className="font-heading font-bold text-white text-sm">Frame Normalization</h4>
              <p className="text-text-muted text-xs leading-relaxed">
                OpenCV preprocessor samples live webcam video, centers the region of interest, and
                rescales the frame to standard 224×224 RGB tensors.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-surface-secondary border border-surface-border space-y-2">
              <div className="font-mono text-xs text-yellow-accent font-bold">STAGE 02</div>
              <h4 className="font-heading font-bold text-white text-sm">Deep Feature Extraction</h4>
              <p className="text-text-muted text-xs leading-relaxed">
                A PyTorch VGG16 backbone processes spatial features across convolutional layers,
                projecting embeddings into classification logits.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-surface-secondary border border-surface-border space-y-2">
              <div className="font-mono text-xs text-yellow-accent font-bold">STAGE 03</div>
              <h4 className="font-heading font-bold text-white text-sm">Temporal Stabilization</h4>
              <p className="text-text-muted text-xs leading-relaxed">
                A rolling window verifies the gesture exceeds confidence thresholds for 5 consecutive
                frames before declaring a confirmed detection.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-surface-secondary border border-surface-border space-y-2">
              <div className="font-mono text-xs text-yellow-accent font-bold">STAGE 04</div>
              <h4 className="font-heading font-bold text-white text-sm">Spoken Translation</h4>
              <p className="text-text-muted text-xs leading-relaxed">
                Confirmed gestures trigger browser-side Web Speech API utterance generation, with
                duplicate suppression and session transcript logging.
              </p>
            </div>
          </div>
        </div>

        {/* Technology Stack Grid */}
        <div className="space-y-6">
          <div className="text-center max-w-xl mx-auto">
            <span className="text-xs font-mono text-yellow-accent uppercase tracking-widest">
              MODERN TECHNOLOGIES
            </span>
            <h3 className="font-heading text-2xl font-bold text-white mt-1">
              Engineered with Production-Grade Stacks
            </h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { title: "PyTorch 2.4", role: "Model & Transfer Learning" },
              { title: "OpenCV", role: "Computer Vision Pipeline" },
              { title: "Next.js 14", role: "React Web Architecture" },
              { title: "FastAPI", role: "Asynchronous REST Microservice" },
              { title: "Tailwind CSS", role: "High-Performance Design System" },
              { title: "Web Speech API", role: "Zero-Latency Client Voice" },
            ].map((tech, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-surface-card border border-surface-border flex flex-col justify-between"
              >
                <div className="font-heading font-bold text-white text-sm">{tech.title}</div>
                <div className="text-[11px] text-text-muted mt-2">{tech.role}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="p-8 rounded-2xl bg-surface-card border border-surface-border text-center space-y-4">
          <h3 className="font-heading text-2xl font-bold text-white">
            Experience the Gesture Recognition Studio
          </h3>
          <p className="text-text-secondary text-sm max-w-md mx-auto">
            Launch your camera and test sign language detection directly in your browser.
          </p>
          <div className="pt-2">
            <Link
              href="/studio"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-yellow-accent text-black font-semibold text-sm tracking-wide hover:bg-yellow-hover transition-all"
            >
              <span>LAUNCH LIVE STUDIO</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

