import type { Metadata } from "next";

import { Ld, Masthead, SearchBar } from "@/components/Chrome";
import {
    byClause,
    editorial,
    entries,
    home,
    href,
    parts,
    publisher,
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
    const revised = [...entries].sort((a, b) => b.reviewed.localeCompare(a.reviewed)).slice(0, 3);
    const [w, h] = home.image_slot.ratio.split(":");

    return (
        <>
            <Ld nodes={siteLd} />
            <Masthead />
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
                                        <span className="part__count">{part.count} entries</span>
                                    </span>
                                    <span className="part__blurb">{part.blurb}</span>
                                </a>
                            ))}
                        </div>

                        <div className="home__row">
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
                            <figure className="figure" style={{ margin: 0 }}>
                                <div className="slot" style={{ aspectRatio: `${w}/${h}` }}>
                                    <span>
                                        IMAGE SLOT · {home.image_slot.ratio}
                                        <br />
                                        {home.image_slot.subject}
                                    </span>
                                </div>
                                <figcaption>FIG. — {home.image_slot.caption}</figcaption>
                            </figure>
                        </div>
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

                        <h2 className="section-rule" style={{ marginTop: "var(--s-8)" }}>
                            RECENTLY REVISED
                        </h2>
                        <ul className="revised">
                            {revised.map((entry) => (
                                <li key={entry.clause}>
                                    <a href={href(entry.url)}>{entry.title}</a>
                                    <span>{entry.reviewed} · ed. {entry.edition}</span>
                                </li>
                            ))}
                        </ul>

                        <div className="policy">
                            <b>{home.maintenance.label}</b>
                            {home.maintenance.body}
                            <span style={{ display: "block", marginTop: "var(--s-2)" }}>
                                <a href={href(editorial.policy_url)}>Read the editorial policy</a>
                            </span>
                        </div>

                        <p className="margin-note" style={{ marginTop: "var(--s-5)" }}>
                            Maintained by the team behind{" "}
                            <a href={publisher.url} rel="noopener">{publisher.name}</a>, who teach the
                            same material as a course.
                        </p>
                    </aside>
                </div>
            </main>
        </>
    );
}
