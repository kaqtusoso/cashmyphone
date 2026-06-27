import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const SITE_URL = "https://televera.se";

const root = process.cwd();
const today = new Date().toISOString().slice(0, 10);

const modelToSlug = (model) =>
  model
    .toLowerCase()
    .replace(/[()]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");

const readText = (path) => readFileSync(resolve(root, path), "utf8");

const parseIphoneModels = () => {
  const source = readText("src/data/iphoneCatalog.ts");
  const match = source.match(/export const iphoneModels = \[([\s\S]*?)\];/);
  if (!match) throw new Error("Could not find iphoneModels in src/data/iphoneCatalog.ts");

  return [...match[1].matchAll(/"([^"]+)"/g)].map((item) => item[1]);
};

const parseArticleSlugs = () => {
  const source = readText("src/data/article-summaries.ts");
  return [...source.matchAll(/slug:\s*"([^"]+)"/g)].map((item) => item[1]);
};

const routes = [
  { path: "/", priority: "1.0", changefreq: "daily" },
  { path: "/salja-iphone", priority: "0.9", changefreq: "weekly" },
  { path: "/artiklar", priority: "0.7", changefreq: "weekly" },
  { path: "/om-oss", priority: "0.5", changefreq: "monthly" },
  { path: "/villkor", priority: "0.3", changefreq: "yearly" },
  { path: "/integritet", priority: "0.3", changefreq: "yearly" },
  { path: "/cookies", priority: "0.3", changefreq: "yearly" },
  ...parseIphoneModels().map((model) => ({
    path: `/salja/${modelToSlug(model)}`,
    priority: "0.8",
    changefreq: "daily",
  })),
  ...parseArticleSlugs().map((slug) => ({
    path: `/artikel/${slug}`,
    priority: "0.6",
    changefreq: "monthly",
  })),
];

const seen = new Set();
const uniqueRoutes = routes.filter((route) => {
  if (seen.has(route.path)) return false;
  seen.add(route.path);
  return true;
});

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${uniqueRoutes
  .map(
    (route) => `  <url>
    <loc>${SITE_URL}${route.path === "/" ? "" : route.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${route.changefreq}</changefreq>
    <priority>${route.priority}</priority>
  </url>`,
  )
  .join("\n")}
</urlset>
`;

writeFileSync(resolve(root, "public/sitemap.xml"), xml);
console.log(`Generated public/sitemap.xml with ${uniqueRoutes.length} URLs.`);
