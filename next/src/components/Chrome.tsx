import type { ReactNode } from "react";

import { config, href, parts, site } from "@/lib/content";

const SearchIcon = () => (
    <svg
        className="icon-search"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        aria-hidden="true"
    >
        <circle cx="7" cy="7" r="4.5" />
        <path d="M10.4 10.4 14 14" />
    </svg>
);

export function Masthead({ crumbs, withDrawer = false }: { crumbs?: ReactNode; withDrawer?: boolean }) {
    return (
        <header className="masthead">
            {withDrawer ? (
                <button
                    className="masthead__drawer-btn"
                    type="button"
                    data-drawer-btn=""
                    aria-expanded="false"
                    aria-controls="corpus"
                >
                    Contents
                </button>
            ) : null}
            <a className="masthead__wordmark" href={href("/")}>GRC WIKI</a>
            <span className="masthead__sep" aria-hidden="true">|</span>
            <span className="masthead__crumbs">
                {crumbs ?? `${site.entries_total} entries · ${site.parts_total} parts · open access`}
            </span>
            <div className="masthead__tail">
                <button className="masthead__search" type="button" data-finder-open="">
                    Search&nbsp;&nbsp;⌘K
                </button>
                <button
                    className="theme-toggle"
                    type="button"
                    data-theme-toggle=""
                    aria-label="Switch colour mode"
                >
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden="true">
                        <circle cx="8" cy="8" r="3.2" />
                        <path d="M8 1v1.6M8 13.4V15M15 8h-1.6M2.6 8H1M12.9 3.1l-1.1 1.1M4.2 11.8l-1.1 1.1M12.9 12.9l-1.1-1.1M4.2 4.2 3.1 3.1" />
                    </svg>
                    <span data-theme-label="">dark</span>
                </button>
            </div>
        </header>
    );
}

export function Finder() {
    return (
        <dialog className="finder" data-finder="" aria-label="Search the reference">
            <div className="finder__bar">
                <span className="finder__icon"><SearchIcon /></span>
                <label className="u-vh" htmlFor="finder-input">
                    Search {site.entries_total} entries
                </label>
                <input
                    className="finder__input"
                    id="finder-input"
                    type="search"
                    autoComplete="off"
                    spellCheck={false}
                    placeholder="Search a term, a framework, or a question…"
                    data-finder-input=""
                />
                <span className="finder__esc">esc</span>
            </div>
            <ul className="finder__results" data-finder-results="" />
            <p className="finder__empty" data-finder-empty="">
                Type to search entries, clauses and definitions.
            </p>
            <div className="finder__foot">
                <span>↑↓ move</span>
                <span>↵ open</span>
                <span>esc close</span>
            </div>
        </dialog>
    );
}

export function Colophon() {
    return (
        <footer className="colophon">
            <div>
                <h2>THE REFERENCE</h2>
                <ul>
                    {parts.map((p) => (
                        <li key={p.slug}>
                            <a href={href(`/${p.slug}/`)}>{p.n} · {p.name}</a>
                        </li>
                    ))}
                </ul>
            </div>
            <div>
                <h2>RESOURCES</h2>
                <ul>
                    <li><a href={href("/a-z/")}>A–Z index</a></li>
                </ul>
            </div>
        </footer>
    );
}

export function SearchBar() {
    return (
        <button className="searchbar" type="button" data-finder-open="">
            <span className="searchbar__icon"><SearchIcon /></span>
            <span className="searchbar__label">Search a term, a framework, or a question…</span>
            <span className="searchbar__key" aria-hidden="true">⌘K</span>
        </button>
    );
}

export function Ld({ nodes }: { nodes: Record<string, unknown>[] }) {
    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{
                __html: JSON.stringify({ "@context": "https://schema.org", "@graph": nodes }),
            }}
        />
    );
}

export const siteName = config.site.name;
