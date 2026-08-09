from src.news_engine.normalizer import clean_html_text


def test_complex_rbi_html_is_plain_text_and_bounded():
    raw = "<table><tr><td><span>RBI &amp; SEBI</span></td></tr></table><script>alert(1)</script>" + (" x" * 400)
    result = clean_html_text(raw, max_length=120)
    assert "<" not in result and ">" not in result
    assert "RBI & SEBI" in result
    assert "alert" not in result
    assert len(result) <= 123


def test_malformed_provider_markup_is_not_published_as_markup():
    result = clean_html_text("<div>Policy <b>update</div>&nbsp;&nbsp; today")
    assert result == "Policy update today"
