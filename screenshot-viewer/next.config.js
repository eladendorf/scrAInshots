/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove 'output: export' to allow dynamic API routes
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig