"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { GESTURE_CATALOG, type GestureItem } from "@/lib/gestures-data";
import { speech } from "@/lib/speech";
import {
  Search,
  Volume2,
  Sparkles,
  ArrowRight,
  Filter,
  CheckCircle,
} from "lucide-react";

export default function GesturesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [playingId, setPlayingId] = useState<string | null>(null);

  const categories = useMemo(() => {
    const cats = Array.from(new Set(GESTURE_CATALOG.map((g) => g.category)));
    return ["All", ...cats];
  }, []);

  const filteredGestures = useMemo(() => {
    return GESTURE_CATALOG.filter((g) => {
      const matchesCategory =
        selectedCategory === "All" || g.category === selectedCategory;
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        g.name.toLowerCase().includes(q) ||
        g.text.toLowerCase().includes(q) ||
        g.description.toLowerCase().includes(q);
      return matchesCategory && matchesSearch;
    });
  }, [searchQuery, selectedCategory]);

  const handleSpeak = (g: GestureItem) => {
    setPlayingId(g.id);
    speech.speak(g.text, true);
    setTimeout(() => {
      setPlayingId(null);
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-heading text-3xl sm:text-4xl font-bold tracking-tight text-white">
                Gesture Vocabulary Library
              </h1>
              <Badge variant="yellow" size="sm">
                {GESTURE_CATALOG.length} CLASSES
              </Badge>
            </div>
            <p className="text-text-secondary text-sm mt-1 max-w-2xl">
              Inspect all supported hand gestures recognized by GESTURA's neural classification
              pipeline, their spoken translations, and kinematic postures.
            </p>
          </div>

          <Link
            href="/studio"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-yellow-accent text-black font-semibold text-xs tracking-wide hover:bg-yellow-hover shadow-sm transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Test In Live Studio</span>
          </Link>
        </div>

        {/* Search and Filters Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search gestures, translations, or keywords..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm placeholder:text-text-muted focus:border-yellow-accent/60 outline-none transition-colors"
            />
          </div>

          {/* Category Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat
                    ? "bg-yellow-accent text-black font-semibold shadow-sm"
                    : "bg-surface-card border border-surface-border text-text-secondary hover:text-white"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Gestures Cards Grid */}
        {filteredGestures.length === 0 ? (
          <div className="py-20 text-center text-text-muted space-y-2">
            <p className="text-base text-white">No matching gestures found</p>
            <p className="text-xs">Try adjusting your search query or selected category filter.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredGestures.map((gesture) => (
              <Card
                key={gesture.id}
                hoverEffect
                className="bg-surface-card border-surface-border flex flex-col justify-between space-y-4"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-2 pb-3 border-b border-surface-border">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-heading font-bold text-xl text-white tracking-wide">
                          {gesture.name}
                        </span>
                        {gesture.isVocabularyCore && (
                          <span
                            title="Primary spoken vocabulary class"
                            className="w-1.5 h-1.5 rounded-full bg-yellow-accent"
                          />
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-yellow-accent font-semibold">
                        SPOKEN: &ldquo;{gesture.text}&rdquo;
                      </span>
                    </div>

                    <Badge variant="neutral" size="sm">
                      {gesture.category}
                    </Badge>
                  </div>

                  {/* Pose Description */}
                  <div className="space-y-2 pt-3">
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {gesture.description}
                    </p>

                    <div className="p-3 rounded-lg bg-surface-secondary border border-surface-border/60 text-[11px] text-text-muted leading-relaxed">
                      <span className="text-text-primary font-mono font-semibold block mb-0.5">
                        KINEMATIC POSTURE:
                      </span>
                      {gesture.handPosture}
                    </div>
                  </div>
                </div>

                {/* Card Action: Audition Voice */}
                <div className="pt-2 border-t border-surface-border/60 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-text-muted">
                    {gesture.isVocabularyCore ? "CORE MODEL CLASS" : "HAGRID EXTENSION"}
                  </span>

                  <button
                    onClick={() => handleSpeak(gesture)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-yellow-accent hover:text-black border border-surface-border text-text-secondary text-xs font-medium transition-all group"
                  >
                    <Volume2
                      className={`w-3.5 h-3.5 ${
                        playingId === gesture.id
                          ? "text-yellow-accent animate-ping"
                          : "group-hover:text-black"
                      }`}
                    />
                    <span>Audition Speech</span>
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Information Callout */}
        <div className="p-6 rounded-2xl bg-surface-card border border-surface-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h4 className="font-heading font-bold text-base text-white">
              Dataset Alignment Assurance
            </h4>
            <p className="text-xs text-text-muted max-w-2xl leading-relaxed">
              All listed gesture classes mirror the unified class mappings verified in{" "}
              <code className="text-yellow-accent">config.yaml</code> and the VGG16 transfer learning
              backbone. Unsupported gestures are classified under the ambient{" "}
              <code className="text-yellow-accent">NONE</code> category.
            </p>
          </div>

          <Link
            href="/about"
            className="text-xs font-mono text-yellow-accent hover:underline whitespace-nowrap"
          >
            Review Model Specs →
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}
