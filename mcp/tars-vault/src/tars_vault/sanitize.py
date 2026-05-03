"""Sanitization helpers for Obsidian-safe text and wikilink targets.

Single source of truth for two things:

  1. Smart-quote and whitespace normalization. Obsidian wikilink resolution
     compares targets byte-for-byte; "Café's" with a curly apostrophe will
     not match "Café's" with a straight apostrophe.

  2. Obsidian filename sanitization. The set of characters Obsidian forbids
     in note filenames is `\ / : * ? " < > | [ ] # ^`. We replace these with
     a single hyphen. Apostrophes and spaces are preserved intentionally —
     Obsidian allows them and round-trips them through wikilinks.

The constants and functions here are pure: no IO, no vault access. Other
modules (wikilink.py, validators.py, scripts/fix-wikilinks.py) compose
these to do the real work.
"""
from __future__ import annotations

import re
import unicodedata


# Smart / typographic punctuation that the user often pastes into chat but
# that Obsidian's wikilink resolver treats as different from the ASCII form.
SMART_QUOTE_MAP: dict[str, str] = {
    "‘": "'",  # left single quote
    "’": "'",  # right single quote / curly apostrophe
    "‚": "'",  # single low-9 quote
    "‛": "'",  # single high-reversed-9 quote
    "“": '"',  # left double quote
    "”": '"',  # right double quote
    "„": '"',  # double low-9 quote
    "‟": '"',  # double high-reversed-9 quote
    "′": "'",  # prime
    "″": '"',  # double prime
    "–": "-",  # en dash
    "—": "-",  # em dash
    "…": "...",  # ellipsis
}


# Characters Obsidian forbids in note filenames (and therefore in wikilink
# targets). `[`, `]`, `#`, `^` are wikilink syntax; the rest are filesystem-
# illegal on Windows or path separators.
FORBIDDEN_FN_CHARS: frozenset[str] = frozenset('\\/:*?"<>|[]#^')


_WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Normalize user-provided reference text.

    Steps: NFC unicode normalization, smart-quote folding, whitespace
    collapse, leading/trailing strip. Pure.
    """
    if not text:
        return ""
    out = unicodedata.normalize("NFC", text)
    for src, dst in SMART_QUOTE_MAP.items():
        if src in out:
            out = out.replace(src, dst)
    out = _WS_RE.sub(" ", out).strip()
    return out


def sanitize_basename(name: str) -> str:
    """Return an Obsidian-safe filename basename (no .md extension).

    Replaces forbidden characters with a space, then collapses runs of
    whitespace. Preserves apostrophes and case. Returns "" for input that
    becomes empty after sanitization. The result is what we'd recommend the
    user create on disk if they choose to materialize this entity.
    """
    if not name:
        return ""
    name = normalize_text(name)
    out_chars: list[str] = []
    for ch in name:
        if ch in FORBIDDEN_FN_CHARS:
            out_chars.append(" ")
        else:
            out_chars.append(ch)
    out = "".join(out_chars)
    out = _WS_RE.sub(" ", out).strip()
    return out


# ---------------------------------------------------------------------------
# Wikilink scanning (used by validators and the pre-tool-use hook).
# ---------------------------------------------------------------------------


# Match `[[target]]` and `[[target|display]]`. Captures the link target only.
# Permissive on what's inside: we want to *find* offenders, not exclude them.
_WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")


def _split_target(raw: str) -> tuple[str, str | None, str | None]:
    """Split a wikilink target into (basename, heading, display).

    `Foo#Bar|baz` → ("Foo", "Bar", "baz"). `Foo` → ("Foo", None, None).
    Block IDs (`Foo#^abc`) come back as headings starting with `^`.
    """
    body = raw
    display: str | None = None
    if "|" in body:
        body, display = body.split("|", 1)
    heading: str | None = None
    if "#" in body:
        body, heading = body.split("#", 1)
    return body, heading, display


def scan_wikilinks(content: str) -> list[dict[str, str]]:
    """Return a list of wikilinks in ``content`` with hygiene findings.

    Each entry: {raw, basename, issue}. ``issue`` is one of:
      * ``"smart_quote"`` — basename or display contains smart punctuation
      * ``"illegal_char"`` — basename contains a character forbidden in
        Obsidian filenames (excluding the wikilink syntax chars `#` and `|`,
        which are valid here when separating heading/display)
      * ``"empty"`` — basename is empty after splitting
      * ``""`` — clean, no issue (callers can ignore these)

    Pure; takes plain string content, returns plain dicts.
    """
    out: list[dict[str, str]] = []
    for match in _WIKILINK_RE.finditer(content):
        raw = match.group(1)
        basename, _heading, display = _split_target(raw)
        basename = basename.strip()
        issue = ""
        if not basename:
            issue = "empty"
        elif any(ch in SMART_QUOTE_MAP for ch in raw):
            issue = "smart_quote"
        else:
            # Restrict the forbidden-set to chars that are illegal *inside*
            # the basename (not # or | which separate heading/display).
            inline_forbidden = FORBIDDEN_FN_CHARS - {"#", "|", "[", "]"}
            if any(ch in inline_forbidden for ch in basename):
                issue = "illegal_char"
        out.append({"raw": raw, "basename": basename, "issue": issue})
    return out


def find_bad_wikilinks(content: str) -> list[dict[str, str]]:
    """Return only the entries from :func:`scan_wikilinks` that have an issue."""
    return [item for item in scan_wikilinks(content) if item["issue"]]
