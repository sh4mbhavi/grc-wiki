import type { Metadata } from "next";

import { Ld, Masthead } from "@/components/Chrome";
import {
    byClause,
    config,
    coverage,
    href,
    indexLd,
    indexTerms,
    parts,
    site,
    type IndexTerm,
} from "@/lib/content";

export const metadata: Metadata = {
    title: "Index of entries",
    description:
        `Every term in the ${site.name}, alphabetically, with the clause it belongs to. ` +
        `${indexTerms.length} headwords across ${parts.length} parts.`,
    alternates: { canonical: "/a-z/" },
};

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

const BROWSE_MODES: [string, string | null, boolean][] = [
    ["A-Z index", "/a-z/", true],
    ["By part", null, false],
    ["By framework", null, false],
    ["By artefact", null, false],
    ["By role", null, false],
    ["Recently revised", null, false],
];

// All off by default. This page is the crawl surface; shipping it pre-filtered
// would hide most of the corpus from the first render.
const FILTERS: [string, string][] = [
    ["level", "Entry-level explanations"],
    ["example", "Has worked example"],
    ["template", "Has downloadable template"],
    ["fresh", "Revised in last 90 days"],
];

function Term({ term }: { term: IndexTerm }) {
    const headword = term.key ? <b>{term.t}</b> : term.t;
    const mark = term.example ? (
        <>
            {" "}
            <span className="idx__mark" title="Has a worked example">▪</span>
        </>
    ) : null;

    return (
        <span className="idx__term" data-live={term.url ? "true" : "false"}>
            <span className="idx__head">
                {term.url ? <a href={href(term.url)}>{headword}</a> : headword}
                {mark}
            </span>
            <span className="idx__ref">{term.ref}</span>
        </span>
    );
}

export default function IndexPage() {
    const groups = new Map<string, IndexTerm[]>();
    for (const term of indexTerms) {
        const letter = term.t[0].toUpperCase();
        groups.set(letter, [...(groups.get(letter) ?? []), term]);
    }
    const letters = [...groups.keys()].sort();
    const examplesTotal = indexTerms.filter((t) => t.example).length;

    return (
        <>
            <Ld nodes={indexLd} />
            <Masthead withDrawer crumbs="Index / A-Z" />
            <div className="frame">
                <nav className="rail rail--corpus" id="corpus" data-drawer="" aria-label="Browse the index">
                    <div className="rail__label">BROWSE BY</div>
                    <ul className="browse">
                        {BROWSE_MODES.map(([label, url, current]) => (
                            <li key={label}>
                                {url ? (
                                    <a href={href(url)} aria-current={current ? "page" : undefined}>{label}</a>
                                ) : (
                                    <span>{label}</span>
                                )}
                            </li>
                        ))}
                    </ul>

                    <div className="rail__label" style={{ marginTop: "var(--s-5)" }}>FILTERS</div>
                    <ul className="filters" data-index-filters="">
                        {FILTERS.map(([key, label]) => (
                            <li key={key}>
                                <label>
                                    <input type="checkbox" data-index-filter="" value={key} />
                                    {label}
                                </label>
                            </li>
                        ))}
                    </ul>

                    <div className="rail__related">
                        <span className="rail__heading">COVERAGE</span>
                        {coverage.map((line, i) => (
                            <span key={i} dangerouslySetInnerHTML={{ __html: line + "<br>" }} />
                        ))}
                    </div>
                </nav>

                <aside className="rail rail--page" data-page-rail="" aria-label="Index tools">
                    <details open>
                        <summary>JUMP TO LETTER</summary>
                        <div className="rail__label">JUMP TO LETTER</div>
                        <nav
                            className="strip"
                            style={{ border: 0, padding: 0, margin: 0 }}
                            aria-label="Jump to letter"
                        >
                            {ALPHABET.map((letter) =>
                                groups.has(letter) ? (
                                    <a key={letter} href={`#letter-${letter}`}>{letter}</a>
                                ) : (
                                    <span key={letter} data-off="true">{letter}</span>
                                ),
                            )}
                        </nav>

                        <div className="rail__block">
                            <span className="rail__heading">MOST LOOKED UP</span>
                            <ul>
                                {config.home.most_cited
                                    .filter((c) => byClause(c.ref))
                                    .map((c) => (
                                        <li key={c.ref}>
                                            <a href={href(byClause(c.ref)!.url)}>{c.title}</a>
                                        </li>
                                    ))}
                            </ul>
                        </div>

                        <div className="rail__block">
                            <span className="rail__heading">EXPORT</span>
                            <ul>
                                <li><a href={href("/a-z/index.csv")} download>Term list (CSV)</a></li>
                                <li><a href="javascript:window.print()">Full index (PDF)</a></li>
                            </ul>
                        </div>

                        <p className="margin-note" style={{ marginTop: "var(--s-5)", fontSize: "var(--t-small)" }}>
                            {examplesTotal} headwords carry a worked example, marked with a ▪ and worked
                            through in full in the entry that owns them.
                        </p>
                    </details>
                </aside>

                <main className="idx" id="main">
                    <h1 className="idx__title">Index of entries</h1>
                    <p className="idx__intro">
                        Every term in the reference, alphabetically. <b>Bold</b> entries are the ones
                        most people arrive looking for; a <span className="idx__mark">▪</span> marks an
                        entry with a worked example. Terms in grey are commissioned and not yet
                        published - the clause number is where they will live.
                    </p>

                    <nav className="strip" aria-label="Letters in use">
                        {ALPHABET.map((letter) =>
                            groups.has(letter) ? (
                                <a key={letter} href={`#letter-${letter}`}>{letter}</a>
                            ) : (
                                <span key={letter} data-off="true" aria-hidden="true">{letter}</span>
                            ),
                        )}
                        <span className="strip__count">{groups.size} letters in use</span>
                    </nav>

                    <div className="idx__cols" data-index="">
                        {letters.map((letter) => (
                            <section className="idx__group" data-letter={letter} key={letter}>
                                <h2 className="idx__letter" id={`letter-${letter}`}>{letter}</h2>
                                <ul className="idx__terms">
                                    {groups.get(letter)!.map((term) => (
                                        <li key={term.t} data-flags={term.flags}>
                                            <Term term={term} />
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        ))}
                    </div>

                    <div className="idx__foot">
                        <span data-index-count="">
                            Showing {indexTerms.length} of {indexTerms.length}
                        </span>
                        <span>
                            <a href={href("/a-z/index.csv")} download>Download the term list ▸</a>
                        </span>
                    </div>
                </main>
            </div>
        </>
    );
}
