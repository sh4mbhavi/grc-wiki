import type { Entry } from "@/lib/content";
import { byClause, entriesInPart, href, navTitle, parts } from "@/lib/content";

export function CorpusRail({ current }: { current: Entry | null }) {
    const related = current
        ? current.related.map(byClause).filter((e): e is Entry => Boolean(e))
        : [];

    return (
        <nav
            className="rail rail--corpus"
            id="corpus"
            data-drawer=""
            aria-label="Contents of the reference"
        >
            <div className="rail__label">CONTENTS OF THE REFERENCE</div>
            <ul className="tree">
                {parts.map((part) => {
                    const expanded = current !== null && current.part === part.n;
                    return (
                        <li key={part.slug}>
                            <a className="tree__part" href={href(`/${part.slug}/`)}>
                                {part.n} · {part.name.toUpperCase()}
                                <span className="tree__count">{part.count}</span>
                            </a>
                            {expanded ? (
                                <ul className="tree__pages">
                                    {entriesInPart(part.n).map((page) => (
                                        <li key={page.clause}>
                                            <a
                                                className="tree__page"
                                                href={href(page.url)}
                                                aria-current={page.clause === current!.clause ? "page" : undefined}
                                                data-entry-link=""
                                            >
                                                <span className="tree__n">{page.clause}</span>{" "}
                                                {navTitle(page)}
                                                <span className="u-vh" data-read-flag="" />
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            ) : null}
                        </li>
                    );
                })}
            </ul>

            {related.length ? (
                <div className="rail__related">
                    <span className="rail__heading">RELATED ENTRIES</span>
                    <ul>
                        {related.map((entry) => (
                            <li key={entry.clause}>
                                <a href={href(entry.url)}>{navTitle(entry)}</a>
                            </li>
                        ))}
                    </ul>
                </div>
            ) : null}
        </nav>
    );
}

export function PageRail({ entry }: { entry: Entry }) {
    const figures = Array.from({ length: entry.figure_count }, (_, i) => i + 1);

    return (
        <aside className="rail rail--page" data-page-rail="" aria-label="On this page">
            <details open>
                <summary>ON THIS PAGE</summary>
                <div className="rail__label">ON THIS PAGE</div>
                <ul className="toc" data-toc="">
                    <li data-for="" data-active="true" data-depth="2">
                        <a href="#main">{entry.clause} {navTitle(entry)}</a>
                    </li>
                    {entry.sections.map((section) => (
                        <li key={section.id} data-for={section.id} data-active="false">
                            <a href={`#${section.id}`}>{section.clause} {section.text}</a>
                        </li>
                    ))}
                </ul>

                <div className="rail__block">
                    <dl>
                        <dt>read</dt>
                        <dd data-progress-pct="">0%</dd>
                    </dl>
                    <div
                        className="progress"
                        role="progressbar"
                        aria-label="How much of this entry you have read"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={0}
                    >
                        <div className="progress__fill" data-progress="" />
                    </div>
                    <dl>
                        <dt>figures</dt><dd>{entry.figure_count}</dd>
                        <dt>sources</dt><dd>{entry.sources.length}</dd>
                    </dl>
                </div>

                {figures.length ? (
                    <div className="rail__block">
                        <span className="rail__heading">FIGURES</span>
                        <ul className="rail__figs">
                            {figures.map((n) => (
                                <li key={n}><a href={`#fig-${n}`}>{n}</a></li>
                            ))}
                        </ul>
                    </div>
                ) : null}

                <div className="rail__block">
                    <span className="rail__heading">TOOLS</span>
                    <ul>
                        <li><a href="#cite">Cite this page</a></li>
                    </ul>
                </div>
            </details>
        </aside>
    );
}
