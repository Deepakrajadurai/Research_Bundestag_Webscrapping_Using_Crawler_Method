# Research_Bundestag_Webscrapping_Using_Crawler_Method

This repository contains the implementation planning blueprint for building a high-quality German public-sector text corpus for model training.

## Goal

Build a **noise-minimized, model-ready dataset** from federal and state-level German government debate/legal corpora:

- Federal level (Bund): ~200,000 sentences
- State parliaments (Länder, 16 states): ~300,000 sentences
- Total target: ~500,000 sentences

## Scope and Source Priorities

### P1 (must implement first)

#### Federal
1. **Bundestag Plenarprotokolle** (WP 18–21, speeches since 2013)  
   - Format: API XML  
   - URLs: `dip.bundestag.de`, `bundestag.de/services/opendata`  
   - Est. sentences: ~120,000
2. **Bundesrat Plenarprotokolle**  
   - Format: PDF  
   - URL: `bundesrat.de/DE/service/protokolle/protokolle-node.html`  
   - Est. sentences: ~30,000
3. **Bundesgesetzblatt / federal legal texts**  
   - Format: XML bulk  
   - URLs: `gesetze-im-internet.de`, `github.com/bundestag/gesetze`  
   - Est. sentences: ~30,000

#### Länder
1. Bayern, NRW, Baden-Württemberg, Niedersachsen, Hessen (all PDF-based)  
   - Combined est. sentences: ~125,000

### P2 (second wave)

- **Europarl DE corpus** (XML, `statmt.org/europarl`) ~20,000
- Sachsen, Berlin, Brandenburg, Hamburg, Thüringen, Sachsen-Anhalt (PDF) ~97,000

### P3 (third wave)

- Schleswig-Holstein, Rheinland-Pfalz, Mecklenburg-Vorpommern, Saarland, Bremen (PDF) ~48,000

## Detailed Implementation Plan

### Phase 1 — Repository Structure and Config

Create a modular pipeline layout:

- `configs/sources/*.yaml`: one config per source (URL pattern, format, pagination, parser rules)
- `crawler/`: source fetchers (api/xml/pdf/html indexers)
- `parser/`: XML/PDF parsing and extraction logic
- `cleaning/`: normalization + noise filters
- `quality/`: validation rules and quality reports
- `dataset/`: final export format builders
- `orchestration/`: run plans (`p1`, `p2`, `p3`, full)

Standardize metadata schema across all sources:

- `source_type` (bundestag, bundesrat, landtag_*)
- `document_id`, `session_id`, `date`, `speaker`, `party_or_role`, `state`
- `text_raw`, `text_clean`, `language`, `license`, `url`, `retrieved_at`
- `quality_flags` (boilerplate, OCR_low_confidence, duplicate, truncated, etc.)

### Phase 2 — Source Connectors (Ingestion)

#### XML/API connectors (Bundestag, Gesetze, Europarl)
- Use official endpoints or mirrored bulk XML dumps.
- Parse with strict XML schema validation (reject malformed records).
- Incremental crawling: only fetch new/changed documents by date/version markers.

#### PDF connectors (Bundesrat + all Länder)
- Crawl index pages for plenar protocol links and metadata.
- Download with checksum + content-type validation.
- Use dual extraction strategy:
  1. Text-native PDF extraction
  2. OCR fallback only when PDF has no extractable text
- Track extraction method per page/document for downstream quality controls.

### Phase 3 — Parsing and Canonical Text Extraction

Implement format-specific parsers:

- **Debate transcripts**:
  - Detect speaker boundaries reliably (regex + layout cues + optional NER rules)
  - Strip agenda headers, attendance lists, page numbers, and footers
  - Keep speech blocks in chronological order
- **Legal XML**:
  - Preserve paragraph/article hierarchy
  - Remove navigation/meta boilerplate
  - Keep only legally substantive content blocks

All outputs must preserve **raw + cleaned text** for auditability.

### Phase 4 — Noise Elimination and Data Cleaning

Apply layered cleaning:

1. **Structural noise removal**:
   - headers/footers, page counters, TOCs, repeated templates
2. **Text normalization**:
   - Unicode normalization, de-hyphenation across line breaks, whitespace cleanup
3. **Duplicate removal**:
   - exact hash deduplication + near-duplicate similarity thresholding
4. **Language filtering**:
   - keep German (`de`) as primary output, flag multilingual fragments
5. **Sentence segmentation**:
   - German-aware segmentation with abbreviation safeguards (`z. B.`, `Art.` etc.)
6. **Quality filters**:
   - drop ultra-short fragments, OCR gibberish, low-alphabetic-ratio strings

### Phase 5 — Dataset Refinement for Model Training

Create train-ready outputs:

- Sentence-level and document-level datasets
- Recommended splits:
  - train 80%
  - validation 10%
  - test 10%
- Stratify by source + year + institution to reduce distribution bias
- Remove leakage:
  - deduplicate across splits
  - prevent same speech/document family from appearing in multiple splits

Output formats:

- `parquet` (primary)
- `jsonl` (interoperable)

### Phase 6 — Quality Assurance and Acceptance Criteria

Automated validation checks per run:

- schema completeness (`source`, `date`, `text_clean` non-null)
- sentence count progression vs expected source envelope
- duplicate rate under threshold
- OCR fallback ratio monitored (unexpected spikes trigger warnings)
- random sampling report per source for manual review

Acceptance criteria:

- >= 95% records pass mandatory schema checks
- < 2% near-duplicate rate in final corpus
- sentence count within expected ±15% per source (unless justified)
- documented provenance for every record (URL + retrieval timestamp)

### Phase 7 — Orchestration, Monitoring, and Reproducibility

- Scheduled crawls for refreshable sources
- Idempotent runs keyed by source/document identifiers
- Version each dataset release (`vYYYY.MM.DD`)
- Store pipeline logs, parser stats, and rejection reasons for traceability

## Suggested Delivery Milestones

1. **Milestone A (P1 federal + 5 major Länder)**: end-to-end ingestion to clean sentence export
2. **Milestone B (P2 sources)**: expanded coverage + improved OCR/quality tuning
3. **Milestone C (P3 sources + hardening)**: full 16-state coverage + release checklist

## Clarifying Questions

1. Should legal texts (Bundesgesetzblatt) remain paragraph-level only, or also sentence-split like speeches?
2. Are there strict licensing constraints for downstream model redistribution that require per-record license filtering?
3. Do you prefer one unified corpus, or separate domain corpora (debates vs legal text) with independent train/val/test splits?
4. What is the preferred OCR engine and language model for low-quality scanned PDFs?
