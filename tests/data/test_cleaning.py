"""Golden tests for the regex cleaning pipeline.

Each marker class identified in the leakage analysis must be removed by
``clean_text``; the final output is always lower-cased, single-spaced, and free
of single-character tokens. Tests assert on substrings rather than exact strings
so they stay robust to incidental spacing.
"""

import pandas as pd

from src.data.cleaning import clean_text, filter_short_articles


def test_reuters_dateline_prefix_removed() -> None:
    out = clean_text("WASHINGTON (Reuters) - The Senate voted today.")
    assert "reuters" not in out
    assert "washington" not in out  # dateline city stripped with the prefix
    assert "the senate voted today" in out


def test_wire_parens_and_word_removed() -> None:
    assert "reuters" not in clean_text("A report (Reuters) said reuters things")
    assert "(ap)" not in clean_text("Filed (AP) overnight")


def test_urls_removed() -> None:
    out = clean_text(
        "see http://x.co/a and www.y.com pic.twitter.com/z and tmsnrt.rs/q"
    )
    for marker in ("http", "www.", "pic.twitter", "tmsnrt"):
        assert marker not in out


def test_social_handles_removed() -> None:
    out = clean_text("Trump said via @realDonaldTrump that @CNN is fake")
    assert "@" not in out
    assert "realdonaldtrump" not in out
    assert "cnn" not in out


def test_clickbait_prefix_removed() -> None:
    assert clean_text("VIDEO: something happened").startswith("something")
    assert clean_text("BREAKING! news here").startswith("news")


def test_image_credits_removed() -> None:
    out = clean_text("A story. Featured image via Getty Images.")
    assert "getty" not in out
    assert "featured image" not in out


def test_html_artifacts_removed() -> None:
    out = clean_text("<p>Hello</p> &amp; goodbye <script>evil()</script>")
    assert "<" not in out and ">" not in out
    assert "amp" not in out
    assert "evil" not in out


def test_site_template_removed() -> None:
    assert "21st century wire" not in clean_text("Reported by 21st Century Wire staff")


def test_year_word_join_fixed() -> None:
    assert "2017 the" in clean_text("In 2017The economy grew")


def test_single_char_tokens_removed_and_lowercased() -> None:
    out = clean_text("A B cat dog E")
    assert out == "cat dog"


def test_output_is_single_spaced_and_stripped() -> None:
    out = clean_text("  too    much\twhitespace  ")
    assert out == "too much whitespace"


def test_filter_short_articles_boundary() -> None:
    df = pd.DataFrame({"text": ["one two three", "a b c d e f g h i j", "short"]})
    # min_words=10 keeps only the 10-word row.
    kept = filter_short_articles(df, min_words=10)
    assert len(kept) == 1
    assert kept.loc[0, "text"] == "a b c d e f g h i j"


def test_filter_short_articles_handles_empty_text() -> None:
    df = pd.DataFrame({"text": ["", "plenty of words here now ok go on more words"]})
    kept = filter_short_articles(df, min_words=5)
    assert len(kept) == 1
