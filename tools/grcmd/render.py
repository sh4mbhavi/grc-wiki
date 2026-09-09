"""Block list -> HTML, and HTML -> whole pages.

Every string that reaches a template has already been escaped or is authored
markup produced by parse.py. `e()` is used wherever content crosses in.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

from .model import Entry, Site
from .parse import md_inline

from .seo import json_ld_entry, json_ld_home, json_ld_index

FONT_HREF = "https://cdn.jsdelivr.net/npm/@fontsource-variable/hubot-sans/index.css"

# Applied before first paint so a stored preference never flashes the wrong theme.
THEME_BOOT = (
    "try{var t=localStorage.getItem('grc-theme');"
    "if(t){document.documentElement.setAttribute('data-theme',t)}}catch(e){}"
)

MATRIX_ROWS = ["Almost certain", "Likely", "Possible", "Unlikely", "Rare"]
MATRIX_COLS = ["Insignificant", "Minor", "Moderate", "Major", "Severe"]
# Heat index per cell, row-major, matching the design's ramp.
MATRIX_HEAT = [
    [4, 5, 6, 7, 8],
    [3, 4, 5, 6, 7],
    [2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5],
    [0, 1, 2, 3, 4],
]


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


# --- Citations -> links ------------------------------------------------------
#
# Every source line in an entry links to the body that publishes it. The target
# is the standard's own landing page (or that publisher's), not a paywalled PDF,
# so a reader can always get to the authoritative source in one click.

def _nist_sp(m: "re.Match[str]") -> str:
    series, num = m.group(1), m.group(2)
    rev = m.group(3) or m.group(4)
    dash = m.group(5)
    if rev:
        tail = f"r{rev}/final"
    elif dash:
        tail = f"{dash}/final"
    else:
        tail = "final"
    return f"https://csrc.nist.gov/pubs/sp/{series}/{num}/{tail}"


_CITE_RULES: list[tuple["re.Pattern[str]", Any]] = []


def _cite(pattern: str, url: Any) -> None:
    _CITE_RULES.append((re.compile(pattern, re.I), url))


_cite(r"\bNIST\s+SP\s+(\d{3})-(\d+)\s*(?:Rev\.?\s*(\d+)|r(\d+)|-(\d+))?", _nist_sp)
_cite(r"NIST\s+AI\s+100-1|Artificial Intelligence Risk Management Framework|\bAI\s+RMF\b",
      "https://www.nist.gov/itl/ai-risk-management-framework")
_cite(r"NIST\b.*Cybersecurity Framework|\bNIST\s+CSF\b|\bCSF\s*2\.0\b",
      "https://www.nist.gov/cyberframework")
_cite(r"\bNIST\b", "https://csrc.nist.gov/publications/sp800")

_cite(r"ISO(?:/IEC)?\s*270\d\d|ISO/IEC\s*27000\b",
      "https://www.iso.org/isoiec-27001-information-security.html")
_cite(r"\bISO\s*31000\b|\bIEC\s*31010\b|ISO\s+Guide\s*73\b",
      "https://www.iso.org/iso-31000-risk-management.html")
_cite(r"\bISO(?:/TS)?\s*2230\d\b|\bISO/TS\s*22317\b",
      "https://www.iso.org/standard/75106.html")
_cite(r"\bISO\s*9001\b", "https://www.iso.org/iso-9001-quality-management.html")
_cite(r"\bISO/IEC\s*42001\b|Artificial intelligence management system",
      "https://www.iso.org/standard/81230.html")
_cite(r"ISO/IEC\s+Directives", "https://www.iso.org/directives-and-policies.html")
_cite(r"\bISO\b", "https://www.iso.org/standards.html")

_cite(r"\bCOBIT\b", "https://www.isaca.org/resources/cobit")
_cite(r"\bISACA\b|\bCRISC\b|\bCISA\b|\bCISM\b|\bCMMI\b", "https://www.isaca.org/")
_cite(r"\(ISC\)|\bCISSP\b", "https://www.isc2.org/certifications/cissp")
_cite(r"\bGIAC\b", "https://www.giac.org/")
_cite(r"\bSANS\b", "https://www.sans.org/")

_cite(r"Three Lines Model",
      "https://www.theiia.org/en/content/position-papers/2020/the-iias-three-lines-model-an-update-of-the-three-lines-of-defense/")
_cite(r"\bIIA\b|International Professional Practices Framework|Three Lines of Defence|Standards for the Professional Practice",
      "https://www.theiia.org/en/standards/")
_cite(r"\bIAASB\b|\bISA\s*200\b", "https://www.iaasb.org/")

_cite(r"European Data Protection Board|\bEDPB\b",
      "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en")
_cite(r"Regulation \(EU\) 2016/679|General Data Protection Regulation|\bGDPR\b",
      "https://eur-lex.europa.eu/eli/reg/2016/679/oj")

_cite(r"\bAICPA\b|Trust Services Criteria|\bSSAE\b|\bAT-C\b|Description Criteria",
      "https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services")
_cite(r"\bPCI\b|Payment Card Industry|Self-Assessment Questionnaire",
      "https://www.pcisecuritystandards.org/document_library/")
_cite(r"Center for Internet Security|CIS Critical Security Controls|\bCIS\b",
      "https://www.cisecurity.org/controls")
_cite(r"\bCOSO\b", "https://www.coso.org/")
_cite(r"\bHIPAA\b|45 CFR|Office for Civil Rights", "https://www.hhs.gov/hipaa/for-professionals/security/")
_cite(r"\bFIRST\b|Common Vulnerability Scoring System|\bCVSS\b", "https://www.first.org/cvss/")
_cite(r"Open Group|\bO-RA\b|\bO-RT\b|Open FAIR|\bFAIR\b", "https://www.opengroup.org/open-fair")
_cite(r"Cloud Security Alliance|Cloud Controls Matrix|\bCAIQ\b|\bCCM\b|\bSTAR\b", "https://cloudsecurityalliance.org/")
_cite(r"\bHITRUST\b", "https://hitrustalliance.net/")
_cite(r"\bFedRAMP\b", "https://www.fedramp.gov/")
_cite(r"Shared Assessments|\bSIG\b", "https://sharedassessments.org/")
_cite(r"Cyber Essentials", "https://www.ncsc.gov.uk/cyberessentials/overview")
_cite(r"Essential Eight|\bASD\b",
      "https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight")
_cite(r"\bENISA\b", "https://www.enisa.europa.eu/publications")
_cite(r"\bITIL\b", "https://www.axelos.com/certifications/itil-service-management")
_cite(r"\bPTES\b|Penetration Testing Execution Standard", "http://www.pentest-standard.org/")
_cite(r"How to Measure Anything|Hubbard",
      "https://search.worldcat.org/search?q=How+to+Measure+Anything+in+Cybersecurity+Risk")


def link_citation(text: str) -> str:
    """Render a source line and wrap it in a link to the publishing body."""
    inner = md_inline(text)
    for rx, url in _CITE_RULES:
        m = rx.search(text)
        if m:
            target = url(m) if callable(url) else url
            return f'<a href="{e(target)}" target="_blank" rel="noopener">{inner}</a>'
    return inner


# --- Blocks -------------------------------------------------------------------


def render_blocks(blocks: list[dict[str, Any]], site: Site) -> str:
    return "\n".join(render_block(b, site) for b in blocks)


def render_block(block: dict[str, Any], site: Site) -> str:
    kind = block["type"]
    fn = _BLOCKS.get(kind)
    if fn is None:
        raise KeyError(f"no HTML renderer for block type {kind!r}")
    return fn(block, site)


def _b_prose(b, site):
    return f'<div class="prose">{b["html"]}</div>' 


def _b_lede(b, site):
    return f'<p class="lede">{b["html"]}</p>'


def _b_note(b, site):
    return f'<aside class="margin-note">{b["html"]}</aside>'


def _b_heading(b, site):
    if b["level"] != 2:
        return f'<h3 class="clause clause--sub" id="{e(b["id"])}">{e(b["text"])}</h3>'
    return (
        f'<h2 class="clause" id="{e(b["id"])}">'
        f'<span class="u-vh" id="{e(b["alias"])}"></span>'
        f'<span class="clause__n">{e(b["clause"])}</span>{e(b["text"])}'
        f'<a class="anchor" href="#{e(b["id"])}" aria-label="Link to this clause">#</a>'
        f"</h2>"
    )


def _b_terms(b, site):
    rows = "".join(
        f'<dt>{e(item["term"])}</dt><dd>{item["html"]}</dd>' for item in b["items"]
    )
    return f'<dl class="terms">{rows}</dl>'


def _b_def(b, site):
    ref = ""
    if b["ref"]:
        target = site.by_clause(b["ref"])
        if target is not None:
            ref = f' <a class="def__ref" href="{e(site.url(target.url))}">&rarr; {e(b["ref"])}</a>'
    return (
        f'<div class="def"><span class="def__label">DEFINITION &middot; '
        f'{e(b["term"].upper())}</span>{b["html"]}{ref}</div>'
    )


# The register-row diagram: a single risk-register record rendered as a CSS
# artefact. It carries the "real artefact" job a photograph used to do, without
# an image. Kept identical to the React version in next/src/components/Blocks.tsx.
REGISTER_ROW = [
    ("Ref", "R-014", False),
    ("Risk", "Supplier holds customer PII with no DPA signed", False),
    ("Likelihood", "Likely (4)", False),
    ("Impact", "Major (4)", False),
    ("Residual", "16", True),
    ("Owner", "Head of Procurement", False),
    ("Treatment", "Mitigate", False),
    ("Status", "Open · review 30 Sep", False),
]
REGISTER_LABEL = (
    "A risk register row: reference R-014, a supplier holding customer PII with no "
    "data processing agreement, scored likely and major for a residual of 16, owned "
    "by the Head of Procurement, treatment mitigate, status open."
)


def _diagram_loop():
    nodes = [
        ("Governance", "sets objectives &amp; appetite", False),
        ("Risk", "sizes &amp; treats the threats", False),
        ("Assurance", "board &amp; customer reporting", True),
        ("Compliance", "controls &amp; kept evidence", False),
    ]

    def node(i):
        name, sub, out = nodes[i]
        cls = "loop__node loop__node--out" if out else "loop__node"
        return f'<div class="{cls}"><b>{name}</b><span>{sub}</span></div>'

    return (
        f'<div class="loop" role="img" aria-label="Governance sets objectives and appetite for Risk. '
        f'Risk produces controls and evidence held by Compliance. Compliance feeds Assurance, which '
        f'reports back to Governance.">'
        + node(0)
        + '<div class="loop__edge loop__edge--h" aria-hidden="true">sets<br>---&#9656;</div>'
        + node(1)
        + '<div class="loop__edge loop__edge--v" aria-hidden="true">&#9652;<br>reports</div><div></div>'
        + '<div class="loop__edge loop__edge--v" aria-hidden="true">produces<br>&#9662;</div>'
        + node(2)
        + '<div class="loop__edge loop__edge--h" aria-hidden="true">feeds<br>&#9666;---</div>'
        + node(3)
        + "</div>"
    )


def _diagram_register_row():
    out = []
    for k, v, mark in REGISTER_ROW:
        mark_attr = ' data-mark="true"' if mark else ""
        out.append(
            f'<div class="regrow__row"{mark_attr}>'
            f'<span class="regrow__k">{e(k)}</span>'
            f'<span class="regrow__v">{e(v)}</span></div>'
        )
    return f'<div class="regrow" role="img" aria-label="{e(REGISTER_LABEL)}">{"".join(out)}</div>'


def _b_diagram(b, site):
    if b["name"] == "grc-loop":
        body = _diagram_loop()
    elif b["name"] == "register-row":
        body = _diagram_register_row()
    else:
        raise KeyError(b["name"])
    return (
        f'<figure class="figure" id="fig-{b["n"]}"><div class="figure__frame">{body}</div>'
        f"<figcaption>{b['caption']}</figcaption></figure>"
    )


def _b_matrix(b, site):
    mark = tuple(b["mark"]) if b["mark"] else ()
    head_row = "".join(f'<th scope="col">{e(c)}</th>' for c in MATRIX_COLS)
    body = []
    for r, row_name in enumerate(MATRIX_ROWS, start=1):
        cells = []
        for c, col_name in enumerate(MATRIX_COLS, start=1):
            heat = MATRIX_HEAT[r - 1][c - 1]
            marked = " data-mark=\"true\"" if mark == (r, c) else ""
            label = f"{row_name} likelihood, {col_name.lower()} impact"
            if marked:
                label += " - the worked example"
            cells.append(
                f'<td data-heat="{heat}"{marked}><span></span>'
                f'<span class="u-vh">{e(label)}</span></td>'
            )
        body.append(f'<tr><th scope="row">{e(row_name)}</th>{"".join(cells)}</tr>')

    caption = f'<figcaption>{b["note"]}</figcaption>' if b["note"] else ""
    return (
        f'<figure class="figure figure--wide" id="fig-{b["n"]}">'
        f'<div class="scroll-x"><table class="matrix">'
        f'<caption>{b["caption"]}</caption>'
        f'<thead><tr><td></td>{head_row}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        f"</table></div>{caption}</figure>"
    )


def _b_faq(b, site):
    items = []
    for i, item in enumerate(b["items"]):
        open_attr = " open" if i == 0 else ""
        items.append(
            f'<details id="{e(item["id"])}"{open_attr}><summary>{e(item["q"])}</summary>'
            f'<div class="faq__answer">{item["html"]}</div></details>'
        )
    return f'<div class="faq">{"".join(items)}</div>'


def _b_versus(b, site):
    sides = []
    for key, side in zip(("a", "b"), b["sides"]):
        badge = f'<div class="versus__badge">{e(side["badge"])}</div>' if side["badge"] else ""
        sides.append(
            f'<div class="versus__side" data-side="{key}">'
            f'<h3 class="versus__name">{e(side["name"])}</h3>{badge}'
            f'<p class="versus__body">{side["html"]}</p></div>'
        )
    return f'<div class="versus">{"".join(sides)}</div>'


def _b_attrs(b, site):
    rows = []
    for row in b["rows"]:
        av = f' data-v="{e(row["av"])}"' if row.get("av") else ""
        bv = f' data-v="{e(row["bv"])}"' if row.get("bv") else ""
        rows.append(
            f'<tr><th scope="row">{e(row["attr"])}</th>'
            f'<td{av}>{e(row["a"])}</td><td{bv}>{e(row["b"])}</td></tr>'
        )
    return (
        f'<div class="scroll-x"><table class="dtable dtable--attrs">'
        f'<caption>{e(b["a"])} compared with {e(b["b"])}</caption>'
        f'<thead><tr><th scope="col"></th>'
        f'<th scope="col" data-side="a">{e(b["a"])}</th>'
        f'<th scope="col" data-side="b">{e(b["b"])}</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def _b_split(b, site):
    cols = "".join(f"<div>{render_blocks(col, site)}</div>" for col in b["columns"])
    return f'<div class="split" style="--split: {e(b["ratio"])}">{cols}</div>' 


_BLOCKS = {
    "prose": _b_prose,
    "lede": _b_lede,
    "note": _b_note,
    "heading": _b_heading,
    "terms": _b_terms,
    "def": _b_def,
    "diagram": _b_diagram,
    "matrix": _b_matrix,
    "faq": _b_faq,
    "split": _b_split,
    "versus": _b_versus,
    "attrs": _b_attrs,
}


# --- Chrome -------------------------------------------------------------------


def head(site: Site, *, title: str, description: str, path: str, ld: list[dict], keywords=(), robots="index,follow") -> str:
    canonical = site.absolute(path)
    kw = f'\n<meta name="keywords" content="{e(", ".join(keywords))}">' if keywords else ""
    graph = json.dumps({"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="{e(site.config['site']['locale'])}" data-base="{e(site.base_path)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">{kw}
<meta name="robots" content="{e(robots)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{e(site.name)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:locale" content="{e(site.config['site']['locale'].replace('-', '_'))}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#f1f2f3">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="{e(FONT_HREF)}">
<link rel="stylesheet" href="{e(site.url('assets/grc.css'))}">
<link rel="alternate" type="application/xml" href="{e(site.url('sitemap.xml'))}" title="Sitemap">
<script>{THEME_BOOT}</script>
<script type="application/ld+json">{graph}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>"""


def masthead(site: Site, *, crumbs: str = "", with_drawer: bool = False, home: bool = False) -> str:
    drawer = (
        '<button class="masthead__drawer-btn" type="button" data-drawer-btn '
        'aria-expanded="false" aria-controls="corpus">'
        '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round">'
        '<path d="M2 4h12M2 8h12M2 12h12"/></svg>'
        '<span>Browse</span></button>'
        if (with_drawer or home)
        else ""
    )
    crumb_html = (
        f'<span class="masthead__sep" aria-hidden="true">|</span>'
        f'<span class="masthead__crumbs">{crumbs}</span>'
        if crumbs
        else ""
    )
    cls = "masthead masthead--home" if home else "masthead"
    return f"""<header class="{cls}">
{drawer}<a class="masthead__wordmark" href="{e(site.url(''))}">GRC WIKI</a>
{crumb_html}
<div class="masthead__tail">
<button class="masthead__search" type="button" data-finder-open>Search<span class="masthead__search-key">&nbsp;&nbsp;&#8984;K</span></button>
<button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch colour mode">
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><circle cx="8" cy="8" r="3.2"/><path d="M8 1v1.6M8 13.4V15M15 8h-1.6M2.6 8H1M12.9 3.1l-1.1 1.1M4.2 11.8l-1.1 1.1M12.9 12.9l-1.1-1.1M4.2 4.2 3.1 3.1"/></svg>
<span data-theme-label>dark</span></button>
</div>
</header>"""


def finder(site: Site) -> str:
    return f"""<dialog class="finder" data-finder aria-label="Search the reference">
<div class="finder__bar">
<span class="finder__icon"><svg class="icon-search" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="M10.4 10.4 14 14"/></svg></span>
<label class="u-vh" for="finder-input">Search {e(site.entries_total)} entries</label>
<input class="finder__input" id="finder-input" type="search" autocomplete="off" spellcheck="false"
       placeholder="Search a term, a framework, or a question&hellip;" data-finder-input>
<button class="finder__esc" type="button" onclick="this.closest('dialog').close()">esc</button>
</div>
<ul class="finder__results" data-finder-results></ul>
<p class="finder__empty" data-finder-empty>Type to search {e(site.entries_total)} entries and their clauses.</p>
<div class="finder__foot"><span>&#8593;&#8595; move</span><span>&#8629; open</span><span>esc close</span></div>
</dialog>"""


def colophon(site: Site) -> str:
    parts = "".join(
        f'<li><a href="{e(site.url(p.url))}">{e(p.n)} &middot; {e(p.name)}</a></li>' for p in site.parts
    )
    year = 2026
    return f"""<footer class="colophon">
<div class="colophon__cols">
<div><h2>THE REFERENCE</h2><ul>{parts}</ul></div>
<div><h2>RESOURCES</h2><ul>
<li><a href="{e(site.url('/a-z/'))}">A-Z index</a></li>
<li><a href="{e(site.url('/career/breaking-into-grc/'))}">Breaking into GRC</a></li>
<li><a href="{e(site.url('/career/grc-courses-and-training/'))}">Courses &amp; training</a></li>
<li><a href="{e(site.url('sitemap.xml'))}">Sitemap</a></li>
</ul></div>
<div><h2>ABOUT</h2><p class="colophon__about">A plain-language reference for governance, risk and compliance. Free, open access, and checked against the standards it cites.</p></div>
</div>
<div class="colophon__bar">
<span>&copy; {year} GRC Wiki. All rights reserved.</span>
<span>{e(site.entries_total)} entries &middot; {e(site.config['site']['parts_total'])} parts</span>
</div>
</footer>"""


def tail(site: Site) -> str:
    return f"""{finder(site)}
<script src="{e(site.url('assets/grc.js'))}" defer></script>
</body>
</html>"""


# --- Corpus rail --------------------------------------------------------------


def corpus_rail(site: Site, current: Entry | None) -> str:
    out = ['<nav class="rail rail--corpus" id="corpus" data-drawer aria-label="Contents of the reference">']
    out.append('<div class="rail__label">CONTENTS OF THE REFERENCE</div>')
    out.append('<ul class="tree">')

    for part in site.parts:
        expanded = current is not None and current.part == part.n
        out.append("<li>")
        out.append(
            f'<a class="tree__part" href="{e(site.url(part.url))}">{e(part.n)} &middot; '
            f'{e(part.name.upper())}<span class="tree__count">{e(part.published)}</span></a>'
        )
        if expanded:
            pages = [en for en in site.entries if en.part == part.n]
            out.append('<ul class="tree__pages">')
            for page in pages:
                aria = ' aria-current="page"' if current is not None and page.clause == current.clause else ""
                out.append(
                    f'<li><a class="tree__page" href="{e(site.url(page.url))}"{aria} data-entry-link>'
                    f'<span class="tree__n">{e(page.clause)}</span> {e(page.nav_title)}'
                    f'<span class="u-vh" data-read-flag></span></a></li>'
                )
            out.append("</ul>")
        out.append("</li>")
    out.append("</ul>")

    if current is not None and current.related:
        links = []
        for ref in current.related:
            target = site.by_clause(ref)
            if target is None:
                continue
            links.append(f'<li><a href="{e(site.url(target.url))}">{e(target.nav_title)}</a></li>')
        if links:
            out.append(
                '<div class="rail__related"><span class="rail__heading">RELATED ENTRIES</span>'
                f'<ul>{"".join(links)}</ul></div>'
            )

    out.append("</nav>")
    return "\n".join(out)


def page_rail(site: Site, entry: Entry) -> str:
    items = [
        f'<li data-for="" data-active="true" data-depth="2">'
        f'<a href="#main">{e(entry.clause)} {e(entry.nav_title)}</a></li>'
    ]
    for section in entry.sections:
        items.append(
            f'<li data-for="{e(section["id"])}" data-active="false">'
            f'<a href="#{e(section["id"])}">{e(section["clause"])} {e(section["text"])}</a></li>'
        )

    figures = ""
    if entry.figure_count:
        rows = "".join(
            f'<li><a href="#fig-{i}">{i}</a></li>' for i in range(1, entry.figure_count + 1)
        )
        figures = (
            f'<div class="rail__block"><span class="rail__heading">FIGURES</span>'
            f'<ul class="rail__figs">{rows}</ul></div>'
        )

    tools = "".join(
        f'<li><a href="{e(href)}">{e(label)}</a></li>'
        for label, href in (
            ("Cite this page", "#cite"),
            ("Print / PDF", "javascript:window.print()"),
        )
    )

    return f"""<aside class="rail rail--page" data-page-rail aria-label="On this page">
<details open>
<summary>ON THIS PAGE</summary>
<div class="rail__label">ON THIS PAGE</div>
<ul class="toc" data-toc>{''.join(items)}</ul>
<div class="rail__block">
<dl><dt>read</dt><dd data-progress-pct>0%</dd></dl>
<div class="progress" role="progressbar" aria-label="How much of this entry you have read"
     aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="progress__fill" data-progress></div></div>
<dl>
<dt>figures</dt><dd>{e(entry.figure_count)}</dd>
<dt>sources</dt><dd>{e(len(entry.sources))}</dd>
</dl>
</div>
{figures}
<div class="rail__block"><span class="rail__heading">TOOLS</span><ul>{tools}</ul></div>
</details>
</aside>"""


# --- Pages --------------------------------------------------------------------


def entry_page(site: Site, entry: Entry, blocks: list[dict[str, Any]]) -> str:
    part = entry.part_obj
    assert part is not None

    title = f"{entry.title} - {site.name}"
    crumbs = (
        f'Part {e(part.n)} / <a href="{e(site.url(part.url))}">{e(part.name)}</a> / '
        f"{e(entry.clause)}"
    )

    infobox = ""
    if entry.quick_facts:
        rows = "".join(
            f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in entry.quick_facts.items()
        )
        infobox = f'<div class="infobox"><div class="infobox__head">QUICK FACTS</div><dl>{rows}</dl></div>'

    # The lede and the infobox share the opening grid; everything after runs full width.
    lede_html = ""
    rest = blocks
    if blocks and blocks[0]["type"] == "lede":
        lede_html = render_block(blocks[0], site)
        rest = blocks[1:]

    intro_prose = ""
    while rest and rest[0]["type"] == "prose":
        intro_prose += render_block(rest[0], site)
        rest = rest[1:]

    opening = (
        f'<div class="article__opening"><div class="article__body">{lede_html}{intro_prose}</div>'
        f"{infobox}</div>"
    )

    sources = ""
    if entry.sources:
        items = "".join(f"<li>{link_citation(s)}</li>" for s in entry.sources)
        sources = f'<section class="sources" id="cite"><h2>SOURCES</h2><ol>{items}</ol></section>'

    pager = ""
    if entry.prev or entry.next:
        prev_e = site.by_clause(entry.prev["ref"]) if entry.prev else None
        next_e = site.by_clause(entry.next["ref"]) if entry.next else None
        left = (
            f'<a href="{e(site.url(prev_e.url))}">&#9666; {e(entry.prev["ref"])} &nbsp;{e(entry.prev["title"])}</a>'
            if entry.prev and prev_e
            else f'<span class="pager__off">{e(entry.prev["ref"]) + " " + e(entry.prev["title"]) if entry.prev else ""}</span>'
        )
        right = (
            f'<a href="{e(site.url(next_e.url))}">{e(entry.next["ref"])} &nbsp;{e(entry.next["title"])} &#9656;</a>'
            if entry.next and next_e
            else f'<span class="pager__off">{e(entry.next["ref"]) + " " + e(entry.next["title"]) if entry.next else ""}</span>'
        )
        pager = f'<nav class="pager" aria-label="Adjacent entries">{left}{right}</nav>'

    meta_bits = [
        f"Reading {e(entry.reading_minutes)} min",
        f"Cited by {e(entry.cited_by)}",
        f"{e(len(entry.sources))} sources",
    ]

    return f"""{head(site,
        title=title,
        description=entry.description,
        path=entry.url,
        keywords=entry.keywords,
        ld=json_ld_entry(site, entry, blocks))}
{masthead(site, crumbs=crumbs, with_drawer=True)}
<div class="frame">
{corpus_rail(site, entry)}
{page_rail(site, entry)}
<main class="article" id="main" data-article>
<article>
<div class="article__clause">{e(entry.clause)}</div>
<h1 class="article__title">{e(entry.title)}</h1>
<div class="article__meta">{''.join(f'<span>{b}</span>' for b in meta_bits)}</div>
{opening}
{render_blocks(rest, site)}
{sources}
{pager}
</article>
</main>
</div>
{colophon(site)}
{tail(site)}"""


def home_drawer(site: Site) -> str:
    """The hamburger panel on the home page: every part with every entry, so a
    reader can browse the whole reference visually without a search."""
    out = [
        '<nav class="drawer" id="corpus" data-drawer aria-label="Browse the reference">',
        '<div class="drawer__head">BROWSE THE REFERENCE</div>',
    ]
    for part in site.parts:
        pages = [en for en in site.entries if en.part == part.n]
        out.append('<div class="drawer__part">')
        out.append(
            f'<a class="drawer__part-link" href="{e(site.url(part.url))}">'
            f'{e(part.n)} &middot; {e(part.name.upper())}'
            f'<span class="drawer__count">{e(part.published)}</span></a>'
        )
        out.append('<ul>')
        for page in pages:
            out.append(
                f'<li><a href="{e(site.url(page.url))}">'
                f'<span class="drawer__n">{e(page.clause)}</span> {e(page.nav_title)}</a></li>'
            )
        out.append('</ul></div>')
    out.append(
        f'<a class="drawer__az" href="{e(site.url("/a-z/"))}">A-Z index &#8594;</a>'
    )
    out.append('</nav>')
    return "\n".join(out)


def home_page(site: Site) -> str:
    cfg = site.config
    home = cfg["home"]
    ed = cfg["editorial"]

    chips = "".join(
        f'<button class="chip" type="button" data-finder-open data-seed="{e(c)}">{e(c)}</button>'
        for c in home["chips"]
    )

    parts = "".join(
        f'<a class="part" href="{e(site.url(p.url))}">'
        f'<span class="part__head"><span class="part__n">{e(p.n)}</span>'
        f'<span class="part__name">{e(p.name)}</span>'
        f'<span class="part__count">{e(p.published)} entries</span></span>'
        f'<span class="part__blurb">{e(p.blurb)}</span></a>'
        for p in site.parts
    )

    start = []
    for i, ref in enumerate(home["start_here"], start=1):
        target = site.by_clause(ref)
        if target is None:
            continue
        start.append(f'<span class="start__n">{i:02d}</span>')
        start.append(
            f'<span class="start__item"><a href="{e(site.url(target.url))}">{e(target.title)}</a>'
            f'<span class="start__time"> &middot; {e(target.reading_minutes)} min</span></span>'
        )

    cited = "".join(
        f'<li><a href="{e(site.url(site.by_clause(c["ref"]).url))}">{e(c["title"])}</a>'
        f'<span class="cited__n">{e(c["count"])}</span></li>'
        for c in home["most_cited"]
        if site.by_clause(c["ref"])
    )

    sitemap = []
    for part in site.parts:
        pages = [en for en in site.entries if en.part == part.n]
        links = "".join(
            f'<li><a href="{e(site.url(pg.url))}"><span class="sitemap__n">{e(pg.clause)}</span> {e(pg.nav_title)}</a></li>'
            for pg in pages
        )
        sitemap.append(
            f'<div class="sitemap__col"><a class="sitemap__part" href="{e(site.url(part.url))}">'
            f'{e(part.n)} &middot; {e(part.name.upper())}</a><ul>{links}</ul></div>'
        )

    return f"""{head(site,
        title=f"{home['title']} - {site.name}",
        description=cfg['site']['description'],
        path='/',
        keywords=[c for c in home['chips']],
        ld=json_ld_home(site))}
{masthead(site, home=True)}
{home_drawer(site)}
<div class="drawer__scrim" data-drawer-scrim hidden></div>
<main id="main">
<section class="portal">
<div class="portal__inner">
<p class="portal__standfirst">{e(ed['standfirst'])}</p>
<h1 class="portal__title">{e(home['title'])}</h1>
<p class="portal__blurb">{e(" ".join(home['blurb'].split()))}</p>
<button class="searchbar" type="button" data-finder-open>
<span class="searchbar__icon"><svg class="icon-search" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="M10.4 10.4 14 14"/></svg></span>
<span class="searchbar__label">Search a term, a framework, or a question&hellip;</span>
<span class="searchbar__key" aria-hidden="true">&#8984;K</span>
</button>
<div class="chips">{chips}</div>
</div>
</section>

<div class="home">
<div class="home__main">
<h2 class="section-rule">THE REFERENCE &middot; SIX PARTS</h2>
<div class="parts">{parts}</div>

<section>
<h2 class="section-rule">START HERE - IF YOU ARE NEW</h2>
<div class="start">{''.join(start)}</div>
</section>

<section class="sitemap">
<h2 class="section-rule">BROWSE EVERY ENTRY</h2>
<div class="sitemap__grid">{''.join(sitemap)}</div>
</section>
</div>

<aside class="home__aside">
<h2 class="section-rule">MOST CITED</h2>
<div class="cited"><ul>{cited}</ul></div>
<a class="aside-card" href="{e(site.url('/a-z/'))}"><b>A-Z INDEX</b><span>Every term, alphabetically, with the clause it belongs to.</span></a>
<a class="aside-card" href="{e(site.url('/career/breaking-into-grc/'))}"><b>NEW TO GRC?</b><span>How people move into the field, and the gap that blocks them.</span></a>
</aside>
</div>
</main>
{colophon(site)}
{tail(site)}"""


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

BROWSE_MODES = [
    ("A-Z index", "/a-z/", True),
    ("By part", None, False),
    ("By framework", None, False),
    ("By artefact", None, False),
    ("By role", None, False),
]

# All off by default. The handoff shows "Entry-level" ticked, but this page is
# the crawl surface - shipping it pre-filtered would hide most of the corpus
# from the first render, which is the one thing it exists not to do.
FILTERS = [
    ("level", "Entry-level explanations", False),
    ("example", "Has worked example", False),
    ("template", "Has downloadable template", False),
]


def _coverage(site: Site) -> list[str]:
    terms = site.index_terms
    live = [t for t in terms if site.by_clause(t.ref)]
    examples = sum(1 for t in terms if t.example)
    frameworks = sum(1 for t in terms if t.ref.startswith("5."))
    return [
        f"{len(terms)} headwords &middot; {examples} with examples",
        f"{len(live)} headwords live &middot; {site.entries_total} entries",
        f"{frameworks} framework terms mapped",
    ]


def index_page(site: Site) -> str:
    """3c - the A-Z. This is the crawl surface: one page that links every
    headword with its clause number, so depth is two clicks from anywhere."""
    groups: dict[str, list] = {}
    for term in site.index_terms:
        groups.setdefault(term.letter, []).append(term)

    strip = []
    for letter in ALPHABET:
        if letter in groups:
            strip.append(f'<a href="#letter-{letter}">{letter}</a>')
        else:
            strip.append(f'<span data-off="true" aria-hidden="true">{letter}</span>')
    strip.append(f'<span class="strip__count">{len(groups)} letters in use</span>')

    blocks = []
    for letter in sorted(groups):
        rows = []
        for term in groups[letter]:
            target = site.by_clause(term.ref)
            headword = f"<b>{e(term.t)}</b>" if term.key else e(term.t)
            if target is not None:
                headword = f'<a href="{e(site.url(target.url))}">{headword}</a>'
            mark = ' <span class="idx__mark" title="Has a worked example">&#9642;</span>' if term.example else ""
            flags = " ".join(
                f
                for f, on in (
                    ("example", term.example),
                    ("template", term.template),
                    ("level", term.level == "entry"),
                )
                if on
            )
            rows.append(
                f'<li data-flags="{e(flags)}"><span class="idx__term" data-live="{"true" if target else "false"}">'
                f'<span class="idx__head">{headword}{mark}</span>'
                f'<span class="idx__ref">{e(term.ref)}</span></span></li>'
            )
        blocks.append(
            f'<section class="idx__group" data-letter="{letter}">'
            f'<h2 class="idx__letter" id="letter-{letter}">{letter}</h2>'
            f'<ul class="idx__terms">{"".join(rows)}</ul></section>'
        )

    jump = "".join(
        f'<a href="#letter-{l}">{l}</a>' if l in groups else f'<span data-off="true">{l}</span>'
        for l in ALPHABET
    )

    browse = "".join(
        (
            f'<li><a href="{e(site.url(href))}"{" aria-current=\"page\"" if current else ""}>{e(label)}</a></li>'
            if href
            else f"<li><span>{e(label)}</span></li>"
        )
        for label, href, current in BROWSE_MODES
    )

    filters = "".join(
        f'<li><label><input type="checkbox" data-index-filter value="{key}"'
        f'{" checked" if on else ""}>{e(label)}</label></li>'
        for key, label, on in FILTERS
    )

    looked_up = "".join(
        f'<li><a href="{e(site.url(site.by_clause(c["ref"]).url))}">{e(c["title"])}</a></li>'
        for c in site.config["home"]["most_cited"]
        if site.by_clause(c["ref"])
    )

    coverage = "<br>".join(_coverage(site))
    examples_total = sum(1 for t in site.index_terms if t.example)

    return f"""{head(site,
        title=f"Index of entries - {site.name}",
        description=f"Every term in the {site.name}, alphabetically, with the clause it belongs to. "
                    f"{len(site.index_terms)} headwords across {len(site.parts)} parts.",
        path='/a-z/',
        ld=json_ld_index(site))}
{masthead(site, crumbs='Index / A-Z', with_drawer=True)}
<div class="frame">
<nav class="rail rail--corpus" id="corpus" data-drawer aria-label="Browse the index">
<div class="rail__label">BROWSE BY</div>
<ul class="browse">{browse}</ul>
<div class="rail__label" style="margin-top:var(--s-5)">FILTERS</div>
<ul class="filters" data-index-filters>{filters}</ul>
<div class="rail__related"><span class="rail__heading">COVERAGE</span>{coverage}</div>
</nav>

<aside class="rail rail--page" data-page-rail aria-label="Index tools">
<details open>
<summary>JUMP TO LETTER</summary>
<div class="rail__label">JUMP TO LETTER</div>
<nav class="strip" style="border:0;padding:0;margin:0" aria-label="Jump to letter">{jump}</nav>
<div class="rail__block"><span class="rail__heading">MOST LOOKED UP</span><ul>{looked_up}</ul></div>
<div class="rail__block"><span class="rail__heading">EXPORT</span><ul>
<li><a href="{e(site.url('/a-z/index.csv'))}" download>Term list (CSV)</a></li>
<li><a href="javascript:window.print()">Full index (PDF)</a></li>
</ul></div>
<p class="margin-note" style="margin-top:var(--s-5);font-size:var(--t-small)">{e(examples_total)} headwords carry a worked
example, marked with a &#9642; and worked through in full in the entry that owns them.</p>
</details>
</aside>

<main class="idx" id="main">
<h1 class="idx__title">Index of entries</h1>
<p class="idx__intro">Every term in the reference, alphabetically. <b>Bold</b> entries are the ones most
people arrive looking for; a <span class="idx__mark">&#9642;</span> marks an entry with a worked example.
Terms in grey are commissioned and not yet published - the clause number is where they will live.</p>
<nav class="strip" aria-label="Letters in use">{''.join(strip)}</nav>
<div class="idx__cols" data-index>{''.join(blocks)}</div>
<div class="idx__foot">
<span data-index-count>Showing {len(site.index_terms)} of {len(site.index_terms)}</span>
<span><a href="{e(site.url('/a-z/index.csv'))}" download>Download the term list &#9656;</a></span>
</div>
</main>
</div>
{colophon(site)}
{tail(site)}"""


def index_csv(site: Site) -> str:
    """The term list as CSV. Link bait: other GRC sites cite a term list."""
    rows = ["headword,clause,published,worked_example,template,entry_level"]
    for term in site.index_terms:
        entry = site.by_clause(term.ref)
        rows.append(
            ",".join([
                '"' + term.t.replace('"', '""') + '"',
                term.ref,
                "yes" if entry else "no",
                "yes" if term.example else "no",
                "yes" if term.template else "no",
                "yes" if term.level == "entry" else "no",
            ])
        )
    return "\n".join(rows) + "\n"


def part_page(site: Site, part) -> str:
    entries = [en for en in site.entries if en.part == part.n]
    rows = "".join(
        f'<span class="start__n">{en.clause}</span>'
        f'<span class="start__item"><a href="{e(site.url(en.url))}">{e(en.title)}</a>'
        f'<span class="start__time"> &middot; {e(en.reading_minutes)} min</span>'
        f'<span style="display:block;font-size:var(--t-small);color:var(--ink-quiet)">{e(en.description)}</span></span>'
        for en in entries
    )
    return f"""{head(site,
        title=f"{part.name} - {site.name}",
        description=part.blurb,
        path=part.url,
        ld=json_ld_home(site))}
{masthead(site, crumbs=f'Part {part.n} / {e(part.name)}', with_drawer=True)}
<div class="frame">
{corpus_rail(site, entries[0] if entries else None)}
<main class="article" id="main" style="grid-column:2/span 2">
<div class="article__clause">PART {e(part.n)}</div>
<h1 class="article__title">{e(part.name)}</h1>
<p class="lede" style="max-width:56ch">{e(part.blurb)}</p>
<div class="article__meta"><span>{e(len(entries))} entries</span><span>{e(part.count)} planned</span></div>
<div class="start" style="grid-template-columns:44px minmax(0,1fr)">{rows}</div>
</main>
</div>
{colophon(site)}
{tail(site)}"""


def simple_page(site: Site, *, path: str, title: str, description: str, body_html: str, robots="index,follow") -> str:
    return f"""{head(site, title=f"{title} - {site.name}", description=description, path=path, ld=json_ld_home(site), robots=robots)}
{masthead(site, crumbs=e(title))}
<main class="index-page" id="main" style="max-width:760px">
{body_html}
</main>
{colophon(site)}
{tail(site)}"""
