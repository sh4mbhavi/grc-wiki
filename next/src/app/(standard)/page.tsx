import type { Metadata } from "next";

import { HomeDrawer, Ld, Masthead, SearchBar } from "@/components/Chrome";
import {
    byClause,
    editorial,
    entriesInPart,
    home,
    href,
    navTitle,
    parts,
    site,
    siteLd,
} from "@/lib/content";

export const metadata: Metadata = {
    title: home.title,
    description: site.description,
    keywords: home.chips,
    alternates: { canonical: "/" },
    openGraph: { title: `${home.title} — ${site.name}`, description: site.description, url: "/" },
};

export default function Home() {
    const startHere = home.start_here.map(byClause).filter(Boolean);
    const cited = home.most_cited.filter((c) => byClause(c.ref));

    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead home />
            <HomeDrawer />
            <main id="main">
                <section className="portal">
                    <div className="portal__inner">
                        <p className="portal__standfirst">{editorial.standfirst}</p>
                        <h1 className="portal__title">{home.title}</h1>
                        <p className="portal__blurb">{home.blurb}</p>
                        <SearchBar />
                        <div className="chips">
                            {home.chips.map((chip) => (
                                <button
                                    key={chip}
                                    className="chip"
                                    type="button"
                                    data-finder-open=""
                                    data-seed={chip}
                                >
                                    {chip}
                                </button>
                            ))}
                        </div>
                    </div>
                </section>

                <div className="home">
                    <div className="home__main">
                        <h2 className="section-rule">THE REFERENCE · SIX PARTS</h2>
                        <div className="parts">
                            {parts.map((part) => (
                                <a key={part.slug} className="part" href={href(`/${part.slug}/`)}>
                                    <span className="part__head">
                                        <span className="part__n">{part.n}</span>
                                        <span className="part__name">{part.name}</span>
                                        <span className="part__count">{part.published} entries</span>
                                    </span>
                                    <span className="part__blurb">{part.blurb}</span>
                                </a>
                            ))}
                        </div>

                        <section>
                            <h2 className="section-rule">START HERE — IF YOU ARE NEW</h2>
                            <div className="start">
                                {startHere.map((entry, i) => (
                                    <div key={entry!.clause} style={{ display: "contents" }}>
                                        <span className="start__n">{String(i + 1).padStart(2, "0")}</span>
                                        <span className="start__item">
                                            <a href={href(entry!.url)}>{entry!.title}</a>
                                            <span className="start__time"> · {entry!.reading_minutes} min</span>
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section className="sitemap">
                            <h2 className="section-rule">BROWSE EVERY ENTRY</h2>
                            <div className="sitemap__grid">
                                {parts.map((part) => (
                                    <div className="sitemap__col" key={part.slug}>
                                        <a className="sitemap__part" href={href(`/${part.slug}/`)}>
                                            {part.n} · {part.name.toUpperCase()}
                                        </a>
                                        <ul>
                                            {entriesInPart(part.n).map((page) => (
                                                <li key={page.clause}>
                                                    <a href={href(page.url)}>
                                                        <span className="sitemap__n">{page.clause}</span> {navTitle(page)}
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>

                    <aside className="home__aside">
                        <h2 className="section-rule">MOST CITED</h2>
                        <div className="cited">
                            <ul>
                                {cited.map((c) => (
                                    <li key={c.ref}>
                                        <a href={href(byClause(c.ref)!.url)}>{c.title}</a>
                                        <span className="cited__n">{c.count}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <a className="aside-card" href={href("/a-z/")}>
                            <b>A–Z INDEX</b>
                            <span>Every term, alphabetically, with the clause it belongs to.</span>
                        </a>
                        <a className="aside-card" href={href("/career/how-to-learn-grc/")}>
                            <b>NEW TO GRC?</b>
                            <span>Start with the from-scratch learning path.</span>
                        </a>
                    </aside>
                </div>
            </main>
        </>
    );
}
