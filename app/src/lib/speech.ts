/**
 * Client-side Speech Synthesis helper for GESTURA.
 * Converts recognized gesture text into spoken voice via the Web Speech API.
 */

class SpeechManager {
  private synth: SpeechSynthesis | null = null;
  private voice: SpeechSynthesisVoice | null = null;
  private enabled: boolean = true;
  private lastSpokenText: string = "";
  private lastSpokenTime: number = 0;
  private duplicateCooldownMs: number = 2000;

  constructor() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      this.synth = window.speechSynthesis;
      this.initVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this.initVoices();
      }
    }
  }

  private initVoices() {
    if (!this.synth) return;
    const voices = this.synth.getVoices();
    // Prefer English natural voices if available
    this.voice =
      voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google"))) ||
      voices.find((v) => v.lang.startsWith("en")) ||
      voices[0] ||
      null;
  }

  public setEnabled(val: boolean) {
    this.enabled = val;
    if (!val && this.synth) {
      this.synth.cancel();
    }
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public speak(text: string, force: boolean = false) {
    if (!this.synth || !this.enabled || !text.trim()) return;

    const now = Date.now();
    if (!force && text === this.lastSpokenText && now - this.lastSpokenTime < this.duplicateCooldownMs) {
      return; // Suppress immediate duplicate
    }

    this.synth.cancel(); // Stop any pending speech to maintain low latency

    const utterance = new SpeechSynthesisUtterance(text);
    if (this.voice) {
      utterance.voice = this.voice;
    }
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    this.lastSpokenText = text;
    this.lastSpokenTime = now;

    this.synth.speak(utterance);
  }

  public stop() {
    if (this.synth) {
      this.synth.cancel();
    }
  }
}

export const speech = new SpeechManager();

