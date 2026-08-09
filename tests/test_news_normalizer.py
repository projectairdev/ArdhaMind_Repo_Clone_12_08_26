import pytest
from src.news_engine.normalizer import NewsNormalizer, clean_html_text

def test_html_tag_stripping():
    raw_html = "<table><tr><td><span>RBI Announcement: Policy Rate unchanged at 6.5%</span></td></tr></table>"
    cleaned = clean_html_text(raw_html)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "RBI Announcement: Policy Rate unchanged at 6.5%" in cleaned

def test_news_normalizer_rbi_html():
    raw_article = {
        "title": "<span>RBI Press Release</span>",
        "description": "<table><tr><td>Monetary Policy Committee decision details</td></tr></table>",
        "source": "RBI Press Releases",
        "pubDate": "Fri, 07 Aug 2026 12:00:00 GMT"
    }
    normalized = NewsNormalizer.normalize_google_article(raw_article)
    assert "<" not in normalized["title"]
    assert "<" not in normalized["content"]
    assert "Monetary Policy Committee decision details" in normalized["content"]
