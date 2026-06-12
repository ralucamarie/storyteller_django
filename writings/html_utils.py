import html
import re

import bleach
from django.utils.html import strip_tags

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "h2",
    "h3",
    "blockquote",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "class", "width", "height", "loading"],
}


def looks_like_html(value: str) -> bool:
    stripped = (value or "").lstrip()
    return stripped.startswith("<") and ">" in stripped


def sanitize_writing_html(value: str) -> str:
    if not value:
        return ""

    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return cleaned.strip()


def html_to_plain_text(value: str) -> str:
    if not value:
        return ""
    if not looks_like_html(value):
        return value.strip()
    text = strip_tags(value)
    return html.unescape(re.sub(r"\n{3,}", "\n\n", text)).strip()


def is_writing_html_empty(value: str) -> bool:
    if not value or not str(value).strip():
        return True
    if not looks_like_html(value):
        return not str(value).strip()
    plain = html_to_plain_text(value)
    if plain:
        return False
    return "img" not in value.lower()


def plain_text_to_html(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if looks_like_html(text):
        return sanitize_writing_html(text)

    parts = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        escaped = html.escape(paragraph).replace("\n", "<br>")
        parts.append(f"<p>{escaped}</p>")
    return "".join(parts) if parts else f"<p>{html.escape(text).replace(chr(10), '<br>')}</p>"
