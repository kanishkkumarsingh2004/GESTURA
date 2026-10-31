"use client";

import { useEffect, useState } from "react";

// 21 standard MediaPipe Hand Landmark coordinates normalized to 0..100 viewBox
const DEFAULT_LANDMARKS = [
  { id: 0, x: 50, y: 88, label: "WRIST" },
  // Thumb
  { id: 1, x: 38, y: 76, label: "THUMB_CMC" },
  { id: 2, x: 30, y: 62, label: "THUMB_MCP" },
  { id: 3, x: 26, y: 48, label: "THUMB_IP" },
  { id: 4, x: 23, y: 36, label: "THUMB_TIP" },
  // Index
  { id: 5, x: 42, y: 50, label: "INDEX_MCP" },
  { id: 6, x: 41, y: 35, label: "INDEX_PIP" },
  { id: 7, x: 41, y: 24, label: "INDEX_DIP" },
  { id: 8, x: 41, y: 15, label: "INDEX_TIP" },
  // Middle
  { id: 9, x: 52, y: 48, label: "MID_MCP" },
  { id: 10, x: 52, y: 32, label: "MID_PIP" },
  { id: 11, x: 52, y: 20, label: "MID_DIP" },
  { id: 12, x: 52, y: 11, label: "MID_TIP" },
  // Ring
  { id: 13, x: 62, y: 52, label: "RING_MCP" },
  { id: 14, x: 63, y: 37, label: "RING_PIP" },
  { id: 15, x: 63, y: 26, label: "RING_DIP" },
  { id: 16, x: 63, y: 18, label: "RING_TIP" },
  // Pinky
  { id: 17, x: 72, y: 58, label: "PINKY_MCP" },
  { id: 18, x: 75, y: 46, label: "PINKY_PIP" },
  { id: 19, x: 76, y: 37, label: "PINKY_DIP" },
  { id: 20, x: 77, y: 30, label: "PINKY_TIP" },
];

const CONNECTIONS: [number, number][] = [
  // Palm base
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  // Palm knuckle loop
  [0, 5],
  [5, 9],
  [9, 13],
  [13, 17],
  [0, 17],
  // Index finger
  [5, 6],
  [6, 7],
  [7, 8],
  // Middle finger
  [9, 10],
  [10, 11],
  [11, 12],
  // Ring finger
  [13, 14],
  [14, 15],
  [15, 16],
  // Pinky finger
  [17, 18],
  [18, 19],
  [19, 20],
];

interface HandVisualizerProps {
  className?: string;
  activeGesture?: string;
  interactive?: boolean;
}

export function HandVisualizer({
  className = "",
  activeGesture = "HELLO",
  interactive = true,
}: HandVisualizerProps) {
  const [pulse, setPulse] = useState(0);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse((p) => (p + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Subtle natural undulating motion for landmarks
  const animatedLandmarks = DEFAULT_LANDMARKS.map((lm, i) => {
    const wave = Math.sin((pulse * 0.1) + i * 0.4) * 1.2;
    return {
      ...lm,
      x: lm.x + (i % 2 === 0 ? wave * 0.5 : -wave * 0.5),
      y: lm.y + wave,
    };
  });

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-yellow-accent/5 rounded-full blur-3xl pointer-events-none" />

      {/* SVG Canvas */}
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full max-w-[420px] max-h-[420px] drop-shadow-[0_0_25px_rgba(245,230,66,0.2)]"
      >
        <defs>
          <linearGradient id="lineGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#292929" />
            <stop offset="60%" stopColor="#F5E642" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#F5E642" />
          </linearGradient>

          <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Scan line */}
        <line
          x1="10"
          y1={((pulse * 1.5) % 100)}
          x2="90"
          y2={((pulse * 1.5) % 100)}
          stroke="#F5E642"
          strokeOpacity="0.25"
          strokeWidth="0.5"
          strokeDasharray="2 2"
        />

        {/* Skeletal connections */}
        {CONNECTIONS.map(([start, end], idx) => {
          const p1 = animatedLandmarks[start];
          const p2 = animatedLandmarks[end];
          const isHighlighted = hoveredNode === start || hoveredNode === end;
          return (
            <line
              key={idx}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              stroke={isHighlighted ? "#FFFFFF" : "url(#lineGrad)"}
              strokeWidth={isHighlighted ? "1.4" : "0.85"}
              strokeOpacity={isHighlighted ? "1" : "0.75"}
              strokeLinecap="round"
              className="transition-all duration-150"
            />
          );
        })}

        {/* 21 Nodes */}
        {animatedLandmarks.map((node) => {
          const isTip = [4, 8, 12, 16, 20].includes(node.id);
          const isWrist = node.id === 0;
          const isHovered = hoveredNode === node.id;

          return (
            <g
              key={node.id}
              className="cursor-pointer"
              onMouseEnter={() => interactive && setHoveredNode(node.id)}
              onMouseLeave={() => interactive && setHoveredNode(null)}
            >
              {/* Outer pulsing ring for tips and wrist */}
              {(isTip || isWrist) && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="3.5"
                  fill="none"
                  stroke="#F5E642"
                  strokeWidth="0.4"
                  strokeOpacity="0.5"
                  className="animate-ping"
                />
              )}

              {/* Node core */}
              <circle
                cx={node.x}
                cy={node.y}
                r={isHovered ? "2.6" : isTip ? "2.0" : "1.4"}
                fill={isHovered ? "#FFFFFF" : "#F5E642"}
                stroke="#0B0B0B"
                strokeWidth="0.5"
                filter="url(#glowEffect)"
                className="transition-all duration-150"
              />

              {/* Landmark Index for hovered state */}
              {isHovered && (
                <text
                  x={node.x + 3}
                  y={node.y - 3}
                  fill="#F5E642"
                  fontSize="3"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  #{node.id} {node.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* Floating HUD Telemetry Badge */}
      <div className="absolute bottom-2 right-4 px-3 py-1.5 rounded-lg bg-surface-card/90 border border-surface-border backdrop-blur-md font-mono text-[11px] text-text-secondary flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
          <span className="text-text-primary">21 LANDMARKS</span>
        </div>
        <span className="text-surface-border">|</span>
        <span className="text-yellow-accent">TOPOLOGY OK</span>
      </div>
    </div>
  );
}

