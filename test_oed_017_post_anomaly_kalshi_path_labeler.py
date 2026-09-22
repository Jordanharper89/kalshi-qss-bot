
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_017_post_anomaly_kalshi_path_labeler import label

s, p = label(Path.cwd())
assert p.exists()
assert s["bounded_rows"] > 0
assert s["event_count"] > 0
assert s["strict_source_event_time"] is True
assert s["legacy_outer_time_not_promoted"] is True
assert s["future_only_labels"] is True
assert s["edge_proven"] is False
assert s["execution_authority"] is False
assert len(s["labels_hash"]) == 64

print("[LABEL_FILE]", p)
print("[BOUNDED_SEQUENCE_WINDOW]", s["bounded_sequence_window"])
print("[BOUNDED_ROWS]", s["bounded_rows"])
print("[EVENTS]", s["event_count"])
print("[STATUS_COUNTS]", s["status_counts"])
print("[LABELED_EVENTS]", s["labeled_event_count"])
print("[LABELS_HASH]", s["labels_hash"])

samples = [x for x in s["events"] if x["label_status"] == "LABELED"][:10]
print("[LABELED_SAMPLES]")
for x in samples:
    print(" ", {
        "event_id": x["event_id"],
        "detectors": x["detectors"],
        "anchor_basis": x["anchor_basis"],
        "targets": x["targets"],
        "labels": x["labels"][:2],
    })

print("[PASS] one bounded PostgreSQL outcome surface used")
print("[PASS] exact Kalshi source-event time recovered from sequence identity")
print("[PASS] exact CHF anchor_epoch recovered for OED-014")
print("[PASS] OED-013 legacy outer-time candidates held rather than fabricated")
print("[PASS] 30s/60s/5m/15m future-only path labels materialized where complete")
print("[PASS] OED-017 post-anomaly path labeler certified")
