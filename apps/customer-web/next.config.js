/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT_STANDALONE ? "standalone" : undefined,
  reactStrictMode: true,
  transpilePackages: ["@zenglow/types", "@zenglow/config", "@tanstack/react-query"],
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: (process.env.BACKEND_API_URL || "http://localhost:8000/api/v1") + "/:path*",
      },
    ];
  },
};

module.exports = nextConfig;

