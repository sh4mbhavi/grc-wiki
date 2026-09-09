import type { MetadataRoute } from "next";

/* Required by output: "export" - the file is written once at build time. */
export const dynamic = "force-static";

import { absolute, entries, livePartsOnly } from "@/lib/content";

/* Static export writes this to /sitemap.xml at build time. */
export default function sitemap(): MetadataRoute.Sitemap {
    const now = new Date();
    return [
        { url: absolute("/"), lastModified: now, changeFrequency: "weekly", priority: 1 },
        { url: absolute("/a-z/"), lastModified: now, changeFrequency: "weekly", priority: 0.8 },
        { url: absolute("/about/"), lastModified: now, changeFrequency: "yearly", priority: 0.5 },
        ...livePartsOnly().map((part) => ({
            url: absolute(`/${part.slug}/`),
            lastModified: now,
            changeFrequency: "monthly" as const,
            priority: 0.7,
        })),
        ...entries.map((entry) => ({
            url: absolute(entry.url),
            lastModified: now,
            changeFrequency: "monthly" as const,
            priority: entry.canonical_entry ? 0.9 : 0.6,
        })),
    ];
}
