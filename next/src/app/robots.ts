import type { MetadataRoute } from "next";

/* Required by output: "export" — the file is written once at build time. */
export const dynamic = "force-static";

import { absolute } from "@/lib/content";

export default function robots(): MetadataRoute.Robots {
    return {
        rules: { userAgent: "*", allow: "/" },
        sitemap: absolute("/sitemap.xml"),
    };
}
