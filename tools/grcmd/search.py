"""Prebuilt search index.

Search is local and instant: the whole index is one JSON file the browser
fetches once. At 212 entries with their clauses that is a few tens of
kilobytes, so there is no reason to involve a service.

Record shape is terse because it ships to every visitor:
    c  clause reference        t  title
    u  url (site-root path)    x  context line
    k  extra keywords          d  depth (1 entry, 2 clause, 3 question)
"""

from __future__ import annotations

import json
from typing import Any

from .model import Entry, Site
from .seo import _strip


def build_index(site: Site, parsed: dict[str, tuple[list[dict[str, Any]], list[dict[str, str]], int]]) -> str:
    records: list[dict[str, Any]] = []

    for entry in site.entries:
        blocks, sections, _ = parsed[entry.clause]

        records.append({
            "c": entry.clause,
            "t": entry.title,
            "u": entry.url.lstrip("/"),
            "x": entry.description,
            "k": " ".join(entry.keywords),
            "d": 1,
        })

        for section in sections:
            records.append({
                "c": section["clause"],
                "t": section["text"],
                "u": f"{entry.url.lstrip('/')}#{section['id']}",
                "x": entry.nav_title,
                "k": "",
                "d": 2,
            })

        for block in _walk(blocks):
            if block["type"] != "faq":
                continue
            for item in block["items"]:
                records.append({
                    "c": entry.clause,
                    "t": item["q"],
                    "u": f"{entry.url.lstrip('/')}#{item['id']}",
                    "x": _truncate(_strip(item["html"]), 110),
                    "k": "",
                    "d": 3,
                })

        for block in _walk(blocks):
            if block["type"] != "def":
                continue
            records.append({
                "c": block["ref"] or entry.clause,
                "t": block["term"],
                "u": entry.url.lstrip("/"),
                "x": _truncate(_strip(block["html"]), 110),
                "k": "definition",
                "d": 2,
            })

    # Index headwords that resolve, so a reader can search the inverted form
    # ("appetite, risk") and land on the entry that defines it.
    for term in site.index_terms:
        entry = site.by_clause(term.ref)
        if entry is None:
            continue
        if term.t.lower() == entry.title.lower():
            continue
        records.append({
            "c": term.ref,
            "t": term.t,
            "u": entry.url.lstrip("/"),
            "x": entry.nav_title,
            "k": "index",
            "d": 2,
        })

    return json.dumps(
        {"generated": True, "count": len(records), "records": records},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _walk(blocks: list[dict[str, Any]]):
    for block in blocks:
        yield block
        for column in block.get("columns", []):
            yield from _walk(column)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"
