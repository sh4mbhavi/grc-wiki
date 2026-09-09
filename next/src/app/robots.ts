import type { MetadataRoute } from "next";

/* Required by output: "export" - the file is written once at build time. */
export const dynamic = "force-static";

import { absolute } from "@/lib/content";

/* AI answer engines only cite pages their crawlers are allowed to fetch. These
   are named explicitly so a future host-level default block does not quietly
   exclude the reference from AI search. */
const AI_CRAWLERS = [
    "GPTBot",
    "ChatGPT-User",
    "OAI-SearchBot",
    "ClaudeBot",
    "Claude-User",
    "Claude-SearchBot",
    "anthropic-ai",
    "PerplexityBot",
    "Perplexity-User",
    "Google-Extended",
    "Applebot-Extended",
    "meta-externalagent",
    "CCBot",
    "Bytespider",
    "Amazonbot",
    "cohere-ai",
    "Diffbot",
];

export default function robots(): MetadataRoute.Robots {
    return {
        rules: [
            { userAgent: "*", allow: "/" },
            { userAgent: AI_CRAWLERS, allow: "/" },
        ],
        sitemap: absolute("/sitemap.xml"),
    };
}
