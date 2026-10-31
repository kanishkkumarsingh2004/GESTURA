import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GESTURA — Intelligent Gesture Recognition & Translation",
  description:
    "Breaking communication barriers through intelligent vision-based gesture recognition and real-time audio synthesis.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-text-primary font-sans antialiased selection:bg-yellow-accent selection:text-background min-h-screen">
        {children}
      </body>
    </html>
  );
}
