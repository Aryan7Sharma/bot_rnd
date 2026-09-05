from datetime import date

from kriyon_bd.digest.markdown_digest import render_digest

SAMPLE_ROW = {
    "title": "Terminal operating system upgrade",
    "summary": "Hamburg Port Authority is upgrading its TOS.",
    "source_url": "https://ted.europa.eu/en/notice/-/detail/477851-2026",
    "buyer_name": "Hamburg Port Authority",
    "country": "DEU",
    "deadline_date": date(2026, 10, 1),
    "rubric_version": "0.1.0",
    "total_score": 17,
    "fit_score": 5,
    "fit_justification": "Directly a TOS migration.",
    "timing_score": 4,
    "timing_justification": "Hard tender deadline of 2026-10-01.",
    "reachability_score": 4,
    "reachability_justification": "Mid-size regional port authority.",
    "evidence_score": 4,
    "evidence_justification": "Official TED notice.",
}


def test_render_digest_includes_signal_details():
    content = render_digest([SAMPLE_ROW], date(2026, 9, 5))

    assert "Kriyon BD Signal Digest — 2026-09-05" in content
    assert "1 signal(s) surfaced." in content
    assert "Terminal operating system upgrade" in content
    assert "score: 17/20" in content
    assert SAMPLE_ROW["source_url"] in content
    assert "Directly a TOS migration." in content


def test_render_digest_handles_no_surfaced_signals():
    content = render_digest([], date(2026, 9, 5))
    assert "No signals cleared the surfacing threshold today." in content
