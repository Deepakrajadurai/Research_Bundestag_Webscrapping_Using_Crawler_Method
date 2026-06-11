from govscraper.text_processing import clean_text, deduplicate_sentences, label_sentence, split_sentences


def test_clean_text_normalizes_whitespace_and_boilerplate():
    text = "Seite 12   Das   ist  ein  Test.\n\nDrucksache 20/123"
    assert clean_text(text) == "Das ist ein Test."


def test_split_sentences_uses_spacy_sentencizer():
    text = "Das ist ein Satz. Das ist noch einer!"
    assert split_sentences(text) == ["Das ist ein Satz.", "Das ist noch einer!"]


def test_label_sentence_assigns_legal_domain():
    labels = label_sentence(sentence="Dies ist ein Gesetzestext.", source_type="bundesgesetzblatt")
    assert labels["domain"] == "legal"
    assert labels["quality_label"] == "ok"


def test_deduplicate_sentences_removes_exact_and_fuzzy_duplicates():
    sentences = [
        "Die Sitzung ist eröffnet.",
        "Die Sitzung ist eröffnet.",
        "Die Sitzung ist eroeffnet.",
        "Ein komplett anderer Satz.",
    ]
    deduplicated = deduplicate_sentences(sentences, fuzzy_threshold=90)
    assert "Die Sitzung ist eröffnet." in deduplicated
    assert "Ein komplett anderer Satz." in deduplicated
    assert len(deduplicated) == 2

