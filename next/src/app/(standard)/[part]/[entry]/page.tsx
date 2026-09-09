import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Blocks, BlockView } from "@/components/Blocks";
import { Ld, Masthead } from "@/components/Chrome";
import { CorpusRail, PageRail } from "@/components/Rails";
import { byClause, editorial, entries, href, OG_IMAGE, partBySlug, parts } from "@/lib/content";

type Params = { part: string; entry: string };

export function generateStaticParams(): Params[] {
    return entries.map((e) => ({ part: e.part_slug, entry: e.slug }));
}

function find(params: Params) {
    return entries.find((e) => e.part_slug === params.part && e.slug === params.entry);
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
    const entry = find(await params);
    if (!entry) {
        return {};
    }
    return {
        title: entry.title,
        description: entry.description,
        keywords: entry.keywords,
        alternates: { canonical: entry.url },
        openGraph: {
            title: entry.title,
            description: entry.description,
            url: entry.url,
            type: "article",
            images: OG_IMAGE,
        },
    };
}

export default async function EntryPage({ params }: { params: Promise<Params> }) {
    const entry = find(await params);
    if (!entry) {
        notFound();
    }

    const part = parts.find((p) => p.n === entry.part)!;
    const blocks = entry.blocks;

    // The lede and the infobox share the opening grid; everything after runs
    // the full column. Mirrors render.py so both builds compose it the same.
    let rest = blocks;
    const lede = rest[0]?.type === "lede" ? rest[0] : null;
    if (lede) {
        rest = rest.slice(1);
    }
    const intro = [];
    while (rest[0]?.type === "prose") {
        intro.push(rest[0]);
        rest = rest.slice(1);
    }

    const prevEntry = entry.prev ? byClause(entry.prev.ref) : undefined;
    const nextEntry = entry.next ? byClause(entry.next.ref) : undefined;

    return (
        <>
            <Ld nodes={entry.ld} />
            <Masthead
                withDrawer
                crumbs={
                    <>
                        Part {part.n} / <a href={href(`/${part.slug}/`)}>{part.name}</a> / {entry.clause}
                    </>
                }
            />
            <div className="frame">
                <CorpusRail current={entry} />
                <PageRail entry={entry} />
                <main className="article" id="main" data-article="">
                    <article>
                        <div className="article__clause">{entry.clause}</div>
                        <h1 className="article__title">{entry.title}</h1>
                        <div className="article__meta">
                            <span>Reading {entry.reading_minutes} min</span>
                            <span>Cited by {entry.cited_by}</span>
                            <span>{entry.sources.length} sources</span>
                            {entry.reviewed || editorial.reviewed ? (
                                <span>
                                    Reviewed{" "}
                                    <time dateTime={entry.reviewed || editorial.reviewed}>
                                        {entry.reviewed || editorial.reviewed}
                                    </time>
                                </span>
                            ) : null}
                        </div>

                        <div className="article__opening">
                            <div className="article__body">
                                {lede ? <BlockView block={lede} /> : null}
                                <Blocks blocks={intro} />
                            </div>
                            {Object.keys(entry.quick_facts).length ? (
                                <div className="infobox">
                                    <div className="infobox__head">QUICK FACTS</div>
                                    <dl>
                                        {Object.entries(entry.quick_facts).map(([k, v]) => (
                                            <div key={k} style={{ display: "contents" }}>
                                                <dt>{k}</dt>
                                                <dd>{v}</dd>
                                            </div>
                                        ))}
                                    </dl>
                                </div>
                            ) : null}
                        </div>

                        <Blocks blocks={rest} />

                        {entry.sources.length ? (
                            <section className="sources" id="cite">
                                <h2>SOURCES</h2>
                                <ol>
                                    {entry.sources_html.map((s, i) => (
                                        <li key={i} dangerouslySetInnerHTML={{ __html: s }} />
                                    ))}
                                </ol>
                            </section>
                        ) : null}

                        {entry.prev || entry.next ? (
                            <nav className="pager" aria-label="Adjacent entries">
                                {entry.prev ? (
                                    prevEntry ? (
                                        <a href={href(prevEntry.url)}>
                                            ◂ {entry.prev.ref}&nbsp; {entry.prev.title}
                                        </a>
                                    ) : (
                                        <span className="pager__off">
                                            {entry.prev.ref} {entry.prev.title}
                                        </span>
                                    )
                                ) : <span />}
                                {entry.next ? (
                                    nextEntry ? (
                                        <a href={href(nextEntry.url)}>
                                            {entry.next.ref}&nbsp; {entry.next.title} ▸
                                        </a>
                                    ) : (
                                        <span className="pager__off">
                                            {entry.next.ref} {entry.next.title}
                                        </span>
                                    )
                                ) : <span />}
                            </nav>
                        ) : null}
                    </article>
                </main>
            </div>
        </>
    );
}
