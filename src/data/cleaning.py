"""Module for cleaning the data."""

import re
from collections.abc import Callable

import pandas as pd

# Wire service markers
_RE_REUTERS_DATELINE = re.compile(r"^[A-Z][A-Z\s/]+ \(Reuters\)\s*-?\s*")
_RE_WIRE_PARENS = re.compile(r"\((?:Reuters|AP|AFP)\)")
_RE_REUTERS_WORD = re.compile(r"\breuters\b", re.IGNORECASE)

# URLs
_RE_URL_HTTP = re.compile(r"https?://\S+")
_RE_URL_WWW = re.compile(r"www\.\S+")
_RE_URL_TWITTER_PIC = re.compile(r"pic\.twitter\.com/\S+")
_RE_URL_TMSNRT = re.compile(r"tmsnrt\.rs/\S+")

# Social handles
_RE_SOCIAL_VIA_HANDLE = re.compile(r"\bvia\s+@\w+", re.IGNORECASE)
_RE_SOCIAL_HANDLE = re.compile(r"@\w+")
_RE_SOCIAL_AT = re.compile(r"@")

# Clickbait prefixes
_RE_CLICKBAIT_PREFIX = re.compile(
    r"^(?:VIDEO|WATCH|BREAKING|SHOCK)\s*[:!]\s*", re.IGNORECASE
)

# Image / photo credit templates
_RE_CREDIT_FEATURED = re.compile(
    r"featured\s+image\s+via\s+[^.]*?(?:getty|flickr|shutterstock|ap)\s*(?:images)?",
    re.IGNORECASE,
)
_RE_CREDIT_PHOTO = re.compile(
    r"(?:photo|image|screenshot|screen\s+capture)\s+(?:by|via|from|credit)\s*:?\s*[^.]*?(?:getty|flickr|ap|reuters|afp)\s*(?:images)?",
    re.IGNORECASE,
)
_RE_CREDIT_GETTY_FULL = re.compile(r"getty\s+images?", re.IGNORECASE)
_RE_CREDIT_GETTY_BARE = re.compile(r"\bgetty\b", re.IGNORECASE)
_RE_CREDIT_IMAGE_VIDEO = re.compile(
    r"(?:featured\s+)?image\s*/?\s*video", re.IGNORECASE
)

# HTML and scraping artifacts
_RE_HTML_SCRIPT = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL)
_RE_HTML_TAG = re.compile(r"<[^>]+>")
_RE_HTML_ENTITY = re.compile(r"&(?:amp|quot|lt|gt|nbsp);?")

# Site-specific templates
_RE_SITE_21CW = re.compile(r"21st\s+century\s+wire", re.IGNORECASE)

# Structural fixes
_RE_FIX_YEAR_WORD = re.compile(r"(\d{4})([A-Z])")

# Normalisation
_RE_WHITESPACE = re.compile(r"\s+")
_RE_SINGLE_CHAR_TOKEN = re.compile(r"\b\w\b")
_RE_REUTERS_LOWER = re.compile(r"\breuters\b")  # case-sensitive: runs after lowercasing


def clean_text(text: str) -> str:
    """Remove leakage markers and normalise whitespace in a raw news article."""
    for step in _PIPELINE:
        text = step(text)
    return text


def filter_short_articles(df: pd.DataFrame, min_words: int = 10) -> pd.DataFrame:
    """Filter out articles with fewer than min_words words after cleaning.

    Args:
        df: DataFrame with a 'text' column (already cleaned).
        min_words: Minimum word count threshold.

    Returns:
        Filtered DataFrame with short articles removed.
    """
    word_counts = df["text"].str.split().str.len().fillna(0)
    mask = word_counts >= min_words
    return df[mask].reset_index(drop=True)


def _remove_wire_markers(text: str) -> str:
    """Remove Reuters dateline prefixes and parenthetical wire service attributions."""
    text = _RE_REUTERS_DATELINE.sub("", text)
    text = _RE_WIRE_PARENS.sub("", text)
    text = _RE_REUTERS_WORD.sub("", text)
    return text


def _remove_urls(text: str) -> str:
    """Remove HTTP/HTTPS URLs, bare www addresses, and known short-link domains."""
    text = _RE_URL_HTTP.sub("", text)
    text = _RE_URL_WWW.sub("", text)
    text = _RE_URL_TWITTER_PIC.sub("", text)
    text = _RE_URL_TMSNRT.sub("", text)
    return text


def _remove_social_handles(text: str) -> str:
    """Remove social handles, 'via @handle' constructions, and bare @ signs."""
    text = _RE_SOCIAL_VIA_HANDLE.sub("", text)  # must precede bare handle removal
    text = _RE_SOCIAL_HANDLE.sub("", text)
    text = _RE_SOCIAL_AT.sub("", text)
    return text


def _remove_clickbait_prefix(text: str) -> str:
    """Strip VIDEO/WATCH/BREAKING/SHOCK prefixes from the start of the text."""
    return _RE_CLICKBAIT_PREFIX.sub("", text)


def _remove_image_credits(text: str) -> str:
    """Remove photo/image credit templates and standalone Getty attributions."""
    text = _RE_CREDIT_FEATURED.sub("", text)
    text = _RE_CREDIT_PHOTO.sub("", text)
    text = _RE_CREDIT_GETTY_FULL.sub("", text)  # must precede bare getty removal
    text = _RE_CREDIT_GETTY_BARE.sub("", text)
    text = _RE_CREDIT_IMAGE_VIDEO.sub("", text)
    return text


def _remove_html_artifacts(text: str) -> str:
    """Strip script blocks, HTML tags, and HTML entities."""
    text = _RE_HTML_SCRIPT.sub("", text)
    text = _RE_HTML_TAG.sub("", text)
    text = _RE_HTML_ENTITY.sub("", text)
    return text


def _remove_site_templates(text: str) -> str:
    """Remove known site-specific boilerplate strings."""
    return _RE_SITE_21CW.sub("", text)


def _fix_year_word_join(text: str) -> str:
    """Insert a space between a 4-digit year and a directly following uppercase word."""
    return _RE_FIX_YEAR_WORD.sub(r"\1 \2", text)


def _normalize_whitespace(text: str) -> str:
    """Collapse all whitespace to single spaces and strip ends."""
    return _RE_WHITESPACE.sub(" ", text).strip()


def _normalize_case_and_tokens(text: str) -> str:
    """Lowercase, remove single-character tokens, and re-collapse whitespace."""
    text = text.lower()
    text = _RE_SINGLE_CHAR_TOKEN.sub("", text)
    return _RE_WHITESPACE.sub(" ", text).strip()


def _remove_reuters_post_lower(text: str) -> str:
    """Second-pass reuters removal: catches residuals that survive after lowercasing."""
    text = _RE_REUTERS_LOWER.sub("", text)
    return _RE_WHITESPACE.sub(" ", text).strip()


_PIPELINE: list[Callable[[str], str]] = [
    _remove_wire_markers,
    _remove_urls,
    _remove_social_handles,
    _remove_clickbait_prefix,
    _remove_image_credits,
    _remove_html_artifacts,
    _remove_site_templates,
    _fix_year_word_join,  # must precede lowercasing: relies on [A-Z]
    _normalize_whitespace,
    _normalize_case_and_tokens,  # lowercase + single-char removal
    _remove_reuters_post_lower,  # second pass on now-lowercase text
]
