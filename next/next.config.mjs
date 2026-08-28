import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Deploy target comes from content/site.yml, not from a second source of
   truth. A repo-scoped GitHub Pages URL sets base_path there; a root domain
   or a Vercel project leaves it at "/". */
const bundle = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), "src/content/bundle.json"), "utf8"));
const basePath = (bundle.site.site.base_path || "/").replace(/\/$/, "");

/** @type {import('next').NextConfig} */
export default {
    output: "export",
    trailingSlash: true,
    basePath: basePath || undefined,
    images: { unoptimized: true },
    env: { NEXT_PUBLIC_BASE: bundle.site.site.base_path || "/" },
};
