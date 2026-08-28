#!/usr/bin/env python3
"""Build the GRC Reference.

    python tools/build.py                 # static site -> dist/
    python tools/build.py --serve         # build, then serve dist/ on :8000
    python tools/build.py --bundle        # also write next/src/content/bundle.json
    python tools/build.py --check         # parse and validate, write nothing

The static build and the Next.js build share this parser. `--bundle` is what
feeds the Next.js app; it never re-parses markdown itself.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from grcmd import render, search, seo  # noqa: E402
from grcmd.model import ContentError, load_site  # noqa: E402
from grcmd.parse import parse_entry  # noqa: E402

CONTENT = ROOT / "content"
SHARED = ROOT / "shared"
DIST = ROOT / "dist"
NEXT = ROOT / "next"
BUNDLE = NEXT / "src" / "content" / "bundle.json"

EDITORIAL_POLICY = """
<h1 class="article__title" style="max-width:none">Editorial policy</h1>
<p class="lede" style="max-width:60ch">How entries are written, who reviews them, what gets
corrected, and what the relationship to GRC Mastery is.</p>

<h2 class="clause"><span class="clause__n">1</span>WHO WRITES THIS</h2>
<p>Entries are written by practitioners who have done the work being described &mdash; run the
register, sat the audit, written the policy that was later tested. Every entry names its editor
and the credential they hold. An entry with no named editor is not published.</p>

<h2 class="clause"><span class="clause__n">2</span>REVIEW CYCLE</h2>
<p>Each entry carries a review date and an edition number. Entries are reviewed quarterly, and
sooner when a source standard is revised. The review date is the date a human read the entry
against its sources, not the date a file changed.</p>

<h2 class="clause"><span class="clause__n">3</span>SOURCES</h2>
<p>Claims about a framework cite the framework. Where an entry states a practice rather than a
requirement, it says so. We do not cite vendor marketing, and we do not cite ourselves.</p>

<h2 class="clause"><span class="clause__n">4</span>CORRECTIONS</h2>
<p>Corrections are published, not quietly patched. A corrected entry increments its edition and
records what changed. If you have found an error, the fastest route is the
&ldquo;Suggest an edit&rdquo; link in the header.</p>

<h2 class="clause"><span class="clause__n">5</span>THE COMMERCIAL RELATIONSHIP</h2>
<p>This reference is maintained by the team behind GRC Mastery, which sells courses covering the
same material in a taught format. That relationship is stated on every page it appears on, and it
does not change what an entry says. Entries link to the courses where a reader would plausibly
want the taught version; no entry is written to create that opportunity, and nothing here is
paywalled.</p>
"""

SUGGEST = """
<h1 class="article__title" style="max-width:none">Suggest an edit</h1>
<p class="lede" style="max-width:60ch">Corrections are welcome and are published rather than
quietly patched.</p>
<p>Tell us the entry, the clause number, what is wrong, and &mdash; if you have one &mdash; the
source that settles it. Clause numbers are the fastest way to point at something: every heading
in every entry has one, and clicking the <code>#</code> beside a heading copies a link straight
to it.</p>
<p>Replace this page with whatever intake you actually use &mdash; a form, an inbox, a repository
issue template. It exists in the build because the editorial policy links to it, and a policy
that links to nothing is not a policy.</p>
"""

NOT_FOUND = """
<h1 class="article__title" style="max-width:none">No entry at that address</h1>
<p class="lede" style="max-width:60ch">The reference has been renumbered before and will be
again. The index lists every entry currently published.</p>
<p><a href="/a-z/">Browse the A&ndash;Z index</a> or press <kbd>&#8984;K</kbd> to search.</p>
"""


# vercel.json is schema-validated on Vercel's side with additionalProperties
# false at every level, so an unknown key — including a "//" comment — fails the
# deploy after a successful build. Checked here so it fails on a laptop instead.
VERCEL_TOP = {
    "$schema", "alias", "build", "buildCommand", "builds", "cleanUrls", "crons",
    "devCommand", "env", "framework", "functions", "git", "github", "headers",
    "ignoreCommand", "images", "installCommand", "name", "outputDirectory",
    "redirects", "regions", "rewrites", "routes", "trailingSlash", "version",
}
VERCEL_REDIRECT = {"source", "destination", "permanent", "statusCode", "has", "missing"}
VERCEL_HEADER = {"source", "headers", "has", "missing"}


def check_vercel(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name}: not valid JSON — {exc}"]

    problems = [f"{path.name}: unknown key {k!r}" for k in sorted(set(cfg) - VERCEL_TOP)]
    for rule in cfg.get("redirects", []):
        problems += [f"{path.name}: unknown key {k!r} in a redirect" for k in sorted(set(rule) - VERCEL_REDIRECT)]
    for rule in cfg.get("headers", []):
        problems += [f"{path.name}: unknown key {k!r} in a header rule" for k in sorted(set(rule) - VERCEL_HEADER)]

    # framework: nextjs makes Vercel read outputDirectory as Next's distDir and
    # look for routes-manifest.json inside it. With output: "export" that file
    # is in .next/ and the deploy fails after a successful build.
    if cfg.get("framework") == "nextjs" and cfg.get("outputDirectory"):
        problems.append(
            f"{path.name}: outputDirectory must not be set alongside framework 'nextjs' — "
            "Vercel reads it as distDir and will not find routes-manifest.json"
        )
    return problems


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(*, bundle: bool, check: bool) -> int:
    site = load_site(CONTENT)

    parsed = {}
    for entry in site.entries:
        blocks, sections, figures = parse_entry(entry)
        entry.sections = sections
        entry.figure_count = figures
        parsed[entry.clause] = (blocks, sections, figures)

    # Referential integrity: a reference work that links to nothing is worse
    # than one that admits the entry is not written yet.
    problems: list[str] = []
    for entry in site.entries:
        for ref in entry.related:
            if site.by_clause(ref) is None:
                problems.append(f"{entry.source_path.name}: related clause {ref} does not exist")
        for key in ("prev", "next"):
            link = getattr(entry, key)
            if link and site.by_clause(link["ref"]) is None:
                problems.append(
                    f"{entry.source_path.name}: {key} points at {link['ref']}, which is not published "
                    "(rendered as plain text)"
                )
        for block in parsed[entry.clause][0]:
            if block["type"] == "def" and block["ref"] and site.by_clause(block["ref"]) is None:
                problems.append(
                    f"{entry.source_path.name}: definition of {block['term']!r} refers to "
                    f"{block['ref']}, which is not published"
                )

    for problem in problems:
        print(f"  note  {problem}", file=sys.stderr)

    # Deploy config is a build-time correctness question, not a note.
    config_errors = check_vercel(NEXT / "vercel.json")
    for error in config_errors:
        print(f"  error {error}", file=sys.stderr)
    if config_errors:
        raise ContentError(f"{len(config_errors)} deploy-config problem(s) — see above")

    if check:
        print(f"parsed {len(site.entries)} entries, {len(problems)} dangling references")
        return 0

    if DIST.exists():
        shutil.rmtree(DIST)

    urls: list[tuple[str, str, str]] = []

    write(DIST / "index.html", render.home_page(site))
    urls.append(("/", seo.today(), "weekly"))

    write(DIST / "a-z" / "index.html", render.index_page(site))
    write(DIST / "a-z" / "index.csv", render.index_csv(site))
    urls.append(("/a-z/", seo.today(), "weekly"))

    for part in site.parts:
        if not any(en.part == part.n for en in site.entries):
            continue
        write(DIST / part.slug / "index.html", render.part_page(site, part))
        urls.append((part.url, seo.today(), "monthly"))

    for entry in site.entries:
        blocks, _, _ = parsed[entry.clause]
        write(DIST / entry.url.strip("/") / "index.html", render.entry_page(site, entry, blocks))
        urls.append((entry.url, entry.reviewed or seo.today(), "monthly"))

    write(DIST / "editorial-policy" / "index.html", render.simple_page(
        site, path="/editorial-policy/", title="Editorial policy",
        description="Who writes this reference, how it is reviewed, how corrections are handled, "
                    "and what the relationship to GRC Mastery is.",
        body_html=EDITORIAL_POLICY))
    urls.append(("/editorial-policy/", seo.today(), "yearly"))

    write(DIST / "suggest-an-edit" / "index.html", render.simple_page(
        site, path="/suggest-an-edit/", title="Suggest an edit",
        description="How to report an error in the GRC Reference.",
        body_html=SUGGEST))
    urls.append(("/suggest-an-edit/", seo.today(), "yearly"))

    write(DIST / "404.html", render.simple_page(
        site, path="/404.html", title="Not found",
        description="No entry at that address.", body_html=NOT_FOUND, robots="noindex,follow"))

    (DIST / "assets").mkdir(parents=True, exist_ok=True)

    write(DIST / "search-index.json", search.build_index(site, parsed))
    write(DIST / "sitemap.xml", seo.sitemap(site, urls))
    write(DIST / "robots.txt", seo.robots(site))
    # GitHub Pages otherwise runs the output through Jekyll and drops nothing
    # useful, but does add a build step we do not need.
    write(DIST / ".nojekyll", "")

    (DIST / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SHARED / "grc.css", DIST / "assets" / "grc.css")
    shutil.copy2(SHARED / "grc.js", DIST / "assets" / "grc.js")

    if bundle:
        # The Next.js app never parses markdown and never re-derives a number.
        # It reads this bundle, the same stylesheets and the same behaviour
        # script, so the two builds cannot tell different stories.
        index_terms = []
        for term in site.index_terms:
            target = site.by_clause(term.ref)
            index_terms.append({
                "t": term.t,
                "ref": term.ref,
                "key": term.key,
                "example": term.example,
                "template": term.template,
                "level": term.level,
                "url": target.url if target else "",
                "flags": " ".join(
                    f for f, on in (
                        ("example", term.example),
                        ("template", term.template),
                        ("level", term.level == "entry"),
                        ("fresh", render._is_fresh(site, term)),
                    ) if on
                ),
            })

        write(BUNDLE, json.dumps({
            "site": site.config,
            "ld": seo.json_ld_home(site),
            "index_ld": seo.json_ld_index(site),
            "parts": [vars(p) for p in site.parts],
            "entries": [
                {
                    **{
                        k: v for k, v in vars(entry).items()
                        if k not in ("body", "source_path", "part_obj")
                    },
                    "url": entry.url,
                    "part_slug": entry.part_obj.slug,
                    "blocks": parsed[entry.clause][0],
                    "ld": seo.json_ld_entry(site, entry, parsed[entry.clause][0]),
                }
                for entry in site.entries
            ],
            "index": {"terms": index_terms, "coverage": render._coverage(site)},
            "pages": {
                "editorial_policy": EDITORIAL_POLICY,
                "suggest": SUGGEST,
                "not_found": NOT_FOUND,
            },
        }, ensure_ascii=False, indent=1))

        styles = NEXT / "src" / "styles"
        styles.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SHARED / "grc.css", styles / "grc.css")
        (NEXT / "public" / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(SHARED / "grc.js", NEXT / "public" / "assets" / "grc.js")
        shutil.copy2(DIST / "search-index.json", NEXT / "public" / "search-index.json")
        (NEXT / "public" / "a-z").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DIST / "a-z" / "index.csv", NEXT / "public" / "a-z" / "index.csv")
        print(f"bundle  {BUNDLE.relative_to(ROOT)} + next/src/styles + next/public")

    pages = len(urls) + 1
    print(f"built   {pages} pages, {len(site.entries)} entries -> {DIST.relative_to(ROOT)}/")
    return 0


def serve(port: int) -> None:
    import functools
    import http.server
    import socketserver

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"serving http://localhost:{port}/  (ctrl-c to stop)")
        httpd.serve_forever()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="serve dist/ after building")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--bundle", action="store_true", help="also write the Next.js content bundle")
    ap.add_argument("--check", action="store_true", help="validate content, write nothing")
    args = ap.parse_args()

    try:
        code = build(bundle=args.bundle, check=args.check)
    except ContentError as exc:
        print(f"content error: {exc}", file=sys.stderr)
        return 1

    if code == 0 and args.serve:
        serve(args.port)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
