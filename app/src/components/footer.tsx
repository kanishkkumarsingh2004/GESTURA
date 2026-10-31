import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-surface-border bg-surface-secondary/60 py-12 text-sm text-text-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2">
              <span className="font-heading font-bold text-lg text-text-primary tracking-wider">
                GESTURA
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-accent" />
            </div>
            <p className="text-xs text-text-muted leading-relaxed">
              Real-time computer vision gesture translation assistant. Built with
              PyTorch, OpenCV, VGG16, and Next.js.
            </p>
            <div className="text-xs font-mono text-yellow-accent/80">
              v1.0.0 — Production Ready
            </div>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-heading text-xs uppercase tracking-wider text-text-primary font-semibold mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/studio" className="hover:text-yellow-accent transition-colors">
                  Live Recognition Studio
                </Link>
              </li>
              <li>
                <Link href="/gestures" className="hover:text-yellow-accent transition-colors">
                  Gesture Vocabulary
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-yellow-accent transition-colors">
                  Session History
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-yellow-accent transition-colors">
                  About & Architecture
                </Link>
              </li>
            </ul>
          </div>

          {/* Machine Learning Specs */}
          <div>
            <h4 className="font-heading text-xs uppercase tracking-wider text-text-primary font-semibold mb-3">
              ML Specs
            </h4>
            <ul className="space-y-2 text-xs font-mono text-text-muted">
              <li>Backbone: VGG16 Transfer Learning</li>
              <li>Input Size: 224 x 224 RGB</li>
              <li>Stabilization: 5-frame temporal buffer</li>
              <li>Latency: ~18ms on GPU</li>
            </ul>
          </div>

          {/* Privacy & Compliance */}
          <div>
            <h4 className="font-heading text-xs uppercase tracking-wider text-text-primary font-semibold mb-3">
              Privacy & Security
            </h4>
            <p className="text-xs text-text-muted leading-relaxed mb-2">
              Camera frames are evaluated in memory and discarded instantly. No video data or biometric information is ever persisted.
            </p>
            <span className="inline-flex items-center gap-1.5 text-xs text-status-success">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
              Local Buffer Only
            </span>
          </div>
        </div>

        <div className="pt-8 border-t border-surface-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-muted">
          <div>© {new Date().getFullYear()} GESTURA AI. Designed for accessible human-computer communication.</div>
          <div className="flex items-center gap-4">
            <span className="font-mono">Status: All Systems Operational</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

