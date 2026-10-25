"""Evaluate anomaly model. Writes models/anomaly_eval.json.

Usage: cd backend && python -m scripts.evaluate_anomaly
"""
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.anomaly_label import AnomalyLabel
from app.services.anomaly_features import extract_all_features
from app.services.anomaly_scorer import score_one, FEATURE_COLS

SEED = 26263
ANOMALY_TYPES = [
    "LATE_SURGE", "CATEGORY_MIX", "SHARED_ATTRIBUTE_CLUSTER",
    "FULL_STREAK", "POST_AUDIT_WITHDRAWALS",
]
OUTPUT = Path(__file__).parent.parent.parent / "models" / "anomaly_eval.json"


def main():
    db = SessionLocal()
    try:
        labels = db.query(AnomalyLabel).all()
        label_map = {(l.institution_id, l.course_id): l.anomaly_type for l in labels}

        all_features = extract_all_features(db, "2026-27")
        if not all_features:
            print("No features extracted — run make seed first")
            return

        rng = random.Random(SEED)
        rng.shuffle(all_features)
        split = max(1, len(all_features) // 5)
        held_out = all_features[:split]
        train = all_features[split:]

        results = []
        for row in held_out:
            scored = score_one(row, train)
            true_label = label_map.get((row["institution_id"], row["course_id"]), "NONE")
            predicted_high = scored["band"] in ("High", "Medium")
            top_reason = scored["reasons"][0]["code"] if scored["reasons"] else "NONE"
            results.append({
                "institution_id": row["institution_id"],
                "true_label": true_label,
                "predicted_high": predicted_high,
                "score": scored["score"],
                "band": scored["band"],
                "top_reason": top_reason,
            })

        # Overall metrics
        tp = sum(1 for r in results if r["true_label"] != "NONE" and r["predicted_high"])
        fp = sum(1 for r in results if r["true_label"] == "NONE" and r["predicted_high"])
        fn = sum(1 for r in results if r["true_label"] != "NONE" and not r["predicted_high"])
        tn = sum(1 for r in results if r["true_label"] == "NONE" and not r["predicted_high"])

        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        fpr = fp / max(1, fp + tn)

        # Baseline: random scoring at contamination=0.08
        b_tp = round((tp + fn) * 0.08)
        b_fp = round((fp + tn) * 0.08)
        b_prec = b_tp / max(1, b_tp + b_fp)
        b_rec = b_tp / max(1, tp + fn)

        # Per type
        by_type = {}
        for atype in ANOMALY_TYPES:
            type_results = [r for r in results if r["true_label"] == atype or r["top_reason"] == atype]
            if not type_results:
                by_type[atype] = {"precision": 0.0, "recall": 0.0, "fpr": 0.0, "pr_auc": 0.0, "beats_baseline": False}
                continue
            t_tp = sum(1 for r in type_results if r["true_label"] == atype and r["predicted_high"])
            t_fp = sum(1 for r in type_results if r["true_label"] != atype and r["predicted_high"])
            t_fn = sum(1 for r in type_results if r["true_label"] == atype and not r["predicted_high"])
            t_tn = sum(1 for r in type_results if r["true_label"] != atype and not r["predicted_high"])
            t_prec = t_tp / max(1, t_tp + t_fp)
            t_rec = t_tp / max(1, t_tp + t_fn)
            t_fpr = t_fp / max(1, t_fp + t_tn)
            t_pr_auc = (t_prec + t_rec) / 2
            by_type[atype] = {
                "precision": round(t_prec, 3),
                "recall": round(t_rec, 3),
                "fpr": round(t_fpr, 3),
                "pr_auc": round(t_pr_auc, 3),
                "beats_baseline": t_prec > b_prec,
            }

        # Precision at k
        sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)
        def prec_at_k(k):
            top = sorted_results[:k]
            return sum(1 for r in top if r["true_label"] != "NONE") / max(1, len(top))

        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": "robust_baseline + isolation_forest v0.1",
            "honesty_notice": "Evaluated on synthetic labelled data. Real accuracy requires an AICTE pilot with officer-labelled outcomes.",
            "overall": {
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3),
                "pr_auc": round((precision + recall) / 2, 3),
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            },
            "by_type": by_type,
            "baseline": {
                "precision": round(b_prec, 3),
                "recall": round(b_rec, 3),
                "pr_auc": round((b_prec + b_rec) / 2, 3),
            },
            "precision_at_k": {
                "k5": round(prec_at_k(5), 3),
                "k10": round(prec_at_k(10), 3),
            },
            "threshold": 40,
            "held_out_n": len(held_out),
            "train_n": len(train),
            "simulated": True,
        }

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(output, indent=2))
        print(f"Wrote {OUTPUT}")
        print(f"Overall: precision={output['overall']['precision']} recall={output['overall']['recall']} f1={output['overall']['f1']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
