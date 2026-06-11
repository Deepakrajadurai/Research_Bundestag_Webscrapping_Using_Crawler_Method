from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from govscraper.fetch import fetch_paginated_json_records
from govscraper.text_processing import clean_text, deduplicate_sentences, extract_text_candidates, label_sentence, split_sentences

TRAIN_RATIO = 0.8
VALIDATION_RATIO = 0.1


@dataclass
class SourceConfig:
    source_type: str
    endpoint: str
    records_key: str | None = None
    max_pages: int = 1
    params: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


def _split_records(records: list[dict[str, Any]], *, seed: int = 42) -> dict[str, list[dict[str, Any]]]:
    shuffled = records[:]
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    train_end = int(total * TRAIN_RATIO)
    val_end = int(total * (TRAIN_RATIO + VALIDATION_RATIO))
    return {
        "train": shuffled[:train_end],
        "validation": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def run_source_pipeline(config: SourceConfig) -> dict[str, dict[str, list[dict[str, Any]]]]:
    records = fetch_paginated_json_records(
        config.endpoint,
        params=config.params,
        headers=config.headers,
        records_key=config.records_key,
        max_pages=config.max_pages,
    )

    sentence_rows: list[dict[str, Any]] = []
    for record in records:
        for raw_text in extract_text_candidates(record):
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue
            for sentence in split_sentences(cleaned):
                labels = label_sentence(sentence=sentence, source_type=config.source_type)
                sentence_rows.append(
                    {
                        "text": sentence,
                        "source_type": config.source_type,
                        "domain": labels["domain"],
                        "quality_label": labels["quality_label"],
                    }
                )

    first_row_by_text: dict[str, dict[str, Any]] = {}
    for row in sentence_rows:
        first_row_by_text.setdefault(row["text"], row)
    unique_texts = deduplicate_sentences(list(first_row_by_text.keys()))
    unique_rows = [first_row_by_text[text] for text in unique_texts if text in first_row_by_text]

    corpora: dict[str, list[dict[str, Any]]] = {"debate": [], "legal": []}
    for row in unique_rows:
        corpora[row["domain"]].append(row)

    return {domain: _split_records(rows) for domain, rows in corpora.items()}


def write_jsonl_splits(
    split_corpora: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    output_dir: str,
) -> None:
    base = Path(output_dir)
    for domain, splits in split_corpora.items():
        domain_dir = base / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        for split_name, rows in splits.items():
            path = domain_dir / f"{split_name}.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
