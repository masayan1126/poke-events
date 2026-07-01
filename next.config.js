const isGithubPages = process.env.GITHUB_PAGES === "true";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: isGithubPages ? "/poke-events" : "",
  assetPrefix: isGithubPages ? "/poke-events/" : "",
  images: {
    unoptimized: true
  }
};

module.exports = nextConfig;
