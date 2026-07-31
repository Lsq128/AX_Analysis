import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const apiUrl = process.env.API_PROXY_URL || "http://localhost:8000";
    // Note: /api/v1/analyses/:id/events is implemented as a Route Handler so SSE
    // is not buffered by this rewrite proxy.
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
