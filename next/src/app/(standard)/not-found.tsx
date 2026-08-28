import { Masthead } from "@/components/Chrome";
import { pages } from "@/lib/content";

export default function NotFound() {
    return (
        <>
            <Masthead crumbs="Not found" />
            <main
                className="index-page"
                id="main"
                style={{ maxWidth: 760 }}
                dangerouslySetInnerHTML={{ __html: pages.not_found }}
            />
        </>
    );
}
