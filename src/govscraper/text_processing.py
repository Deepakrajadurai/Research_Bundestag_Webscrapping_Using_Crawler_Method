from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

import spacy
from datasketch import MinHash, MinHashLSH
from rapidfuzz import fuzz

_WHITESPACE_RE = re.compile(r"\s+")
_BOILERPLATE_RE = re.compile(r"(seite\s+\d+|drucksache\s+\d+/\d+)", re.IGNORECASE)
MIN_SENTENCE_LENGTH = 20
SHINGLE_SIZE = 3
MAX_FUZZY_COMPARISONS = 200
LEGAL_SOURCE_TYPES = {
    "bundesgesetzblatt",
    "gesetze",
    "federal_law",
}
_SENTENCER = None


def _get_sentencer():
    global _SENTENCER
    if _SENTENCER is None:
        nlp = spacy.blank("de")
        nlp.add_pipe("sentencizer")
        _SENTENCER = nlp
    return _SENTENCER


def extract_text_candidates(record: dict[str, Any], preferred_keys: tuple[str, ...] = ("text", "rede", "inhalt", "content")) -> list[str]:
    found: list[str] = []

    for key in preferred_keys:
        value = record.get(key)
        if isinstance(value, str):
            found.append(value)

    def _walk(node: Any) -> None:
        if isinstance(node, str):
            found.append(node)
            return
        if isinstance(node, list):
            for item in node:
                _walk(item)
            return
        if isinstance(node, dict):
            for value in node.values():
                _walk(value)

    _walk(record)
    return [item for item in found if item.strip()]


def clean_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u00ad", "")
    normalized = _BOILERPLATE_RE.sub(" ", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def split_sentences(text: str) -> list[str]:
    doc = _get_sentencer()(text)
    return [sentence.text.strip() for sentence in doc.sents if sentence.text.strip()]


def _classify_domain(source_type: str) -> str:
    normalized = source_type.lower()
    if normalized in LEGAL_SOURCE_TYPES:
        return "legal"
    if any(hint in normalized for hint in ("gesetz", "law")):
        return "legal"
    return "debate"


def label_sentence(*, sentence: str, source_type: str) -> dict[str, str]:
    domain = _classify_domain(source_type)
    quality = "short" if len(sentence) < MIN_SENTENCE_LENGTH else "ok"
    return {"domain": domain, "source_type": source_type, "quality_label": quality}


def _exact_deduplicate(sentences: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for sentence in sentences:
        key = hashlib.sha256(sentence.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        output.append(sentence)
    return output


def _is_fuzzy_duplicate(candidate: str, kept: list[str], threshold: float) -> bool:
    for existing in kept[-MAX_FUZZY_COMPARISONS:]:
        if fuzz.ratio(candidate, existing) >= threshold:
            return True
    return False


def _minhash_signature(text: str, *, num_perm: int = 128) -> MinHash:
    signature = MinHash(num_perm=num_perm)
    chars = text.lower()
    max_start = max(len(chars) - SHINGLE_SIZE + 1, 0)
    shingles = {chars[i : i + SHINGLE_SIZE] for i in range(max_start)}
    if not shingles and chars:
        shingles = {chars}
    for shingle in shingles:
        signature.update(shingle.encode("utf-8"))
    return signature


def deduplicate_sentences(
    sentences: list[str],
    *,
    fuzzy_threshold: float = 95.0,
    minhash_threshold: float = 0.90,
    num_perm: int = 128,
) -> list[str]:
    exact_unique = _exact_deduplicate([clean_text(item) for item in sentences if clean_text(item)])
    lsh = MinHashLSH(threshold=minhash_threshold, num_perm=num_perm)
    kept: list[str] = []

    for index, sentence in enumerate(exact_unique):
        if _is_fuzzy_duplicate(sentence, kept, fuzzy_threshold):
            continue
        signature = _minhash_signature(sentence, num_perm=num_perm)
        if lsh.query(signature):
            continue
        lsh.insert(f"s{index}", signature)
        kept.append(sentence)
    return kept
