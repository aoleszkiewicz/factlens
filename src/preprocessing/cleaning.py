"""Module for cleaning the data."""

import re

import pandas as pd


def clean_text(text: str) -> str:
    """Cleans the text by removing metadata artifacts while preserving content signals."""

    # Remove wire service markers (Reuters, AP, AFP)
    text = re.sub(r"^[A-Z][A-Z\s/]+ \(Reuters\)\s*-?\s*", "", text)
    text = re.sub(r"\((?:Reuters|AP|AFP)\)", "", text)
    text = re.sub(r"\breuters\b", "", text, flags=re.IGNORECASE)

    # URLs, twitter handles
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"pic\.twitter\.com/\S+", "", text)
    text = re.sub(r"tmsnrt\.rs/\S+", "", text)
    text = re.sub(r"@\w+", "", text)

    # Photo/video credit templates (remove full template, keep individual words)
    text = re.sub(
        r"featured\s+image\s+via\s+[^.]*?(?:getty|flickr|shutterstock|ap)\s*(?:images)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?:photo|image|screenshot|screen\s+capture)\s+(?:by|via|from|credit)\s*:?\s*[^.]*?(?:getty|flickr|ap|reuters|afp)\s*(?:images)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"getty\s+images?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:featured\s+)?image\s*/?\s*video", "", text, flags=re.IGNORECASE)

    # HTML and scraping artifacts
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&(?:amp|quot|lt|gt|nbsp);?", "", text)

    # Site-specific templates
    text = re.sub(r"21st\s+century\s+wire", "", text, flags=re.IGNORECASE)

    # Fix malformed date-word joins (e.g. "2017Trump" -> "2017 Trump")
    text = re.sub(r"(\d{4})([A-Z])", r"\1 \2", text)

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b\w\b", "", text)
    text = text.lower().strip()

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
