from govscraper.pipeline import SourceConfig, run_source_pipeline


def test_run_source_pipeline_splits_by_domain(monkeypatch):
    sample_records = [
        {"text": "Die Sitzung ist eröffnet. Wir starten jetzt."},
        {"text": "§ 1 Dieses Gesetz gilt für alle."},
    ]

    def fake_fetch(*args, **kwargs):
        return sample_records

    monkeypatch.setattr("govscraper.pipeline.fetch_paginated_json_records", fake_fetch)
    config = SourceConfig(source_type="bundesgesetzblatt", endpoint="https://example.org")
    output = run_source_pipeline(config)

    assert set(output.keys()) == {"debate", "legal"}
    assert sum(len(rows) for rows in output["legal"].values()) > 0

