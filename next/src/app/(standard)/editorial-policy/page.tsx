import type { Metadata } from "next";

import { Ld, Masthead } from "@/components/Chrome";
import { pages, siteLd } from "@/lib/content";

export const metadata: Metadata = {
    title: "Editorial policy",
    description:
        "Who writes this reference, how it is reviewed, and how corrections are handled.",
    alternates: { canonical: "/editorial-policy/" },
};

export default function EditorialPolicy() {
    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead crumbs="Editorial policy" />
            <main
                className="index-page"
                id="main"
                style={{ maxWidth: 760 }}
                dangerouslySetInnerHTML={{ __html: pages.editorial_policy }}
            />
        </>
    );
}
