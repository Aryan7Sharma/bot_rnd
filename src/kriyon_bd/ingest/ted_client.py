"""Client for the TED (Tenders Electronic Daily) Search API v3.

Built against the documented contract — POST /v3/notices/search, expert
query syntax, kebab-case eForms field names, no auth required — sourced
from third-party references. This sandbox's network policy blocks both
api.ted.europa.eu and docs.ted.europa.eu, so the exact request/response
shape has NOT been verified against a live call. See README.md's
"Known limitation" section before relying on this for real ingestion;
`build_expert_query` is kept pure and separately testable so its syntax
can be fixed in one place once verified live.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterator, Optional

import httpx

from kriyon_bd.logging_conf import get_logger
from kriyon_bd.settings import CONFIG_DIR

logger = get_logger(__name__)

RESULT_FIELDS = [
    "publication-number",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "classification-cpv",
    "publication-date",
    "deadline-receipt-request",
    "links",
    "contact-point",
]


@dataclass(frozen=True)
class TedSourceConfig:
    countries: list[str]
    scope: str
    page_size: int
    lookback_days: int
    sort: str
    cpv_codes: list[str]
    main_activities: list[str]
    keywords: list[str]

    @classmethod
    def load(cls) -> "TedSourceConfig":
        with open(CONFIG_DIR / "sources.toml", "rb") as f:
            data = tomllib.load(f)
        ted = data["ted"]
        return cls(
            countries=ted["countries"],
            scope=ted["scope"],
            page_size=ted["page_size"],
            lookback_days=ted["lookback_days"],
            sort=ted["sort"],
            cpv_codes=ted["cpv_codes"],
            main_activities=ted.get("main_activities", []),
            keywords=ted.get("keywords", []),
        )


def build_expert_query(config: TedSourceConfig, since: Optional[date] = None) -> str:
    """Build the TED expert-search query string: buyer country AND
    (CPV code OR keyword full-text match) AND a publication-date floor.
    """
    since = since or (date.today() - timedelta(days=config.lookback_days))

    country_clause = " OR ".join(f"buyer-country={c}" for c in config.countries)
    scope_terms = []
    if config.cpv_codes:
        scope_terms.append(" OR ".join(f"classification-cpv={code}" for code in config.cpv_codes))
    if config.keywords:
        scope_terms.append(" OR ".join(f'FT~"{term}"' for term in config.keywords))

    clauses = [f"({country_clause})"]
    if scope_terms:
        clauses.append(f"({' OR '.join(scope_terms)})")
    clauses.append(f"publication-date>={since.strftime('%Y%m%d')}")

    return " AND ".join(clauses) + f" SORT BY {config.sort}"


class TedClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def search(self, config: TedSourceConfig, since: Optional[date] = None) -> Iterator[dict[str, Any]]:
        """Yield raw notice dicts across all pages for the given config."""
        query = build_expert_query(config, since=since)
        page = 1
        seen = 0
        while True:
            body = {
                "query": query,
                "fields": RESULT_FIELDS,
                "page": page,
                "limit": config.page_size,
                "scope": config.scope,
                "paginationMode": "PAGE_NUMBER",
            }
            logger.info("ted_search_request", page=page, query=query)
            response = self._client.post(f"{self._base_url}/notices/search", json=body)
            response.raise_for_status()
            payload = response.json()
            notices = payload.get("notices", [])
            if not notices:
                break
            yield from notices
            seen += len(notices)
            total = payload.get("totalNoticeCount", seen)
            if seen >= total or len(notices) < config.page_size:
                break
            page += 1

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TedClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
