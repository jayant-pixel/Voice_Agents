import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  turbopack: {
    // Fix workspace root detection - use explicit project path
    root: "C:\\Users\\lbabu\\Voice AI Template",
  },
};

export default nextConfig;
