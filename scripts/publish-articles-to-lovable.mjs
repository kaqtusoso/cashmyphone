import { copyFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const lovableRepo = process.env.LOVABLE_REPO || "/private/tmp/televera-lovable-repo";

const filesToSync = [
  "package.json",
  "src/data/article-summaries.ts",
  "src/pages/ArticlePage.tsx",
  "src/pages/ArticlesListPage.tsx",
  "public/sitemap.xml",
  "scripts/generate-sitemap.mjs",
  "scripts/publish-articles-to-lovable.mjs",
];

const run = (command, args, options = {}) => {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    encoding: "utf8",
    stdio: options.capture ? "pipe" : "inherit",
  });

  if (result.status !== 0) {
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${command} ${args.join(" ")} failed${output ? `:\n${output}` : ""}`);
  }

  return result.stdout || "";
};

if (!existsSync(resolve(lovableRepo, ".git"))) {
  throw new Error(`Lovable repo not found at ${lovableRepo}`);
}

run("npm", ["run", "sitemap"]);
run("npm", ["run", "build"]);

for (const file of filesToSync) {
  const source = resolve(root, file);
  const target = resolve(lovableRepo, file);
  if (!existsSync(source)) throw new Error(`Missing source file: ${file}`);
  if (!existsSync(dirname(target))) throw new Error(`Missing target directory for: ${file}`);
  copyFileSync(source, target);
}

run("git", ["add", ...filesToSync], { cwd: lovableRepo });

const staged = run("git", ["diff", "--cached", "--name-only"], {
  cwd: lovableRepo,
  capture: true,
})
  .trim()
  .split("\n")
  .filter(Boolean);

if (staged.length === 0) {
  console.log("No article changes to publish.");
  process.exit(0);
}

const date = new Date().toISOString().slice(0, 10);
run("git", ["commit", "-m", `Publish Televera article update ${date}`], { cwd: lovableRepo });
run("git", ["push", "origin", "HEAD:main"], { cwd: lovableRepo });

console.log(`Published article update to Lovable from ${lovableRepo}.`);
