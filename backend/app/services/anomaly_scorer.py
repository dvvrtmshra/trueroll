"""Anomaly scoring service (spec 6.6).

Score = round(100 * (0.5*s_if + 0.5*s_rz))
Band: <40 Low, 40-69 Medium, >=70 High
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.models.review_priority import ReviewPriority
from app.services.anomaly_features import extract_all_features

FEATURE_COLS = [
    "late_share_14d", "surge_ratio",
    "mix_ocifn", "mix_nri", "mix_ciwgc", "mix_ews",
    "fill_streak", "withdraw_rate", "post_audit_withdrawals",
    "max_cluster", "dob_concentration",
]

REASON_MAP = {
    "late_share_14d": "LATE_SURGE",
    "surge_ratio": "LATE_SURGE",
    "mix_ocifn": "CATEGORY_MIX",
    "mix_nri": "CATEGORY_MIX",
    "mix_ciwgc": "CATEGORY_MIX",
    "mix_ews": "CATEGORY_MIX",
    "fill_streak": "FULL_STREAK",
    "withdraw_rate": "POST_AUDIT_WITHDRAWALS",
    "post_audit_withdrawals": "POST_AUDIT_WITHDRAWALS",
    "max_cluster": "SHARED_ATTRIBUTE_CLUSTER",
    "dob_concentration": "CATEGORY_MIX",
}

REASON_DETAIL_TEMPLATES = {
    "LATE_SURGE": "Admissions in the last 14 days are {z:.1f} MAD above peer median",
    "CATEGORY_MIX": "Category mix is {z:.1f}x the peer median standard deviation",
    "FULL_STREAK": "Every bucket exactly full for {z:.0f} consecutive period(s)",
    "POST_AUDIT_WITHDRAWALS": "{z:.0f} withdrawals recorded after the audit date",
    "SHARED_ATTRIBUTE_CLUSTER": "Group of {z:.0f} students share a contact attribute",
}


def _intake_band(intake: int) -> str:
    if intake <= 100: return "0-100"
    if intake <= 200: return "101-200"
    if intake <= 300: return "201-300"
    if intake <= 600: return "301-600"
    return "601+"


def _peer_group(row: dict, all_rows: list[dict]) -> list[dict]:
    peers = [
        r for r in all_rows
        if r["state"] == row["state"]
        and r["level"] == row["level"]
        and _intake_band(r["approved_intake"]) == _intake_band(row["approved_intake"])
        and r["course_id"] != row["course_id"]
    ]
    if len(peers) < 8:
        peers = [
            r for r in all_rows
            if r["region"] == row["region"]
            and r["level"] == row["level"]
            and r["course_id"] != row["course_id"]
        ]
    return peers


def _robust_zscore(value: float, peers: list[float]) -> float:
    if not peers:
        return 0.0
    arr = np.array(peers, dtype=float)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    if mad == 0:
        return 0.0
    return (value - med) / (1.4826 * mad)


def score_one(row: dict, all_rows: list[dict]) -> dict:
    peers = _peer_group(row, all_rows)
    peer_desc = (
        f"Same state, {row['level']}, intake {_intake_band(row['approved_intake'])} (n={len(peers)})"
        if len(peers) >= 8
        else f"Same region, {row['level']} (n={len(peers)})"
    )

    z_scores: dict[str, float] = {}
    for col in FEATURE_COLS:
        val = float(row.get(col, 0))
        peer_vals = [float(p.get(col, 0)) for p in peers]
        z_scores[col] = _robust_zscore(val, peer_vals)

    max_z = max(abs(z) for z in z_scores.values()) if z_scores else 0.0
    s_rz = min(1.0, max_z / 6.0)

    # Isolation forest only when we have enough peers
    s_if = s_rz  # default: use z-score as proxy
    if len(peers) >= 5:
        try:
            from sklearn.ensemble import IsolationForest
            feature_matrix = np.array([[float(p.get(c, 0)) for c in FEATURE_COLS] for p in peers + [row]])
            iso = IsolationForest(n_estimators=200, contamination=0.08, random_state=26263)
            iso.fit(feature_matrix[:-1])
            scores = iso.score_samples(feature_matrix)
            subject_score = scores[-1]
            peer_scores = scores[:-1]
            # Percentile rank of subject within peers (inverted: lower IF score = more anomalous)
            rank = float(np.mean(peer_scores > subject_score))
            s_if = rank
        except Exception:
            pass

    final_score = round(100 * (0.5 * s_if + 0.5 * s_rz))
    band = "High" if final_score >= 70 else ("Medium" if final_score >= 40 else "Low")

    # Top 3 reasons by |z|
    sorted_cols = sorted(FEATURE_COLS, key=lambda c: abs(z_scores.get(c, 0)), reverse=True)
    seen_codes: set[str] = set()
    reasons = []
    for col in sorted_cols:
        z = z_scores.get(col, 0.0)
        if abs(z) < 1.0:
            break
        code = REASON_MAP.get(col, "CATEGORY_MIX")
        if code in seen_codes:
            continue
        seen_codes.add(code)
        template = REASON_DETAIL_TEMPLATES.get(code, "{z:.1f}")
        detail = template.format(z=abs(z))
        reasons.append({"code": code, "detail": detail})
        if len(reasons) >= 3:
            break

    return {
        "score": final_score,
        "band": band,
        "reasons": reasons,
        "peer_group": peer_desc,
        "z_scores": z_scores,
    }


def score_all(db: Session, academic_year: str = "2026-27") -> list[dict]:
    all_features = extract_all_features(db, academic_year)
    results = []
    for row in all_features:
        scored = score_one(row, all_features)
        # Upsert ReviewPriority
        existing = db.query(ReviewPriority).filter(
            ReviewPriority.institution_id == row["institution_id"],
            ReviewPriority.course_id == row["course_id"],
            ReviewPriority.period == academic_year,
        ).first()

        if existing:
            existing.score = scored["score"]
            existing.band = scored["band"]
            existing.reasons = json.dumps(scored["reasons"])
            existing.peer_group = scored["peer_group"]
            existing.features_json = json.dumps({k: row[k] for k in FEATURE_COLS if k in row})
        else:
            rp = ReviewPriority(
                institution_id=row["institution_id"],
                course_id=row["course_id"],
                period=academic_year,
                score=scored["score"],
                band=scored["band"],
                reasons=json.dumps(scored["reasons"]),
                peer_group=scored["peer_group"],
                model_version="robust_baseline + isolation_forest v0.1",
                status="advisory",
                features_json=json.dumps({k: row[k] for k in FEATURE_COLS if k in row}),
            )
            db.add(rp)

        results.append({
            "institution_id": row["institution_id"],
            "course_id": row["course_id"],
            "score": scored["score"],
            "band": scored["band"],
        })

    db.commit()
    return results
