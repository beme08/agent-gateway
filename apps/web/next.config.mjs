/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  serverActions: { bodySizeLimit: "2mb" },
};
export default nextConfig;
