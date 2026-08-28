import type { Metadata } from "next";

import { Ld, Masthead } from "@/components/Chrome";
import { pages, siteLd } from "@/lib/content";

export const metadata: Metadata = {
    title: "Suggest an edit",
    description: "How to report an error in the GRC Reference.",
    alternates: { canonical: "/suggest-an-edit/" },
};

export default function Suggest() {
    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead crumbs="Suggest an edit" />
            <main
                className="index-page"
                id="main"
                style={{ maxWidth: 760 }}
                dangerouslySetInnerHTML={{ __html: pages.suggest }}
            />
        </>
    );
}
