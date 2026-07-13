/** @type {import('next').NextConfig} */
const nextConfig = {
  // Produce a self-contained server bundle — required for the lean production Docker image.
  // This outputs node_modules inline so the final image only needs `node server.js`.
  output: "standalone",
};

export default nextConfig;
