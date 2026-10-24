"""Matching evaluation service — measures the fuzzy matcher on M16 pairs."""
from sqlalchemy.orm import Session

from app.models.matching_pair import MatchingPair
from app.services.fuzzy_matcher import score as fuzzy_score, duplicate_class


def run_evaluation(db: Session) -> dict:
    pairs = db.query(MatchingPair).all()
    if not pairs:
        return {
            "status": "not_measured",
            "message": "M16 data not loaded. Run make seed first.",
        }

    tp = fp = tn = fn = 0
    sent_to_review = 0
    total_true = sum(1 for p in pairs if p.is_true_duplicate)

    for pair in pairs:
        s = fuzzy_score(pair.name_a, pair.dob_a, pair.name_b, pair.dob_b, same_course=False)
        dc = duplicate_class(s)
        is_match = dc is not None
        is_true = pair.is_true_duplicate

        if is_true and is_match:
            tp += 1
        elif not is_true and is_match:
            fp += 1
        elif is_true and not is_match:
            fn += 1
        else:
            tn += 1

        if dc == "D4":
            sent_to_review += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    review_share = sent_to_review / total_true if total_true > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "sent_to_review": sent_to_review,
        "review_share": round(review_share, 4),
        "total_pairs": len(pairs),
        "total_true": total_true,
        "honesty_note": "Measured on synthetic typo-injected data only. Real accuracy requires a pilot.",
        "simulated": True,
    }
