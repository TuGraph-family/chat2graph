import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  images: {
    unoptimized: true, // 禁用图片优化
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'github.com',
      },
      {
        protocol: 'https',
        hostname: 'shields.io',
      },
      {
        protocol: 'https',
        hostname: 'badgen.net',
      },
    ],
  },
};

export default withMDX(config);
