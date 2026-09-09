"""Structured data, sitemap, robots.

The reference ranks on definitional queries, so the schema does three jobs:
say what the page defines (DefinedTerm), anchor each claim to its sources
(TechArticle + citation), and expose the FAQ block. Nothing here is
decorative - every field maps to something visible on the page, which is the
only version of structured data that survives a manual review.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .model import Entry, Site


def _org_id(site: Site) -> str:
    return site.absolute("/") + "#org"


def _maintainer(site: Site) -> str:
    return " ".join(
        site.config.get("editorial", {})
        .get("maintainer", "Maintained by governance, risk and compliance practitioners.")
        .split()
    )


def _organization(site: Site) -> dict[str, Any]:
    """The maintaining body. GRC Wiki is kept by practitioners, so the entity is
    named even though no individual author is. AI answer engines weigh a clear
    publisher entity when deciding whether to cite a source."""
    return {
        "@type": "Organization",
        "@id": _org_id(site),
        "name": site.name,
        "url": site.absolute("/"),
        "description": _maintainer(site),
        "logo": {
            "@type": "ImageObject",
            "url": site.absolute("/assets/logo.svg"),
            "width": 148,
            "height": 34,
        },
    }


def _website(site: Site) -> dict[str, Any]:
    return {
        "@type": "WebSite",
        "@id": site.absolute("/") + "#website",
        "url": site.absolute("/"),
        "name": site.name,
        "description": " ".join(site.config["site"]["description"].split()),
        "inLanguage": site.config["site"]["locale"],
        "publisher": {"@id": _org_id(site)},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": site.absolute("/a-z/") + "?q={search_term_string}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def json_ld_home(site: Site) -> list[dict[str, Any]]:
    return [_organization(site), _website(site)]


def json_ld_index(site: Site) -> list[dict[str, Any]]:
    """The A-Z is a DefinedTermSet: it is the page that says what the corpus
    contains, and the only one worth describing as a collection."""
    url = site.absolute("/a-z/")
    return [
        _organization(site),
        _website(site),
        {
            "@type": "DefinedTermSet",
            "@id": url + "#termset",
            "name": f"{site.name} - index of terms",
            "url": url,
            "description": (
                f"Every term in the {site.name}, alphabetically, with the clause it belongs to."
            ),
            "hasDefinedTerm": [
                {
                    "@type": "DefinedTerm",
                    "name": term.t,
                    "url": site.absolute(entry.url),
                }
                for term in site.index_terms
                if (entry := site.by_clause(term.ref)) is not None
            ],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": site.name, "item": site.absolute("/")},
                {"@type": "ListItem", "position": 2, "name": "Index of entries", "item": url},
            ],
        },
    ]


def json_ld_entry(site: Site, entry: Entry, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    part = entry.part_obj
    assert part is not None
    url = site.absolute(entry.url)

    graph: list[dict[str, Any]] = [_organization(site), _website(site)]

    graph.append({
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": site.name, "item": site.absolute("/")},
            {"@type": "ListItem", "position": 2, "name": part.name, "item": site.absolute(part.url)},
            {"@type": "ListItem", "position": 3, "name": entry.title, "item": url},
        ],
    })

    ed = site.config.get("editorial", {})
    reviewed = entry.reviewed or ed.get("reviewed", "") or today()
    published = ed.get("first_published", "") or reviewed

    article: dict[str, Any] = {
        "@type": "TechArticle",
        "@id": url + "#article",
        "headline": entry.title,
        "name": entry.title,
        "description": entry.description,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": site.config["site"]["locale"],
        "isAccessibleForFree": True,
        "isPartOf": {"@id": site.absolute("/") + "#website"},
        "publisher": {"@id": _org_id(site)},
        "datePublished": published,
        "dateModified": reviewed,
        "articleSection": part.name,
        "wordCount": _word_count(blocks),
        "timeRequired": f"PT{entry.reading_minutes}M",
    }
    if entry.sources:
        article["citation"] = list(entry.sources)
    if entry.keywords:
        article["keywords"] = ", ".join(entry.keywords)
    graph.append(article)

    if entry.defines:
        graph.append({
            "@type": "DefinedTerm",
            "@id": url + "#term",
            "name": entry.defines,
            "alternateName": entry.quick_facts.get("abbr", ""),
            "description": entry.description,
            "url": url,
            "inDefinedTermSet": {
                "@type": "DefinedTermSet",
                "name": site.name,
                "url": site.absolute("/"),
            },
        })

    faq = next((b for b in blocks if b["type"] == "faq"), None)
    if faq:
        graph.append({
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": _strip(item["html"])},
                }
                for item in faq["items"]
            ],
        })

    return graph


def _strip(html_text: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", html_text)
    return " ".join(text.split())


def _word_count(blocks: list[dict[str, Any]]) -> int:
    total = 0
    for block in blocks:
        for key in ("html", "caption", "note"):
            if isinstance(block.get(key), str):
                total += len(_strip(block[key]).split())
        for item in block.get("items", []):
            total += len(_strip(item.get("html", "")).split())
        for column in block.get("columns", []):
            total += _word_count(column)
    return total


def sitemap(site: Site, paths: list[tuple[str, str, str]]) -> str:
    """paths: (site-root path, lastmod, changefreq)."""
    urls = []
    for path, lastmod, freq in paths:
        urls.append(
            "  <url>\n"
            f"    <loc>{site.absolute(path)}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


# AI answer engines only cite pages their crawlers are allowed to fetch. These
# are named explicitly so a future host-level default block does not quietly
# exclude the reference from AI search.
_AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    "ClaudeBot", "Claude-User", "Claude-SearchBot", "anthropic-ai",
    "PerplexityBot", "Perplexity-User",
    "Google-Extended", "Applebot-Extended", "meta-externalagent", "CCBot",
    "Bytespider", "Amazonbot", "cohere-ai", "Diffbot",
]


def robots(site: Site) -> str:
    lines = ["User-agent: *", "Allow: /", ""]
    for agent in _AI_CRAWLERS:
        lines += [f"User-agent: {agent}", "Allow: /", ""]
    lines.append(f"Sitemap: {site.absolute('/sitemap.xml')}")
    return "\n".join(lines) + "\n"


def today() -> str:
    return date.today().isoformat()
