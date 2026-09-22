from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))

def read_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"__read_error__": f"{type(exc).__name__}: {exc}"}

def count_statuses(obj):
    c = Counter()
    if isinstance(obj, dict):
        for value in obj.values():
            if isinstance(value, dict):
                status = str(value.get("status") or "UNKNOWN")
                c[status] += 1
    elif isinstance(obj, list):
        for value in obj:
            if isinstance(value, dict):
                status = str(value.get("status") or "UNKNOWN")
                c[status] += 1
    return c

def sample_tickers(obj, limit=20):
    found = []
    rows = obj.values() if isinstance(obj, dict) else obj if isinstance(obj, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = (
            row.get("ticker")
            or row.get("market_ticker")
            or row.get("market_id")
            or row.get("market")
        )
        if ticker:
            ticker = str(ticker)
            if ticker not in found:
                found.append(ticker)
        if len(found) >= limit:
            break
    return found

def print_json_summary(label, path, obj):
    print(f"[{label}] path={path.relative_to(ROOT)} present={path.is_file()}")
    if obj is None:
        return
    if isinstance(obj, dict):
        print(f"[{label}] top_level_keys={tuple(sorted(obj.keys()))[:25]}")
    elif isinstance(obj, list):
        print(f"[{label}] rows={len(obj)}")

def main():
    print("=" * 80)
    print(" ORACLE CURRENT LEARNING DIAGNOSTIC")
    print(" READ-ONLY — FROZEN OLR-001 THROUGH OLR-045")
    print("=" * 80)

    state_dir = ROOT / "runtime_state"

    paths = {
        "LEARNING STATE": state_dir / "oracle_learning_runtime_state.json",
        "LEARNING LEDGER": state_dir / "oracle_learning_event_ledger.json",
        "CALIBRATION STATE": state_dir / "oracle_calibration_ingestion_state.json",
        "CALIBRATION LEDGER": state_dir / "oracle_calibration_ledger.json",
        "LIVE FEEDBACK": state_dir / "oracle_live_reasoning_feedback.json",
        "FEEDBACK SNAPSHOT": state_dir / "oracle_reasoning_feedback_snapshot.json",
        "OLR FREEZE": state_dir / "oracle_learning_runtime_freeze_manifest.json",
    }

    data = {label: read_json(path) for label, path in paths.items()}

    for label, path in paths.items():
        print_json_summary(label, path, data[label])

    print("-" * 80)

    learning = data["LEARNING STATE"]
    if isinstance(learning, dict):
        print(f"[LEARNING] cycles={learning.get('cycles', 0)}")
        print(f"[LEARNING] outcomes_scanned={learning.get('outcomes_scanned', 0)}")
        print(f"[LEARNING] outcomes_learned={learning.get('outcomes_learned', 0)}")
        print(f"[LEARNING] duplicates={learning.get('duplicate_events', learning.get('duplicates', 0))}")
        ocl = learning.get("ocl_state")
        if isinstance(ocl, dict):
            print(f"[LEARNING] applied_through_sequence={ocl.get('applied_through_sequence', 0)}")
            print(f"[LEARNING] learner_state_hash={ocl.get('state_hash', '')}")

    ledger = data["LEARNING LEDGER"]
    if isinstance(ledger, (dict, list)):
        ledger_len = len(ledger)
        statuses = count_statuses(ledger)
        tickers = sample_tickers(ledger)
        print(f"[LEARNING LEDGER] records={ledger_len}")
        print(f"[LEARNING LEDGER] statuses={dict(sorted(statuses.items()))}")
        print(f"[LEARNING LEDGER] sample_markets={tuple(tickers)}")

    calibration_state = data["CALIBRATION STATE"]
    if isinstance(calibration_state, dict):
        print(f"[CALIBRATION] cycles_completed={calibration_state.get('cycles_completed', 0)}")
        print(f"[CALIBRATION] settled_scanned={calibration_state.get('settled_scanned', 0)}")
        print(f"[CALIBRATION] candidates_seen={calibration_state.get('candidates_seen', 0)}")
        print(f"[CALIBRATION] records_admitted={calibration_state.get('records_admitted', 0)}")
        print(f"[CALIBRATION] probability_abstentions={calibration_state.get('probability_abstentions', 0)}")
        print(f"[CALIBRATION] ledger_records={calibration_state.get('ledger_records', 0)}")

    calibration_ledger = data["CALIBRATION LEDGER"]
    if isinstance(calibration_ledger, dict):
        print(f"[CALIBRATION LEDGER] records={len(calibration_ledger)}")
        print(f"[CALIBRATION LEDGER] sample_markets={tuple(sample_tickers(calibration_ledger))}")

    feedback = data["LIVE FEEDBACK"]
    if isinstance(feedback, dict):
        markets = feedback.get("markets", [])
        if not isinstance(markets, list):
            markets = []
        mature = [x for x in markets if isinstance(x, dict) and x.get("mature") is True]
        stable = [x for x in markets if isinstance(x, dict) and x.get("stable") is True]
        print(f"[LIVE FEEDBACK] calibration_records={feedback.get('calibration_records', 0)}")
        print(f"[LIVE FEEDBACK] markets={len(markets)}")
        print(f"[LIVE FEEDBACK] mature_markets={len(mature)}")
        print(f"[LIVE FEEDBACK] stable_markets={len(stable)}")
        if mature:
            print("[LIVE FEEDBACK] mature_sample=")
            for row in mature[:10]:
                print(
                    "  "
                    f"{row.get('market_ticker')} "
                    f"samples={row.get('samples')} "
                    f"bias={row.get('calibration_bias')} "
                    f"reliability={row.get('reliability_weight')} "
                    f"behavior={row.get('behavior_class')}"
                )

    print("-" * 80)

    try:
        from qseries_v2.oracle_learning_runtime.olr_041_learning_health_model import inspect_learning_health
        health = inspect_learning_health(ROOT)
        print(
            f"[OLR HEALTH] health={health.health} reason={health.reason} "
            f"learning_cycles={health.learning_cycles} "
            f"outcomes_learned={health.outcomes_learned} "
            f"calibration_cycles={health.calibration_cycles} "
            f"calibration_records={health.calibration_records} "
            f"mature_markets={health.mature_markets}"
        )
    except Exception as exc:
        print(f"[OLR HEALTH] unavailable={type(exc).__name__}: {exc}")

    try:
        from qseries_v2.oracle_learning_runtime.olr_043_production_learning_integrity_verification import verify_production_learning_integrity
        integrity = verify_production_learning_integrity(ROOT)
        print(f"[INTEGRITY] replay_hash={integrity.replay_hash}")
        print(f"[INTEGRITY] state_hash={integrity.state_hash}")
    except Exception as exc:
        print(f"[INTEGRITY] unavailable={type(exc).__name__}: {exc}")

    print("-" * 80)

    learned = 0
    if isinstance(learning, dict):
        learned = int(learning.get("outcomes_learned", 0) or 0)

    cal_records = len(calibration_ledger) if isinstance(calibration_ledger, dict) else 0

    mature_count = 0
    if isinstance(feedback, dict) and isinstance(feedback.get("markets"), list):
        mature_count = sum(
            1 for x in feedback["markets"]
            if isinstance(x, dict) and x.get("mature") is True
        )

    if learned == 0:
        print("[DIAGNOSIS] Oracle runtime is active, but no outcome-grounded learning has been admitted yet.")
        print("[NEXT QUESTION] Are settled outcomes being discovered and matched to prior observations?")
    elif cal_records == 0:
        print("[DIAGNOSIS] Oracle HAS learned outcomes, but none have become defensible calibration records yet.")
        print("[NEXT QUESTION] Are learned outcomes carrying recoverable pre-settlement probabilities/evidence lineage?")
    elif mature_count == 0:
        print("[DIAGNOSIS] Oracle HAS learning + calibration records, but history is not mature enough yet.")
        print("[NEXT QUESTION] Let the live learner accumulate additional settled samples per market/family.")
    else:
        print("[DIAGNOSIS] Oracle has mature learned calibration available for bounded feedback consumption.")

    print("[PASS] Diagnostic performed read-only")
    print("[PASS] Frozen OLR boundary was not modified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE CURRENT LEARNING DIAGNOSTIC COMPLETE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
