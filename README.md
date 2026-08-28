# GRC Reference

A standalone encyclopedic reference on governance, risk and compliance, built
from the Claude Design handoff.

Direction **1a / 2a** — the editorial serif shell — carried through every page
type the handoff specified:

| | Page type | URL |
| --- | --- | --- |
| **3a** | Home — search-first portal | `/` |
| **3b** | Full entry — figures, diagrams, table, FAQ | `/foundations/what-grc-is/` |
| **3c** | A–Z index — browse, filter, export | `/a-z/` |
| — | Part page | `/foundations/` |
| — | Comparison entry | `/foundations/grc-vs-internal-audit/` |

The 2c "lanes" direction was built and then removed once the client chose the
serif world. Its one genuinely distinct idea — the verdict-and-attribute-table
treatment for "X vs Y" pages — was kept and rebuilt in the editorial style as
the `:::versus` and `:::attrs` directives, because "X vs Y" is the highest-intent
query type in the set.

Two renderers, one content pipeline:

| | Output | Deploy |
| --- | --- | --- |
| **Static** | `dist/` — plain HTML, one stylesheet, one script | GitHub Pages (workflow included) |
| **Next.js** | `next/out/` — App Router, `output: "export"` | Vercel, or any static host |

Both read the same `content/`, the same stylesheet and the same behaviour
script. Neither parses markdown twice. Verified after every change: 37 identical
page URLs, identical JSON-LD.

## Quick start

```sh
make setup        # venv + npm install
make serve        # static build on http://localhost:8000
make next-dev     # Next.js dev server
```

`make check` parses and validates the content without writing anything. Run it
before every commit; CI runs it too.

## Layout

```
content/
  site.yml              parts, home page, publisher, deploy origin
  entries/*.md          one entry per file, <clause>-<slug>.md   (3a, 3b)
  index-terms.yml       the A–Z headwords and their flags        (3c)
shared/
  grc.css               the whole design system — both builds link this file
  grc.js                the whole interactive layer — both builds run this file
tools/
  build.py              CLI: static build, --bundle, --check, --serve
  grcmd/                model, parse, render, seo, search
next/                   the Next.js renderer; reads src/content/bundle.json
.claude/skills/grc-entry/  how to author an entry or an index headword
```

## How the two builds stay identical

`tools/build.py --bundle` writes into `next/`:

- `src/content/bundle.json` — parsed blocks, clause numbering, section maps, the
  JSON-LD graph for every entry, and the index headwords with their filter flags
- `src/styles/grc.css` — a copy of the design system
- `public/assets/grc.js` — a copy of `shared/grc.js`
- `public/search-index.json` and `public/a-z/index.csv` — the same files the
  static build ships

The Next.js app has no markdown parser, no directive syntax, no schema builder
and no arithmetic of its own. It renders what it is given. That is the whole
reason a change to a directive cannot make the two sites disagree.

The bundle is committed, so `next build` needs no Python. Regenerate it with
`make bundle` whenever content changes.

## Authoring

One entry is one markdown file. Front matter carries the metadata; the body is
CommonMark plus a `:::` fence for the components the design system provides:

```markdown
:::lede
Governance, risk and compliance is the coordinated set of practices an
organisation uses to *direct* what it is trying to achieve, *understand* what
could stop it, and *prove* it meets the obligations that apply to it.
:::

## The three pillars

:::terms
Governance :: Who decides, on what authority, and where it is recorded.
Risk :: What could obstruct the objectives, sized, treated and watched.
Compliance :: Which obligations bind you, mapped to controls, with the proof.
:::

:::diagram name="grc-loop" n="1" caption="**The GRC loop.** Break any edge…"
:::
```

Headings are numbered automatically from the entry's clause: `## The three
pillars` inside entry `1.1` becomes `1.1.1`, anchored at both
`#the-three-pillars` and `#c1-1-1`.

Full contract — every front-matter key, every directive, the figure rules and
the house voice — is in `.claude/skills/grc-entry/SKILL.md`. In Claude Code,
`/grc-entry` loads it.

## Design

Direction 1a, *normative standard*. Two type roles and nothing else: **Source
Serif 4** carries all prose, **IBM Plex Mono** carries structure — clause IDs,
metadata, rails, contents. No sans anywhere on the page.

Light is warm paper (`#f7f5f0`) with oxblood (`#7a1f1f`) as the structural
accent. Dark is warm near-black (`#14130f`) with terracotta (`#d9a184`) —
oxblood goes muddy below 4.5:1 on dark, so it is replaced rather than dimmed.
The two quietest greys are darker than the handoff's, because every use of them
is 10–12px mono, which WCAG scores as normal text. Every ink token now clears
4.5:1 on every paper it sits on.

Elevation is hairline borders throughout; the only shadow in the build is under
the search dialog, which genuinely floats.

Three columns above 1200px (corpus rail · article · clause map). Between 1000
and 1200 the clause map becomes a disclosure above the article. Below 1000 the
corpus rail becomes a drawer. Source order is rail, clause map, article — so the
collapse is a re-flow, not a re-order.

## Deploying

**Vercel is the deploy target.** Point a project at this repo with **Root
Directory `next/`**; `next/vercel.json` and `next.config.mjs` do the rest. A
clean clone plus `npm install` builds all 37 pages with no Python, because the
content bundle is committed.

Why Vercel over GitHub Pages, for this site specifically:

- **Redirects.** This is a clause-numbered reference and clause numbers move.
  Old paths go in `vercel.json` with `permanent: true` and the link equity
  follows. Pages has no server-side redirects at all.
- **Path hosting.** Pages can only serve at the root of a domain it controls.
  Vercel can serve `grcmastery.com/wiki`, which consolidates authority onto the
  domain already ranking.
- **A preview per branch**, so an entry can be reviewed rendered before it is
  live.
- **Headroom.** `/suggest-an-edit/` is a placeholder today. Delete
  `output: "export"` from `next.config.mjs` and it can be a real form; nothing
  else in the app has to change.

Vercel's Hobby plan is non-commercial, so a client site needs **Pro**.

Two things about `next/vercel.json` worth knowing before editing it:

- **No comments.** Vercel validates it with `additionalProperties: false` at
  every level, so a `"//"` key fails the deploy *after* a successful build.
  `make check` now catches unknown keys offline.
- **Never set `outputDirectory` alongside `framework: "nextjs"`.** Vercel reads
  it as Next's `distDir` and goes looking for `routes-manifest.json` inside it;
  with `output: "export"` that file is in `.next/` and the build packages fail.
  The Next builder already knows the export lands in `out/`.

The `redirects` array is the reason this is on Vercel. When a clause is
renumbered, add its old path there with `"permanent": true` and the link equity
follows it. Do not prune that block.

Two values in `content/site.yml` control every URL the build emits — canonical
tags, Open Graph, the sitemap, the search index and every internal link:

```yaml
origin: https://grc-wiki.vercel.app   # change to the custom domain at launch
base_path: /                          # "/repo/" only for project-scoped Pages
```

**GitHub Pages** stays wired up as a free staging copy:
`.github/workflows/pages.yml` runs `--check`, builds `dist/` and publishes on
push to `main`. It needs `base_path: /grc-wiki/` and an admin to set
Settings → Pages → Source: GitHub Actions once. Do not run both on the same
domain — they are two renderings of one site and the canonicals would compete.

## SEO

Every entry ships `TechArticle` with `reviewedBy` and `citation`, plus
`BreadcrumbList`; entries with `defines:` add `DefinedTerm`, and entries with a
`:::faq` add `FAQPage`. Nothing in the structured data is invisible on the page.

Search is a prebuilt JSON index — entries, every clause, every FAQ question,
every inline definition and every resolving index headword — fetched once and
filtered in the browser. 257 records, 45 KB. No service, no request per
keystroke.

The A–Z ships `DefinedTermSet` with every published headword, and offers the
term list as CSV at `/a-z/index.csv` — link bait, because other GRC sites cite
a term list.

The editorial policy page is the E-E-A-T anchor: named editors, review dates,
published corrections, and the commercial relationship stated rather than
buried.

## Content status

**27 entries, every part populated, zero dangling references.** Every `prev`,
`next`, `related` and inline definition resolves to a published page, so a demo
review does not hit a dead link.

Counts shown on the site are computed from the content, never asserted. The
masthead says 27 because there are 27; `entries_planned: 212` in `site.yml` is
the target and appears only beside the real figure, on the A–Z. Claiming a
corpus you do not have is the fastest way to lose the trust the whole reference
is built on.

The A–Z carries 121 headwords in inverted index form ("Appetite, risk"), of
which 96 resolve and link. The remaining 25 show their clause number in grey —
deliberate, because the index is the crawl surface and hiding the corpus's shape
makes it less useful, not more honest.

`make check` is clean and CI fails the build if it stops being.
