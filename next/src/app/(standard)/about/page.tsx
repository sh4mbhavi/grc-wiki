import type { Metadata } from "next";

import { Ld, Masthead } from "@/components/Chrome";
import { pages, siteLd } from "@/lib/content";

export const metadata: Metadata = {
    title: "About",
    description: pages.about_description,
    alternates: { canonical: "/about/" },
    openGraph: { title: "About - GRC Wiki", description: pages.about_description, url: "/about/" },
};

export default function About() {
    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead crumbs="About" />
            <main
                className="index-page"
                id="main"
                style={{ maxWidth: 760 }}
                dangerouslySetInnerHTML={{ __html: pages.about }}
            />
        </>
    );
}
