import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0B0B0B",
        surface: {
          secondary: "#111111",
          card: "#171717",
          elevated: "#202020",
          border: "#292929",
        },
        yellow: {
          accent: "#F5E642",
          hover: "#E5D632",
          dim: "rgba(245, 230, 66, 0.12)",
          border: "rgba(245, 230, 66, 0.3)",
        },
        text: {
          primary: "#FFFFFF",
          secondary: "#A1A1AA",
          muted: "#71717A",
        },
        status: {
          success: "#70D6A3",
          error: "#FF6464",
          warning: "#F5E642",
        },
      },
      fontFamily: {
        heading: ["Space Grotesk", "sans-serif"],
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scan-line": "scan 3s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        scan: {
          "0%, 100%": { transform: "translateY(0%)" },
          "50%": { transform: "translateY(100%)" },
        },
        glow: {
          "0%": { opacity: "0.4" },
          "100%": { opacity: "0.9" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
