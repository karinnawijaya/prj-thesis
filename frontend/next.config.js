/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/compare/:path*",
        destination: "http://localhost:8000/api/compare/:path*",
      },
      {
        source: "/api/compare",
        destination: "http://localhost:8000/api/compare",
      },
    ];
  },
  webpack: (config) => {
    config.resolveLoader = {
      ...config.resolveLoader,
      modules: [
        "node_modules",
        "node_modules/next/dist/build/webpack/loaders",
        ...(config.resolveLoader?.modules ?? []),
      ],
    };
    return config;
  },
};

module.exports = nextConfig;
