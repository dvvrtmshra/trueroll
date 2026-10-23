"""Ensure forbidden strings are not present anywhere in API response bodies."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

FORBIDDEN = ["violation", "fraud", "guilty"]


def _get_all_text(response) -> str:
    try:
        return str(response.json())
    except Exception:
        return response.text


@pytest.mark.parametrize("word", FORBIDDEN)
def test_forbidden_word_not_in_health(word):
    with TestClient(app) as c:
        r = c.get("/health")
        assert word not in _get_all_text(r).lower()


@pytest.mark.parametrize("word", FORBIDDEN)
def test_forbidden_word_not_in_501_stubs(word):
    with TestClient(app) as c:
        for path in ["/institutions", "/students", "/rules", "/flags"]:
            r = c.get(path)
            assert word not in _get_all_text(r).lower(), f"Found '{word}' in {path}"
