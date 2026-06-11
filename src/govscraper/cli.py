from __future__ import annotations

import argparse
import json
from pathlib import Path

from govscraper.pipeline import SourceConfig, run_source_pipeline, write_jsonl_splits


def _load_json_if_present(value: str | None):
    if not value:
        return None
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="German government corpus scraping pipeline")
    parser.add_argument("--endpoint", required=True, help="Source API endpoint")
    parser.add_argument("--source-type", required=True, help="Source identifier, e.g. bundestag or bundesgesetzblatt")
    parser.add_argument("--records-key", default=None, help="Dot-path key that points to record list in JSON response")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum pages to fetch")
    parser.add_argument("--params", default=None, help="JSON string or file path for request query params")
    parser.add_argument("--headers", default=None, help="JSON string or file path for request headers")
    parser.add_argument("--output-dir", required=True, help="Output directory for per-domain split jsonl files")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = SourceConfig(
        source_type=args.source_type,
        endpoint=args.endpoint,
        records_key=args.records_key,
        max_pages=args.max_pages,
        params=_load_json_if_present(args.params),
        headers=_load_json_if_present(args.headers),
    )
    split_corpora = run_source_pipeline(config)
    write_jsonl_splits(split_corpora, output_dir=args.output_dir)


if __name__ == "__main__":
    main()

