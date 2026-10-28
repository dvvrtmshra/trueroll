"""S24 — Evaluation summary: run evaluate script, check output file and endpoint."""
import json
import os
import pytest


def test_s24_evaluate_script_runs(db):
    """Running the evaluate module writes evaluation_summary.json."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from scripts.evaluate import run
    summary = run()

    assert isinstance(summary, dict)
    assert "generated_at" in summary
    assert "breaches" in summary
    assert "matching" in summary
    assert "reconciliation" in summary


def test_s24_summary_file_exists(db, tmp_path, monkeypatch):
    """evaluate.run() creates models/evaluation_summary.json."""
    # Run the evaluate script
    from scripts.evaluate import run
    run()

    summary_path = os.path.join(
        os.path.dirname(__file__), "..", "models", "evaluation_summary.json"
    )
    assert os.path.exists(summary_path), f"evaluation_summary.json not found at {summary_path}"

    with open(summary_path) as f:
        data = json.load(f)

    assert "matching" in data
    assert "precision" in data["matching"]
    assert "recall" in data["matching"]
    assert "reconciliation" in data
    assert "clean" in data["reconciliation"]


def test_s24_evaluation_endpoint(db):
    """GET /reports/evaluation-summary returns data (or not_run if file missing)."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post("/auth/verify-otp", json={"email": "officer.national@trueroll.demo", "otp": "123456"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]

    resp = client.get("/reports/evaluation-summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # Either has full data or not_run status
    assert "status" in data or "matching" in data
