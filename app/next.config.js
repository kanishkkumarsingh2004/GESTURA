/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.BACK_END_url ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL;

if (!backendUrl) {
  console.warn(
    "[next.config.js] Warning: No backend URL configured in environment (BACK_END_url / NEXT_PUBLIC_BACKEND_URL / NEXT_PUBLIC_API_URL). API proxying will not work."
  );
}

const cleanBackendUrl = backendUrl ? backendUrl.replace(/\/+$/, "") : "";

const nextConfig = {
  reactStrictMode: true,
  env: {
    BACK_END_url: cleanBackendUrl,
    NEXT_PUBLIC_BACKEND_URL: cleanBackendUrl,
    NEXT_PUBLIC_API_URL: cleanBackendUrl,
  },
  async rewrites() {
    if (!cleanBackendUrl) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${cleanBackendUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
