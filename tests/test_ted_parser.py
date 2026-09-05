from datetime import datetime, timezone

from kriyon_bd.ingest.ted_parser import parse_contact_point, parse_notice

SAMPLE_NOTICE = {
    "publication-number": "477851-2026",
    "notice-title": {"eng": "Terminal operating system upgrade", "deu": "TOS-Modernisierung"},
    "buyer-name": {"eng": "Hamburg Port Authority"},
    "buyer-country": "DEU",
    "classification-cpv": ["72000000", "48000000"],
    "publication-date": "2026-08-01",
    "deadline-receipt-request": "2026-10-01",
    "links": {"html": {"eng": "https://ted.europa.eu/en/notice/-/detail/477851-2026"}},
    "contact-point": {
        "name": {"eng": "Jane Doe"},
        "role": {"eng": "Procurement officer"},
        "email": "jane.doe@example.eu",
        "phone": "+49 40 1234567",
    },
}


def test_parse_notice_extracts_core_fields():
    signal = parse_notice(SAMPLE_NOTICE, retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc))

    assert signal.source == "ted"
    assert signal.source_id == "477851-2026"
    assert signal.title == "Terminal operating system upgrade"
    assert signal.buyer_name == "Hamburg Port Authority"
    assert signal.country == "DEU"
    assert signal.cpv_codes == ["72000000", "48000000"]
    assert signal.publication_date.isoformat() == "2026-08-01"
    assert signal.deadline_date.isoformat() == "2026-10-01"
    assert signal.source_url == "https://ted.europa.eu/en/notice/-/detail/477851-2026"
    assert signal.raw_payload == SAMPLE_NOTICE


def test_parse_notice_falls_back_to_template_url_without_links():
    raw = {**SAMPLE_NOTICE, "links": None}
    signal = parse_notice(raw)
    assert signal.source_url == "https://ted.europa.eu/en/notice/-/detail/477851-2026"


def test_parse_notice_handles_missing_title_and_buyer():
    signal = parse_notice({"publication-number": "1-2026"})
    assert signal.title == "(untitled TED notice)"
    assert signal.buyer_name is None


def test_content_hash_is_deterministic_for_identical_input():
    a = parse_notice(SAMPLE_NOTICE)
    b = parse_notice(SAMPLE_NOTICE)
    assert a.content_hash == b.content_hash


def test_content_hash_differs_for_different_title():
    a = parse_notice(SAMPLE_NOTICE)
    other = {**SAMPLE_NOTICE, "notice-title": {"eng": "Something else entirely"}}
    b = parse_notice(other)
    assert a.content_hash != b.content_hash


def test_parse_contact_point_extracts_named_contact():
    signal = parse_notice(SAMPLE_NOTICE)
    contact = parse_contact_point(SAMPLE_NOTICE, signal)

    assert contact is not None
    assert contact.name == "Jane Doe"
    assert contact.email == "jane.doe@example.eu"
    assert contact.source_url == signal.source_url
    assert contact.legitimate_interest_basis  # non-empty, mandatory per GDPR constraint


def test_parse_contact_point_returns_none_when_absent():
    raw = {**SAMPLE_NOTICE, "contact-point": None}
    signal = parse_notice(raw)
    assert parse_contact_point(raw, signal) is None
