"""Markdown + directive parser.

The authoring syntax is CommonMark plus one addition: a `:::` fence that names
a block component.

    :::name key="value" flag
    ...body...
    :::

Fences nest. Inside `:::split`, a line of exactly `+++` separates the columns.

Parsing happens once, here, and produces a list of block dicts. `render.py`
turns those into HTML for the static build; `bundle.py` serialises the same
list for the Next.js build. Neither can drift from the other, because neither
does any parsing of its own.
"""

from __future__ import annotations

import re
from typing import Any

import markdown

from .model import ContentError, Entry

FENCE = re.compile(r"^:::\s*(?P<name>[a-z][a-z0-9-]*)?(?P<attrs>.*)$")
ATTR = re.compile(r"""(?P<key>[a-z][a-z0-9_-]*)(?:\s*=\s*(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>\S+)))?""")
HEADING = re.compile(r"^(?P<hashes>#{2,4})\s+(?P<text>.+?)\s*$")
COLUMN_BREAK = "+++"

BLOCK_DIRECTIVES = {
    "lede", "terms", "diagram", "matrix", "def", "faq", "note", "split", "col",
    "versus", "attrs",
}

# Diagrams are named, not free-form: a diagram is a piece of the design system,
# not something an author draws in markdown. They are also the only figure the
# reference carries — there are no photographs and no image slots.
DIAGRAMS = {"grc-loop", "register-row"}


def slugify(text: str) -> str:
    out = re.sub(r"[^\w\s-]", "", text.lower())
    out = re.sub(r"[\s_-]+", "-", out).strip("-")
    return out or "section"


def _md() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=["tables", "smarty", "attr_list", "sane_lists"],
        extension_configs={"smarty": {"smart_dashes": False}},
        output_format="html",
    )


_CONVERTER = _md()


def md_to_html(text: str) -> str:
    _CONVERTER.reset()
    return _CONVERTER.convert(text.strip())


def md_inline(text: str) -> str:
    """Render a short string (a caption, a note) without wrapping it in <p>."""
    html = md_to_html(text)
    if html.startswith("<p>") and html.endswith("</p>") and html.count("<p>") == 1:
        html = html[3:-4]
    return html


def parse_attrs(raw: str) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for m in ATTR.finditer(raw or ""):
        value = m.group("dq")
        if value is None:
            value = m.group("sq")
        if value is None:
            value = m.group("bare")
        attrs[m.group("key")] = True if value is None else value
    return attrs


# --- Fence tree ---------------------------------------------------------------


def _tree(lines: list[str], start: int, stop_at_close: bool, where: str) -> tuple[list[Any], int]:
    """Return (nodes, index-after). A node is either a raw text run (str) or a
    dict {name, attrs, children}."""
    nodes: list[Any] = []
    buffer: list[str] = []
    i = start

    def flush() -> None:
        if buffer:
            text = "\n".join(buffer)
            if text.strip():
                nodes.append(text)
            buffer.clear()

    while i < len(lines):
        line = lines[i]
        match = FENCE.match(line.rstrip())
        if match:
            name = match.group("name")
            if not name:
                if not stop_at_close:
                    raise ContentError(f"{where}: stray ':::' close on line {i + 1}")
                flush()
                return nodes, i + 1
            if name not in BLOCK_DIRECTIVES:
                raise ContentError(
                    f"{where}: unknown directive ':::{name}' on line {i + 1}. "
                    f"Known: {', '.join(sorted(BLOCK_DIRECTIVES))}"
                )
            flush()
            children, i = _tree(lines, i + 1, True, where)
            nodes.append({"name": name, "attrs": parse_attrs(match.group("attrs")), "children": children})
            continue
        buffer.append(line)
        i += 1

    if stop_at_close:
        raise ContentError(f"{where}: a ':::' block is never closed")
    flush()
    return nodes, i


# --- Blocks -------------------------------------------------------------------


class Builder:
    def __init__(self, entry: Entry):
        self.entry = entry
        self.where = entry.source_path.name
        self.section_n = 0
        self.figure_n = 0
        self.sections: list[dict[str, str]] = []

    # -- helpers

    def next_figure(self, attrs: dict[str, Any]) -> int:
        if attrs.get("n"):
            self.figure_n = int(attrs["n"])
        else:
            self.figure_n += 1
        return self.figure_n

    def caption(self, attrs: dict[str, Any], n: int) -> str:
        text = attrs.get("caption")
        if not text:
            raise ContentError(f"{self.where}: figure {n} has no caption. Every figure is captioned.")
        return f"FIG. {n} — " + md_inline(str(text))

    # -- text runs

    def text_run(self, text: str) -> list[dict[str, Any]]:
        """Split a raw run into headings and markdown chunks, in order."""
        blocks: list[dict[str, Any]] = []
        chunk: list[str] = []

        def flush() -> None:
            body = "\n".join(chunk).strip()
            chunk.clear()
            if not body:
                return
            html = md_to_html(body)
            if "<table>" in html:
                html = html.replace("<table>", '<table class="dtable">')
                html = re.sub(
                    r"(<table class=\"dtable\">.*?</table>)",
                    r'<div class="scroll-x">\1</div>',
                    html,
                    flags=re.DOTALL,
                )
            blocks.append({"type": "prose", "html": html})

        for line in text.split("\n"):
            heading = HEADING.match(line)
            if heading:
                flush()
                blocks.append(self.heading(len(heading.group("hashes")), heading.group("text")))
            else:
                chunk.append(line)
        flush()
        return blocks

    def heading(self, level: int, text: str) -> dict[str, Any]:
        if level == 2:
            self.section_n += 1
            clause = f"{self.entry.clause}.{self.section_n}"
            hid = slugify(text)
            self.sections.append({"id": hid, "clause": clause, "text": text})
            return {
                "type": "heading",
                "level": 2,
                "id": hid,
                "clause": clause,
                "alias": "c" + clause.replace(".", "-"),
                "text": text,
            }
        return {"type": "heading", "level": level, "id": slugify(text), "clause": "", "alias": "", "text": text}

    # -- directives

    def node(self, node: Any) -> list[dict[str, Any]]:
        if isinstance(node, str):
            return self.text_run(node)

        name = node["name"]
        attrs = node["attrs"]
        children = node["children"]
        raw = "\n".join(c for c in children if isinstance(c, str)).strip()

        handler = getattr(self, f"d_{name.replace('-', '_')}", None)
        if handler is None:
            raise ContentError(f"{self.where}: no renderer for ':::{name}'")
        return handler(attrs, children, raw)

    def d_lede(self, attrs, children, raw) -> list[dict[str, Any]]:
        return [{"type": "lede", "html": md_inline(raw)}]

    def d_note(self, attrs, children, raw) -> list[dict[str, Any]]:
        return [{"type": "note", "html": md_inline(raw)}]

    def d_terms(self, attrs, children, raw) -> list[dict[str, Any]]:
        items = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "::" not in line:
                raise ContentError(f"{self.where}: ':::terms' line is missing '::' — {line[:48]!r}")
            term, _, body = line.partition("::")
            items.append({"term": term.strip(), "html": md_inline(body.strip())})
        if not items:
            raise ContentError(f"{self.where}: empty ':::terms' block")
        return [{"type": "terms", "items": items}]

    def d_def(self, attrs, children, raw) -> list[dict[str, Any]]:
        term = attrs.get("term")
        if not term:
            raise ContentError(f"{self.where}: ':::def' needs term=\"...\"")
        return [{
            "type": "def",
            "term": str(term),
            "ref": str(attrs.get("ref", "")),
            "html": md_inline(raw),
        }]

    def d_diagram(self, attrs, children, raw) -> list[dict[str, Any]]:
        name = str(attrs.get("name", ""))
        if name not in DIAGRAMS:
            raise ContentError(
                f"{self.where}: unknown diagram {name!r}. Known: {', '.join(sorted(DIAGRAMS))}"
            )
        n = self.next_figure(attrs)
        return [{"type": "diagram", "name": name, "n": n, "caption": self.caption(attrs, n)}]

    def d_matrix(self, attrs, children, raw) -> list[dict[str, Any]]:
        n = self.next_figure(attrs)
        mark = str(attrs.get("mark", ""))
        cell = [int(x) for x in mark.split(",")] if mark else []
        return [{
            "type": "matrix",
            "n": n,
            "mark": cell,
            "caption": self.caption(attrs, n),
            "note": md_inline(str(attrs["note"])) if attrs.get("note") else "",
        }]

    def d_faq(self, attrs, children, raw) -> list[dict[str, Any]]:
        items: list[dict[str, str]] = []
        question: str | None = None
        buffer: list[str] = []

        def close() -> None:
            if question is None:
                return
            answer = "\n".join(buffer).strip()
            if not answer:
                raise ContentError(f"{self.where}: FAQ question {question!r} has no answer")
            items.append({"q": question, "id": "faq-" + slugify(question), "html": md_to_html(answer)})

        for line in raw.split("\n"):
            heading = HEADING.match(line)
            if heading and len(heading.group("hashes")) == 3:
                close()
                question = heading.group("text")
                buffer = []
            else:
                buffer.append(line)
        close()

        if not items:
            raise ContentError(f"{self.where}: ':::faq' has no '### question' headings")
        return [{"type": "faq", "items": items}]

    def d_versus(self, attrs, children, raw) -> list[dict[str, Any]]:
        """The two sides of an X-vs-Y entry. Separated by `+++`, like a split."""
        halves = re.split(rf"^{re.escape(COLUMN_BREAK)}\s*$", raw, flags=re.MULTILINE)
        if len(halves) != 2:
            raise ContentError(
                f"{self.where}: ':::versus' needs exactly one '{COLUMN_BREAK}' separator"
            )
        sides = []
        for key, body in zip(("a", "b"), halves):
            name = attrs.get(key)
            if not name:
                raise ContentError(f'{self.where}: \':::versus\' needs {key}="..."')
            sides.append({
                "name": str(name),
                "badge": str(attrs.get(f"{key}-badge", "")),
                "html": md_inline(body.strip()),
            })
        return [{"type": "versus", "sides": sides}]

    def d_attrs(self, attrs, children, raw) -> list[dict[str, Any]]:
        """The comparison table. Attribute rows keep the same order on every
        comparison entry, because the table is the snippet target and a reader
        comparing two of your pages is comparing two tables.

        A value prefixed `+` reads as a positive, `-` as a negative."""
        if not attrs.get("a") or not attrs.get("b"):
            raise ContentError(f'{self.where}: \':::attrs\' needs a="..." and b="..."')

        rows = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            cells = [c.strip() for c in line.split("::")]
            if len(cells) != 3:
                raise ContentError(
                    f"{self.where}: ':::attrs' row needs 'attribute :: a :: b' — {line[:48]!r}"
                )
            row = {"attr": cells[0]}
            for key, cell in zip(("a", "b"), cells[1:]):
                mark = ""
                if cell.startswith("+"):
                    mark, cell = "yes", cell[1:].strip()
                elif cell.startswith("-"):
                    mark, cell = "no", cell[1:].strip()
                row[key] = cell
                row[f"{key}v"] = mark
            rows.append(row)

        if not rows:
            raise ContentError(f"{self.where}: empty ':::attrs' block")
        return [{
            "type": "attrs",
            "a": str(attrs["a"]),
            "b": str(attrs["b"]),
            "rows": rows,
        }]

    def d_split(self, attrs, children, raw) -> list[dict[str, Any]]:
        columns: list[list[Any]] = [[]]
        for child in children:
            if isinstance(child, str):
                parts = re.split(rf"^{re.escape(COLUMN_BREAK)}\s*$", child, flags=re.MULTILINE)
                for i, part in enumerate(parts):
                    if i:
                        columns.append([])
                    if part.strip():
                        columns[-1].append(part)
            else:
                columns[-1].append(child)

        if len(columns) != 2:
            raise ContentError(
                f"{self.where}: ':::split' needs exactly one '+++' separator, found {len(columns) - 1}"
            )

        return [{
            "type": "split",
            "ratio": str(attrs.get("ratio", "1fr 1fr")),
            "columns": [self.walk(col) for col in columns],
        }]

    def d_col(self, attrs, children, raw) -> list[dict[str, Any]]:
        raise ContentError(f"{self.where}: ':::col' is not used — separate split columns with '{COLUMN_BREAK}'")

    # -- entry point

    def walk(self, nodes: list[Any]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for node in nodes:
            blocks.extend(self.node(node))
        return blocks


def parse_entry(entry: Entry) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    """Return (blocks, sections, figure count)."""
    nodes, _ = _tree(entry.body.split("\n"), 0, False, entry.source_path.name)
    builder = Builder(entry)
    blocks = builder.walk(nodes)
    return blocks, builder.sections, builder.figure_n
