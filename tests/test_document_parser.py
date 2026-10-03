import pytest
from app.services.document_parser import DocumentParser, DocumentParsingError


def test_clean_text():
    dirty = "  Hello \u00a0 world! \n\n\n\n  Line 2 \x00\x08 "
    cleaned = DocumentParser.clean_text(dirty)
    assert "Hello   world!" in cleaned or "Hello world!" in cleaned
    assert "\x00" not in cleaned
    assert "\n\n\n" not in cleaned


def test_unsupported_file_format():
    with pytest.raises(DocumentParsingError) as exc_info:
        DocumentParser.extract_from_file("resume.exe", b"binary content")
    assert "Unsupported file format" in str(exc_info.value)


def test_empty_text_file():
    with pytest.raises(DocumentParsingError):
        DocumentParser.extract_from_file("resume.txt", b"   ")


def test_valid_text_file():
    content = b"Candidate: Alex\nSkills: Python, SQL, Docker"
    extracted = DocumentParser.extract_from_file("resume.txt", content)
    assert "Candidate: Alex" in extracted
    assert "Python" in extracted
