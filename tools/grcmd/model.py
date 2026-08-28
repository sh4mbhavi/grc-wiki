"""Content model: load site.yml and the entry files into typed objects.

Nothing here knows about HTML. `render.py` and the JSON bundle both consume
these objects, which is what keeps the static build and the Next.js build
telling the same story.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


class ContentError(Exception):
    """Raised for an authoring mistake we can name precisely."""


@dataclass
class Part:
    n: int
    slug: str
    name: str
    count: int          # planned for this part
    blurb: str
    published: int = 0  # filled in once the entries are loaded

    @property
    def url(self) -> str:
        return f"/{self.slug}/"


@dataclass
class Entry:
    clause: str
    part: int
    slug: str
    title: str
    description: str
    body: str
    source_path: Path
    short_title: str = ""
    keywords: list[str] = field(default_factory=list)
    defines: str = ""
    reviewed: str = ""
    edition: int = 1
    editor: str = ""
    reading_minutes: int = 0
    cited_by: int = 0
    canonical_entry: bool = False
    quick_facts: dict[str, Any] = field(default_factory=dict)
    related: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    prev: dict[str, str] | None = None
    next: dict[str, str] | None = None

    # Filled in by the renderer once the body has been parsed.
    sections: list[dict[str, Any]] = field(default_factory=list)
    figure_count: int = 0

    part_obj: Part | None = None

    @property
    def url(self) -> str:
        if self.part_obj is None:
            raise ContentError(f"{self.clause} has no resolved part")
        return f"/{self.part_obj.slug}/{self.slug}/"

    @property
    def nav_title(self) -> str:
        return self.short_title or self.title

    @property
    def sort_key(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.clause.split("."))


@dataclass
class IndexTerm:
    """A headword in the A-Z index. Points at a clause, which may or may not
    be published yet — an index that hides the corpus's shape is less useful
    than one that shows where it is going."""
    t: str
    ref: str
    key: bool = False
    example: bool = False
    template: bool = False
    level: str = ""

    @property
    def letter(self) -> str:
        return self.t[0].upper()


@dataclass
class Site:
    root: Path
    config: dict[str, Any]
    parts: list[Part]
    entries: list[Entry]
    index_terms: list[IndexTerm] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.config["site"]["name"]

    @property
    def origin(self) -> str:
        return self.config["site"]["origin"].rstrip("/")

    @property
    def base_path(self) -> str:
        base = self.config["site"].get("base_path", "/") or "/"
        if not base.startswith("/"):
            base = "/" + base
        if not base.endswith("/"):
            base += "/"
        return base

    def url(self, path: str) -> str:
        """Site-root path -> the path a browser should actually request."""
        return self.base_path + path.lstrip("/")

    def absolute(self, path: str) -> str:
        return self.origin + self.url(path)

    @property
    def entries_total(self) -> int:
        """Always the real number. Nothing in the build may claim more."""
        return len(self.entries)

    @property
    def entries_planned(self) -> int:
        return int(self.config["site"].get("entries_planned", len(self.entries)))

    def part(self, n: int) -> Part:
        for p in self.parts:
            if p.n == n:
                return p
        raise ContentError(f"no part numbered {n}")

    def by_clause(self, clause: str) -> Entry | None:
        for e in self.entries:
            if e.clause == clause:
                return e
        return None


def _split_front_matter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    match = FRONT_MATTER.match(text)
    if not match:
        raise ContentError(f"{path.name}: missing YAML front matter")
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ContentError(f"{path.name}: front matter is not valid YAML — {exc}") from exc
    return meta, text[match.end():]


REQUIRED = ("clause", "part", "slug", "title", "description")


def load_entry(path: Path) -> Entry:
    meta, body = _split_front_matter(path.read_text(encoding="utf-8"), path)

    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        raise ContentError(f"{path.name}: front matter missing {', '.join(missing)}")

    known = {f for f in Entry.__dataclass_fields__ if f not in ("body", "source_path", "sections", "figure_count", "part_obj")}
    unknown = set(meta) - known
    if unknown:
        raise ContentError(f"{path.name}: unknown front-matter keys {', '.join(sorted(unknown))}")

    kwargs: dict[str, Any] = {k: v for k, v in meta.items()}
    kwargs["clause"] = str(kwargs["clause"])
    kwargs["related"] = [str(r) for r in kwargs.get("related", [])]
    kwargs["reviewed"] = str(kwargs.get("reviewed", ""))
    kwargs["description"] = " ".join(str(kwargs["description"]).split())
    kwargs["quick_facts"] = {str(k): str(v) for k, v in (kwargs.get("quick_facts") or {}).items()}

    return Entry(body=body, source_path=path, **kwargs)


def load_site(root: Path) -> Site:
    config_path = root / "site.yml"
    if not config_path.exists():
        raise ContentError(f"no site.yml at {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    parts = [Part(**p) for p in config["parts"]]
    entries = [load_entry(p) for p in sorted((root / "entries").glob("*.md"))]

    seen: dict[str, Path] = {}
    for entry in entries:
        if entry.clause in seen:
            raise ContentError(
                f"clause {entry.clause} is used by both {seen[entry.clause].name} "
                f"and {entry.source_path.name}"
            )
        seen[entry.clause] = entry.source_path
        entry.part_obj = next((p for p in parts if p.n == entry.part), None)
        if entry.part_obj is None:
            raise ContentError(f"{entry.source_path.name}: part {entry.part} is not in site.yml")

    entries.sort(key=lambda e: e.sort_key)
    for part in parts:
        part.published = sum(1 for en in entries if en.part == part.n)

    site = Site(root=root, config=config, parts=parts, entries=entries)
    site.index_terms = load_index_terms(root)
    return site


def load_index_terms(root: Path) -> list[IndexTerm]:
    path = root / "index-terms.yml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms = []
    for raw in data.get("terms", []):
        unknown = set(raw) - set(IndexTerm.__dataclass_fields__)
        if unknown:
            raise ContentError(f"index-terms.yml: unknown keys {', '.join(sorted(unknown))} on {raw.get('t')!r}")
        terms.append(IndexTerm(**{**raw, "ref": str(raw.get("ref", ""))}))
    seen: dict[str, str] = {}
    for term in terms:
        key = term.t.lower()
        if key in seen:
            raise ContentError(
                f"index-terms.yml: headword {term.t!r} is defined twice "
                f"({seen[key]} and {term.ref})"
            )
        seen[key] = term.ref

    terms.sort(key=lambda t: t.t.lower())
    return terms
