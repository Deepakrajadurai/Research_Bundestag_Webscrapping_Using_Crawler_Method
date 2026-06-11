from __future__ import annotations

from typing import Any

import requests

DEFAULT_PAGE_SIZE = 100


def _extract_records(payload: Any, records_key: str | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    if records_key:
        node: Any = payload
        for part in records_key.split("."):
            if not isinstance(node, dict):
                return []
            node = node.get(part)
        if isinstance(node, list):
            return [item for item in node if isinstance(item, dict)]
        return []

    for candidate_key in ("documents", "items", "results", "data"):
        node = payload.get(candidate_key)
        if isinstance(node, list):
            return [item for item in node if isinstance(item, dict)]
    return [payload]


def fetch_paginated_json_records(
    base_url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    records_key: str | None = None,
    max_pages: int = 1,
    page_param: str = "page",
    page_size_param: str = "limit",
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout_seconds: int = 30,
) -> list[dict[str, Any]]:
    all_records: list[dict[str, Any]] = []
    base_params = dict(params or {})
    page = 1

    while page <= max_pages:
        request_params = dict(base_params)
        request_params[page_param] = page
        request_params[page_size_param] = page_size
        response = requests.get(base_url, params=request_params, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        page_records = _extract_records(payload, records_key)
        if not page_records:
            break
        all_records.extend(page_records)
        if len(page_records) < page_size:
            break
        page += 1

    return all_records
