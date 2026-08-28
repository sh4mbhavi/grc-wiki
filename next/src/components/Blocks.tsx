import { Fragment } from "react";

import type { Block } from "@/lib/content";
import { byClause, href } from "@/lib/content";

/* Row and column labels for FIG. 2, and the heat index per cell. Kept here
   rather than in the content, because the matrix is a piece of the design
   system: an author asks for it, they do not draw it. */
const MATRIX_ROWS = ["Almost certain", "Likely", "Possible", "Unlikely", "Rare"];
const MATRIX_COLS = ["Insignificant", "Minor", "Moderate", "Major", "Severe"];
const MATRIX_HEAT = [
    [4, 5, 6, 7, 8],
    [3, 4, 5, 6, 7],
    [2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5],
    [0, 1, 2, 3, 4],
];

const LOOP_NODES = [
    { name: "Governance", sub: "sets objectives & appetite", out: false },
    { name: "Risk", sub: "sizes & treats the threats", out: false },
    { name: "Assurance", sub: "board & customer reporting", out: true },
    { name: "Compliance", sub: "controls & kept evidence", out: false },
];

const LOOP_LABEL =
    "Governance sets objectives and appetite for Risk. Risk produces controls and evidence " +
    "held by Compliance. Compliance feeds Assurance, which reports back to Governance.";

type HtmlTag = "div" | "p" | "aside" | "span" | "figcaption" | "dd";

function Html({ html, as = "div", ...rest }: { html: string; as?: HtmlTag } & Record<string, unknown>) {
    const Tag = as as "div";
    return <Tag {...rest} dangerouslySetInnerHTML={{ __html: html }} />;
}

function aspect(ratio: string) {
    const [w, h] = ratio.split(":");
    return { aspectRatio: `${w}/${h}` } as const;
}

function LoopNode({ i }: { i: number }) {
    const node = LOOP_NODES[i];
    return (
        <div className={node.out ? "loop__node loop__node--out" : "loop__node"}>
            <b>{node.name}</b>
            <span>{node.sub}</span>
        </div>
    );
}

export function BlockView({ block }: { block: Block }) {
    switch (block.type) {
        case "prose":
            return <Html className="prose" html={block.html} />;

        case "lede":
            return <Html as="p" className="lede" html={block.html} />;

        case "note":
            return <Html as="aside" className="margin-note" html={block.html} />;

        case "heading":
            if (block.level !== 2) {
                return <h3 className="clause clause--sub" id={block.id}>{block.text}</h3>;
            }
            return (
                <h2 className="clause" id={block.id}>
                    <span className="u-vh" id={block.alias} />
                    <span className="clause__n">{block.clause}</span>
                    {block.text}
                    <a className="anchor" href={`#${block.id}`} aria-label="Link to this clause">#</a>
                </h2>
            );

        case "terms":
            return (
                <dl className="terms">
                    {block.items.map((item) => (
                        <Fragment key={item.term}>
                            <dt>{item.term}</dt>
                            <Html as="dd" html={item.html} />
                        </Fragment>
                    ))}
                </dl>
            );

        case "def": {
            const target = block.ref ? byClause(block.ref) : undefined;
            return (
                <div className="def">
                    <span className="def__label">DEFINITION · {block.term.toUpperCase()}</span>
                    <Html as="span" html={block.html} />
                    {target ? (
                        <>
                            {" "}
                            <a className="def__ref" href={href(target.url)}>→ {block.ref}</a>
                        </>
                    ) : null}
                </div>
            );
        }

        case "diagram":
            return (
                <figure className="figure" id={`fig-${block.n}`}>
                    <div className="figure__frame">
                        <div className="loop" role="img" aria-label={LOOP_LABEL}>
                            <LoopNode i={0} />
                            <div className="loop__edge loop__edge--h" aria-hidden="true">sets<br />———▸</div>
                            <LoopNode i={1} />
                            <div className="loop__edge loop__edge--v" aria-hidden="true">▴<br />reports</div>
                            <div />
                            <div className="loop__edge loop__edge--v" aria-hidden="true">produces<br />▾</div>
                            <LoopNode i={2} />
                            <div className="loop__edge loop__edge--h" aria-hidden="true">feeds<br />◂———</div>
                            <LoopNode i={3} />
                        </div>
                    </div>
                    <Html as="figcaption" html={block.caption} />
                </figure>
            );

        case "matrix": {
            const [markRow, markCol] = block.mark;
            return (
                <figure className="figure figure--wide" id={`fig-${block.n}`}>
                    <div className="scroll-x">
                        <table className="matrix">
                            <caption dangerouslySetInnerHTML={{ __html: block.caption }} />
                            <thead>
                                <tr>
                                    <td />
                                    {MATRIX_COLS.map((c) => <th key={c} scope="col">{c}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {MATRIX_ROWS.map((rowName, r) => (
                                    <tr key={rowName}>
                                        <th scope="row">{rowName}</th>
                                        {MATRIX_COLS.map((colName, c) => {
                                            const marked = markRow === r + 1 && markCol === c + 1;
                                            const label =
                                                `${rowName} likelihood, ${colName.toLowerCase()} impact` +
                                                (marked ? " — the worked example" : "");
                                            return (
                                                <td
                                                    key={colName}
                                                    data-heat={MATRIX_HEAT[r][c]}
                                                    data-mark={marked ? "true" : undefined}
                                                >
                                                    <span />
                                                    <span className="u-vh">{label}</span>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {block.note ? <Html as="figcaption" html={block.note} /> : null}
                </figure>
            );
        }

        case "slot":
            return (
                <figure className="figure" id={`fig-${block.n}`}>
                    {block.src ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                            src={href(block.src)}
                            alt={block.alt}
                            style={{ ...aspect(block.ratio), objectFit: "cover" }}
                        />
                    ) : (
                        <div className="slot" style={aspect(block.ratio)}>
                            <span>
                                IMAGE SLOT · {block.ratio}
                                <br />
                                {block.subject}
                            </span>
                        </div>
                    )}
                    <Html as="figcaption" html={block.caption} />
                </figure>
            );

        case "faq":
            return (
                <div className="faq">
                    {block.items.map((item, i) => (
                        <details key={item.id} id={item.id} open={i === 0}>
                            <summary>{item.q}</summary>
                            <Html className="faq__answer" html={item.html} />
                        </details>
                    ))}
                </div>
            );

        case "split":
            return (
                <div className="split" style={{ ["--split" as string]: block.ratio }}>
                    {block.columns.map((column, i) => (
                        <div key={i}>
                            <Blocks blocks={column} />
                        </div>
                    ))}
                </div>
            );
    }
}

export function Blocks({ blocks }: { blocks: Block[] }) {
    return (
        <>
            {blocks.map((block, i) => (
                <BlockView key={i} block={block} />
            ))}
        </>
    );
}
