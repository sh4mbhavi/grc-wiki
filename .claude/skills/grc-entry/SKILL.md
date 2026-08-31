---
name: grc-entry
description: Write, edit, or review content for the GRC Wiki — an entry in content/entries/ or a headword in content/index-terms.yml. Use when adding or revising either, filling out a part of the corpus, or checking something against the editorial and SEO standard before it ships. Covers the front-matter contract, the :::directive syntax including the comparison directives, clause numbering, figure discipline, the house voice, and the SEO checks that make a definitional or comparison page rank.
user-invocable: true
argument-hint: "[new <clause> <title> | review <file> | plan <part>]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(.venv/bin/python tools/build.py *)
---

# Writing for the GRC Wiki

Two content types. Sections 1–7 cover **entries**, which are the corpus;
sections 8–10 cover comparison entries, index headwords and the counting rule.

| Type | Lives in | Renders as |
| --- | --- | --- |
| Entry | `content/entries/<clause>-<slug>.md` | the full article |
| Index headword | `content/index-terms.yml` | a row in the A–Z |

One entry is one markdown file in `content/entries/`, named `<clause>-<slug>.md`.
The build turns it into a page in both the static site and the Next.js app. You
never write HTML, and you never write a page — you write an entry, and the
pipeline decides what a page looks like.

Run `.venv/bin/python tools/build.py --check` after every edit. It parses,
validates the front matter, and lists dangling clause references. It is fast and
it catches every mistake this document warns about.

## 1. What this reference is

A plain-language reference work on governance, risk and compliance, published by
the team behind GRC Mastery. Three things follow from that and constrain every
entry:

- **It reads as a reference work, not a brand page.** No marketing hero, no
  "trusted by", no benefit bullets, no calls to action in the body. The clause
  numbering exists to signal a document of record.
- **It ranks on definitional queries.** The target reader typed *what is GRC*,
  *risk appetite vs tolerance*, *ISO 27001 vs SOC 2*. The answer to the query
  belongs in the first forty words, above every heading.
- **Conversion is a margin event.** One `:::note` at the foot of the entry, in
  the flow, admitting the commercial relationship and stating that the entry
  stays free. Never more than one, never a section, never mid-argument.

## 2. Front matter

```yaml
---
clause: "3.4"                 # required, quoted, unique across the corpus
part: 3                       # required, must exist in content/site.yml
slug: risk-treatment          # required, becomes /risk/risk-treatment/
title: Risk treatment options # required, the <h1> and the <title>
short_title: Risk treatment   # optional, used in nav where the title is long
description: >-               # required, 120–158 chars, becomes the meta description
  Four options and nothing else: accept, mitigate, transfer, avoid. What each
  one commits you to, and which one "monitor" is really hiding.
keywords:                     # optional but expected — real queries, not topics
  - risk treatment options
  - accept mitigate transfer avoid
defines: Risk treatment       # optional; emits DefinedTerm schema. Set it on the
                              # entry that is the canonical definition of a term.
reviewed: 2026-08-14          # required in practice — it is an E-E-A-T signal
edition: 2                    # increment on every published correction
editor: C.T., CISA            # a real person with a real credential
reading_minutes: 6
cited_by: 9
canonical_entry: true         # optional; raises sitemap priority
quick_facts:                  # optional; the infobox beside the lede. 4–7 rows.
  options: 4
  owner: Risk owner
related: ["3.1", "3.2"]       # clause refs; unresolved ones are dropped with a note
sources:                      # the standards the claims rest on
  - "ISO 31000:2018, clause 6.5"
prev: { ref: "3.3", title: Risk scoring }
next: { ref: "3.5", title: Issue management }
---
```

`--check` fails on unknown keys, so a typo is caught rather than silently
ignored.

## 3. Body structure

The spine that answers a definitional query and still carries depth:

1. `:::lede` — the definition, one sentence, in the first forty words.
2. One or two unheaded paragraphs of consequence — why the definition matters.
3. `## Section` headings. The build numbers them `<clause>.1`, `.2`, … and gives
   each one a slug anchor plus a clause-number alias, so both `#the-three-pillars`
   and `#c1-1-1` resolve.
4. A `## Common questions` section holding a `:::faq`, when the entry has real
   recurring questions. Do not invent them.
5. `:::note` — the single margin note, last.

Sources and the pager are generated from front matter. Never write them by hand.

## 4. Directives

| Directive | Use |
| --- | --- |
| `:::lede` | The opening definition. Exactly one, first. |
| `:::terms` | `Term :: description` per line. For a set of parallel definitions. |
| `:::def term="X" ref="3.2"` | An inline definition callout that points at the entry owning the term. |
| `:::diagram name="grc-loop" n="1" caption="…"` | A named CSS diagram from the design system. `grc-loop` and `register-row` exist today. |
| `:::matrix n="2" mark="3,3" caption="…" note="…"` | The 5×5 risk matrix. `mark` is `row,col`, 1-indexed. |
| `:::faq` | `### Question` then the answer. First item renders open. Emits FAQPage schema. |
| `:::note` | The margin note. One per entry. |
| `:::split ratio="1.25fr 1fr"` | Two columns, separated by a line containing only `+++`. |
| `:::versus a="X" b="Y"` | The two sides of a comparison entry. See section 8. |
| `:::attrs a="X" b="Y"` | The comparison table. See section 8. |

Markdown tables, lists, emphasis and links all work normally. Tables get the
house treatment and a horizontal scroller automatically.

Adding a new diagram means adding it to `DIAGRAMS` in `tools/grcmd/parse.py`
and giving it a renderer in `tools/grcmd/render.py` *and*
`next/src/components/Blocks.tsx`. Diagrams are design-system parts, not things
an author draws in markdown.

**Any value containing a comma must be quoted** inside a `{ }` YAML flow
mapping, or the comma is read as the next key.

## 5. Figure discipline

**No images. Ever.** The reference carries CSS/SVG diagrams and the risk matrix
and nothing photographic — no `<img>`, no markdown image, no stock photos, no
screenshots. `--check` fails on any image syntax anywhere in `content/`, so the
ban is a build gate, not a guideline.

Two figure kinds do the work: a relationship diagram (a named `:::diagram`) and
a data figure (the `:::matrix`, or a diagram like `register-row` that stands in
for the real artefact a photograph used to show). Two figures is plenty; three
is the ceiling. Every figure is numbered and captioned; `--check` fails a figure
with no caption.

A new diagram is a design-system part: add it to `DIAGRAMS` in
`tools/grcmd/parse.py` and give it a renderer in `tools/grcmd/render.py` *and*
`next/src/components/Blocks.tsx`, kept byte-for-byte in step. An author never
draws one in markdown.

## 6. Voice

Read three published entries before writing one. The register is a specialist
explaining to a competent stranger: declarative, specific, and willing to say
what usually goes wrong.

- Lead with the claim. No throat-clearing, no "in today's landscape", no
  restating the heading as the first sentence.
- Prefer the concrete number, standard, clause or date to the general statement.
- Say what fails, not only what should happen. The failure modes are the part a
  reader cannot get from the standard itself.
- No hedging stacks ("it's important to note that it may sometimes be"). Say it
  or cut it.
- No tricolon habit, no "not just X, but Y", no rhetorical questions as
  headings, no bold-run summary lines.
- British spelling, Oxford comma off, sentence case in prose headings.

Where a claim is contested or practice-dependent, say so in the sentence rather
than softening the whole paragraph.

## 7. Before it ships

- `.venv/bin/python tools/build.py --check` is clean, or every note it prints is
  a deliberate forward reference to an unwritten entry.
- The description is 120–158 characters and reads as a sentence a person would
  click.
- The definition is answerable from the first forty words with no scrolling.
- Every factual claim about a framework traces to something in `sources`.
- Every heading earns its clause number: it is a section of an argument, not a
  label on a paragraph.
- The margin note appears once, at the foot, and the entry reads as neutral with
  it deleted.

## 8. Comparison entries

"X vs Y" is the highest-intent query type in this field, and the answer is
short — so the page earns itself with structure rather than length. Two
directives do that work.

```markdown
:::versus a="GRC" a-badge="SECOND LINE" b="Internal audit" b-badge="THIRD LINE"
Designs the control, writes the policy, keeps the register.
+++
Samples the same controls without having designed them, forms an opinion.
:::

:::attrs a="GRC" b="Internal audit"
Reports to :: Management :: Audit committee or board
Owns the control :: +Yes :: -Never
:::
```

`:::versus` takes the two sides, separated by `+++` like a split. `:::attrs`
takes `attribute :: a :: b` per row; a `+` prefix marks a positive, `-` a
negative.

Two rules:

- **Keep the attribute rows in the same order on every comparison entry.** The
  table is the snippet target, and a reader comparing two of your pages is
  comparing two tables.
- Put the verdict in the lede, in one sentence, with the answer in bold. If the
  reader stops after forty words they should have it.

`content/entries/1.4-grc-vs-internal-audit.md` and `5.1-iso-27001-vs-soc-2.md`
are the two worked examples.

## 9. Index headwords (3c)

`content/index-terms.yml` is the A–Z. Headwords are **inverted** — "Appetite,
risk", "Audit, internal" — which is real index convention and also captures both
query orders. A term names the clause it belongs to; the index links it if that
clause is published and shows it in grey if it is not.

```yaml
- { t: "Appetite, risk", ref: "3.2", key: true, example: true, level: entry }
```

`key` bolds it (the terms people arrive looking for), `example` marks a worked
example, `template` a downloadable, `level: entry` an entry-level explanation.
The last three drive the filters in the left rail. `--check` refuses a duplicate
headword.

A published entry usually earns two or three headwords: its own title, the
inverted form, and any term it is the canonical definition of. Do not add a
headword for something the entry only mentions.

## 10. Counts are computed, never asserted

The masthead, the part cards and the A–Z all show the real number of published
entries, derived from `content/entries/`. `entries_planned` in `site.yml` is the
target corpus and appears only beside the real figure.

Never hard-code a count anywhere. Claiming a corpus that does not exist is the
fastest way to lose the trust the reference is built on, and it is the first
thing a reviewer checks.
