/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT_STANDALONE ? "standalone" : undefined,
  reactStrictMode: true,
  transpilePackages: ["@zenglow/types"],
  eslint: {
    ignoreDuringBuilds: true,
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

