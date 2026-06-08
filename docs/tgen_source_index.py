#!/usr/bin/env python3
"""Build a tgen qualified-name -> source location index from Doxygen XML."""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

TGEN_REPO = "brunomaletta/tgen"
TGEN_DOCS_BASE = "https://brunomaletta.github.io/tgen"
TGEN_DEFAULT_PATH = "single_include/tgen.h"


def doxygen_docs_url(member_id: str) -> str:
    if "_1" in member_id:
        page, anchor = member_id.split("_1", 1)
        return f"{TGEN_DOCS_BASE}/{page}.html#{anchor}"
    return f"{TGEN_DOCS_BASE}/{member_id}.html"


def _repo_relative_path(abs_path: str) -> str:
    if "single_include/" in abs_path:
        return "single_include/" + abs_path.split("single_include/", 1)[1]
    return os.path.basename(abs_path)


def build_index(xml_dir: str) -> dict[str, dict[str, str | int]]:
    index: dict[str, dict[str, str | int]] = {}
    if not os.path.isdir(xml_dir):
        return index

    skip = {
        "index.xml",
        "Doxyfile.xml",
        "combine.xslt",
        "compound.xsd",
        "doxyfile.xsd",
    }
    for fname in os.listdir(xml_dir):
        if not fname.endswith(".xml") or fname in skip:
            continue
        path = os.path.join(xml_dir, fname)
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        for member in root.iter("memberdef"):
            if member.get("kind") not in ("function", "variable", "typedef"):
                continue
            qname = member.findtext("qualifiedname") or member.findtext("name")
            if not qname:
                continue
            location = member.find("location")
            if location is None or not location.get("line"):
                continue
            member_id = member.get("id")
            if not member_id:
                continue
            index[qname] = {
                "path": _repo_relative_path(location.get("file", TGEN_DEFAULT_PATH)),
                "line": int(location.get("line")),
                "member_id": member_id,
            }
    return index


def github_blob_url(
    sha: str, path: str, line: int | None, repo: str = TGEN_REPO
) -> str:
    url = f"https://github.com/{repo}/blob/{sha}/{path}"
    if line is not None:
        url += f"#L{line}"
    return url


class TgenSourceIndex:
    def __init__(self, xml_dir: str):
        self._index = build_index(xml_dir)

    def lookup(self, symbol: str) -> dict[str, str | int] | None:
        return self._index.get(symbol)

    def github_url(self, symbol: str, sha: str) -> str | None:
        loc = self.lookup(symbol)
        if not loc:
            return None
        return github_blob_url(sha, str(loc["path"]), int(loc["line"]))

    def docs_url(self, symbol: str) -> str | None:
        loc = self.lookup(symbol)
        if not loc:
            return None
        member_id = loc.get("member_id")
        if not member_id:
            return None
        return doxygen_docs_url(str(member_id))

    def __len__(self) -> int:
        return len(self._index)


def default_xml_dir(root: str | None = None) -> str:
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "vendor", "tgen", "docs", "build", "xml")


def read_git_sha(vendor_dir: str) -> str | None:
    git_dir = os.path.join(vendor_dir, ".git")
    head_path = os.path.join(git_dir, "HEAD")
    if not os.path.isfile(head_path):
        return None
    with open(head_path, encoding="utf-8") as f:
        head = f.read().strip()
    if head.startswith("ref: "):
        ref_path = os.path.join(git_dir, head[5:])
        if not os.path.isfile(ref_path):
            return None
        with open(ref_path, encoding="utf-8") as f:
            return f.read().strip()
    return head


if __name__ == "__main__":
    xml_dir = default_xml_dir()
    index = TgenSourceIndex(xml_dir)
    if len(index) == 0:
        sys.stderr.write(
            "tgen_source_index: no symbols (run: cd vendor/tgen && make doc-prepare)\n"
        )
        sys.exit(1)
    print(f"tgen_source_index: {len(index)} symbols from {xml_dir}")
