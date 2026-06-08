"""Line-oriented C++ syntax highlighting for bundled source viewers."""

from __future__ import annotations

import html

try:
    from pygments import lex
    from pygments.lexers import CppLexer
    from pygments.token import Token

    _HAS_PYGMENTS = True
except ImportError:
    _HAS_PYGMENTS = False

_TOKEN_CLASS: dict = {}
if _HAS_PYGMENTS:
    _TOKEN_CLASS = {
        Token.Keyword: "tok-kw",
        Token.Keyword.Type: "tok-type",
        Token.Name.Builtin: "tok-type",
        Token.Name.Class: "tok-type",
        Token.Name.Function: "tok-fn",
        Token.Name.Namespace: "tok-type",
        Token.Comment: "tok-cm",
        Token.String: "tok-str",
        Token.Number: "tok-num",
        Token.Operator: "tok-op",
        Token.Punctuation: "tok-op",
        Token.Preprocessor: "tok-pp",
        Token.Literal: "tok-num",
    }


def _class_for(ttype) -> str:
    while ttype is not None:
        cls = _TOKEN_CLASS.get(ttype)
        if cls:
            return cls
        ttype = ttype.parent
    return ""


def highlight_cpp_file(content: str) -> list[str]:
    """Return highlighted HTML for each line (no wrapping elements)."""
    lines = content.splitlines()
    if not lines:
        return []
    if not _HAS_PYGMENTS:
        return [html.escape(line) for line in lines]

    out: list[list[str]] = [[] for _ in lines]
    cur = 0
    for ttype, value in lex(content, CppLexer(stripall=False)):
        css = _class_for(ttype)
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                cur += 1
            if not part or cur >= len(out):
                continue
            chunk = html.escape(part)
            if css:
                chunk = f'<span class="{css}">{chunk}</span>'
            out[cur].append(chunk)
    return ["".join(segs) for segs in out]
