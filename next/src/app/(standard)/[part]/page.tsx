import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Ld, Masthead } from "@/components/Chrome";
import { CorpusRail } from "@/components/Rails";
import { entriesInPart, href, livePartsOnly, partBySlug, siteLd } from "@/lib/content";

type Params = { part: string };

export function generateStaticParams(): Params[] {
    return livePartsOnly().map((p) => ({ part: p.slug }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
    const part = partBySlug((await params).part);
    if (!part) {
        return {};
    }
    return {
        title: part.name,
        description: part.blurb,
        alternates: { canonical: `/${part.slug}/` },
    };
}

export default async function PartPage({ params }: { params: Promise<Params> }) {
    const part = partBySlug((await params).part);
    if (!part) {
        notFound();
    }

    const list = entriesInPart(part.n);

    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead withDrawer crumbs={`Part ${part.n} / ${part.name}`} />
            <div className="frame">
                <CorpusRail current={list[0] ?? null} />
                <main className="article" id="main" style={{ gridColumn: "2 / span 2" }}>
                    <div className="article__clause">PART {part.n}</div>
                    <h1 className="article__title">{part.name}</h1>
                    <p className="lede" style={{ maxWidth: "56ch" }}>{part.blurb}</p>
                    <div className="article__meta">
                        <span>{list.length} published</span>
                        <span>{part.count} planned</span>
                    </div>
                    <div className="start" style={{ gridTemplateColumns: "44px minmax(0,1fr)" }}>
                        {list.map((entry) => (
                            <div key={entry.clause} style={{ display: "contents" }}>
                                <span className="start__n">{entry.clause}</span>
                                <span className="start__item">
                                    <a href={href(entry.url)}>{entry.title}</a>
                                    <span className="start__time"> · {entry.reading_minutes} min</span>
                                    <span
                                        style={{
                                            display: "block",
                                            fontSize: "var(--t-small)",
                                            color: "var(--ink-quiet)",
                                        }}
                                    >
                                        {entry.description}
                                    </span>
                                </span>
                            </div>
                        ))}
                    </div>
                </main>
            </div>
        </>
    );
}
