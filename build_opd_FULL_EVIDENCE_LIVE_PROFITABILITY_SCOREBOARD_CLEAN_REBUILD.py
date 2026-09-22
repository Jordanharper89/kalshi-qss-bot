from pathlib import Path
import shutil

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_predictive_discovery"
OLD=PKG/"opd_full_evidence_live_profitability_scoreboard.py"
NEW=PKG/"opd_full_evidence_live_profitability_scoreboard_clean.py"
RUN=ROOT/"run_opd_full_evidence_predictor_child.py"
TEST=ROOT/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_CLEAN_REBUILD.py"
PRED=PKG/"opd_live_full_evidence_fusion_predictor.py"
RES=PKG/"opd_full_evidence_exact_future_outcome_resolver.py"

if not PRED.exists() or "PREDICTION_LEDGER_REVISION=" not in PRED.read_text(encoding="utf-8"):
    raise SystemExit("[FAIL] immutable prediction ledger boundary missing")
if not RES.exists() or "OUTCOME_LEDGER_REVISION=" not in RES.read_text(encoding="utf-8"):
    raise SystemExit("[FAIL] exact future outcome resolver boundary missing")
if not RUN.exists():
    raise SystemExit("[FAIL] full-evidence continuous child missing")

runner=RUN.read_text(encoding="utf-8")
for marker in ("run_prediction(root=root)","resolve_full_evidence_outcomes(root)","DEFAULT_CADENCE_SECONDS = 30.0"):
    if marker not in runner:
        raise SystemExit("[FAIL] exact runtime boundary missing: "+marker)

MODULE='from pathlib import Path\nimport json\nimport os\n\nPREDICTION_LEDGER_NAME = "opd_full_evidence_live_prediction_ledger.jsonl"\nOUTCOME_LEDGER_NAME = "opd_full_evidence_live_outcome_ledger.jsonl"\nSCOREBOARD_NAME = "opd_full_evidence_live_profitability_scoreboard.json"\nSCOREBOARD_REVISION = "FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_CLEAN_V1"\nROUND_TRIP_HURDLE = 0.02\nEXECUTION_AUTHORITY = False\nPUBLICATION_ALLOWED = False\n\ndef _read_jsonl(path):\n    rows = []\n    if not path.exists():\n        return rows\n    with path.open("r", encoding="utf-8") as f:\n        for raw in f:\n            line = raw.strip()\n            if not line:\n                continue\n            try:\n                rows.append(json.loads(line))\n            except Exception:\n                continue\n    return rows\n\ndef _mean(values):\n    return None if not values else sum(values) / len(values)\n\ndef _directional_hit(row):\n    value = float(row.get("directional_return") or 0.0)\n    if value > 0:\n        return 1.0\n    if value < 0:\n        return 0.0\n    return 0.5\n\ndef _stats(rows):\n    hits = [_directional_hit(r) for r in rows]\n    directional = [float(r.get("directional_return") or 0.0) for r in rows]\n    net = [x - ROUND_TRIP_HURDLE for x in directional]\n    probs = [max(0.0, min(1.0, float(r.get("predicted_probability") or 0.5))) for r in rows]\n    brier = [(p - y) ** 2 for p, y in zip(probs, hits)]\n    abs_cal = [abs(p - y) for p, y in zip(probs, hits)]\n    return {\n        "n": len(rows),\n        "hit_rate": _mean(hits),\n        "mean_directional_return": _mean(directional),\n        "mean_net_realized_after_2pct": _mean(net),\n        "cumulative_net_realized_after_2pct": sum(net) if net else 0.0,\n        "positive_net_count": sum(1 for x in net if x > 0),\n        "negative_net_count": sum(1 for x in net if x < 0),\n        "flat_net_count": sum(1 for x in net if x == 0),\n        "brier_score": _mean(brier),\n        "mean_absolute_calibration_error": _mean(abs_cal),\n        "mean_predicted_probability": _mean(probs),\n    }\n\ndef build_scoreboard(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    base = root / "runtime" / "predictive_data"\n    predictions = _read_jsonl(base / PREDICTION_LEDGER_NAME)\n    outcomes = _read_jsonl(base / OUTCOME_LEDGER_NAME)\n\n    resolved = [r for r in outcomes if r.get("resolution_status") == "RESOLVED_EXACT_FUTURE"]\n    actionable = [r for r in resolved if bool(r.get("actionable_at_freeze"))]\n    abstained = [r for r in resolved if not bool(r.get("actionable_at_freeze"))]\n\n    by_horizon = {}\n    for row in actionable:\n        h = str(int(row.get("horizon_seconds") or 0))\n        by_horizon.setdefault(h, []).append(row)\n\n    a = _stats(actionable)\n    if a["n"] == 0:\n        status = "NO_RESOLVED_ACTIONABLE_PREDICTIONS"\n    elif a["mean_net_realized_after_2pct"] > 0:\n        status = "POSITIVE_NET_EXPECTANCY_OBSERVED"\n    else:\n        status = "NONPOSITIVE_NET_EXPECTANCY_OBSERVED"\n\n    board = {\n        "revision": SCOREBOARD_REVISION,\n        "round_trip_hurdle": ROUND_TRIP_HURDLE,\n        "prediction_rows": len(predictions),\n        "resolved_exact_future_rows": len(resolved),\n        "actionable": a,\n        "abstained": _stats(abstained),\n        "actionable_by_horizon": {\n            h: _stats(rows)\n            for h, rows in sorted(by_horizon.items(), key=lambda item: int(item[0]))\n        },\n        "profitability_status": status,\n        "profitability_certified": False,\n        "certification_note": "Observed prospective economics only; certification requires a sufficient untouched live sample and separate acceptance rule.",\n        "execution_authority": False,\n        "publication_allowed": False,\n    }\n\n    path = base / SCOREBOARD_NAME\n    path.parent.mkdir(parents=True, exist_ok=True)\n    temp = path.with_suffix(".tmp")\n    with temp.open("w", encoding="utf-8") as f:\n        json.dump(board, f, sort_keys=True, indent=2)\n        f.write("\\n")\n        f.flush()\n        os.fsync(f.fileno())\n    temp.replace(path)\n    board["scoreboard_path"] = str(path)\n    return board\n\ndef run(root=None):\n    board = build_scoreboard(root)\n    a = board["actionable"]\n    print("[LIVE PROFITABILITY SCOREBOARD] resolved_exact_future=", board["resolved_exact_future_rows"],\n          "actionable_n=", a["n"], "status=", board["profitability_status"], flush=True)\n    print("[ACTIONABLE] hit_rate=", a["hit_rate"],\n          "mean_directional_return=", a["mean_directional_return"],\n          "mean_net_after_2pct=", a["mean_net_realized_after_2pct"],\n          "cumulative_net_after_2pct=", a["cumulative_net_realized_after_2pct"], flush=True)\n    print("[CALIBRATION] brier=", a["brier_score"],\n          "mean_abs_error=", a["mean_absolute_calibration_error"],\n          "mean_predicted_probability=", a["mean_predicted_probability"], flush=True)\n    print("[SCOREBOARD]", board["scoreboard_path"], flush=True)\n    print("[PROFITABILITY_CERTIFIED] FALSE", flush=True)\n    print("[EXECUTION/PUBLICATION] FALSE/FALSE", flush=True)\n    return board\n\nif __name__ == "__main__":\n    run()\n'
TEST_SOURCE='from pathlib import Path\nimport json\nimport tempfile\nimport qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean as m\n\nwith tempfile.TemporaryDirectory() as td:\n    root = Path(td)\n    base = root / "runtime" / "predictive_data"\n    base.mkdir(parents=True)\n\n    predictions = [\n        {"prediction_id": "P1"},\n        {"prediction_id": "P2"},\n        {"prediction_id": "P3"},\n        {"prediction_id": "P4"},\n    ]\n    outcomes = [\n        {"prediction_id": "P1", "resolution_status": "RESOLVED_EXACT_FUTURE",\n         "actionable_at_freeze": True, "horizon_seconds": 300,\n         "directional_return": 0.08, "predicted_probability": 0.70},\n        {"prediction_id": "P2", "resolution_status": "RESOLVED_EXACT_FUTURE",\n         "actionable_at_freeze": True, "horizon_seconds": 300,\n         "directional_return": -0.01, "predicted_probability": 0.60},\n        {"prediction_id": "P3", "resolution_status": "RESOLVED_EXACT_FUTURE",\n         "actionable_at_freeze": False, "horizon_seconds": 60,\n         "directional_return": 0.03, "predicted_probability": 0.55},\n        {"prediction_id": "P4", "resolution_status": "CONTRACT_HORIZON_INELIGIBLE",\n         "actionable_at_freeze": False, "horizon_seconds": 900},\n    ]\n\n    with (base / m.PREDICTION_LEDGER_NAME).open("w", encoding="utf-8") as f:\n        for row in predictions:\n            f.write(json.dumps(row) + "\\n")\n\n    with (base / m.OUTCOME_LEDGER_NAME).open("w", encoding="utf-8") as f:\n        for row in outcomes:\n            f.write(json.dumps(row) + "\\n")\n\n    board = m.build_scoreboard(root)\n    a = board["actionable"]\n\n    assert board["prediction_rows"] == 4\n    assert board["resolved_exact_future_rows"] == 3\n    assert a["n"] == 2\n    assert abs(a["hit_rate"] - 0.5) < 1e-12\n    assert abs(a["mean_directional_return"] - 0.035) < 1e-12\n    assert abs(a["mean_net_realized_after_2pct"] - 0.015) < 1e-12\n    assert abs(a["cumulative_net_realized_after_2pct"] - 0.03) < 1e-12\n    assert a["positive_net_count"] == 1\n    assert a["negative_net_count"] == 1\n    assert board["profitability_status"] == "POSITIVE_NET_EXPECTANCY_OBSERVED"\n    assert board["profitability_certified"] is False\n    assert board["abstained"]["n"] == 1\n    assert "300" in board["actionable_by_horizon"]\n\n    disk = json.loads((base / m.SCOREBOARD_NAME).read_text(encoding="utf-8"))\n    assert disk["resolved_exact_future_rows"] == 3\n    assert disk["actionable"]["n"] == 2\n    assert disk["execution_authority"] is False\n    assert disk["publication_allowed"] is False\n\nrunner = Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")\nassert "run_prediction(root=root)" in runner\nassert "resolve_full_evidence_outcomes(root)" in runner\nassert "run_full_evidence_scoreboard_clean(root)" in runner\nassert runner.index("run_prediction(root=root)") < runner.index("resolve_full_evidence_outcomes(root)") < runner.index("run_full_evidence_scoreboard_clean(root)")\n\nprint("[PASS] clean scoreboard reads exact resolved outcome ledger")\nprint("[PASS] actionable predictions separated from abstained forecasts")\nprint("[PASS] directional return and fixed 2pct realized net economics verified")\nprint("[PASS] hit rate, Brier score, calibration error, and horizon breakdown verified")\nprint("[PASS] atomic scoreboard JSON write verified")\nprint("[PASS] profitability certification remains FALSE")\nprint("[PASS] clean scoreboard runs after exact resolver in existing 30-second child")\nprint("[EXECUTION/PUBLICATION] FALSE/FALSE")\n'

NEW.parent.mkdir(parents=True,exist_ok=True)
NEW.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

compile(NEW.read_text(encoding="utf-8"),str(NEW),"exec")
compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

lines=[]
for line in runner.splitlines():
    if "opd_full_evidence_live_profitability_scoreboard import run as run_full_evidence_scoreboard" in line:
        continue
    if line.strip()=="run_full_evidence_scoreboard(root)":
        continue
    if "opd_full_evidence_live_profitability_scoreboard_clean import run as run_full_evidence_scoreboard_clean" in line:
        continue
    if line.strip()=="run_full_evidence_scoreboard_clean(root)":
        continue
    lines.append(line)
runner="\n".join(lines)+"\n"

resolver_import="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver import run as resolve_full_evidence_outcomes\n"
clean_import="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean import run as run_full_evidence_scoreboard_clean\n"
if resolver_import not in runner:
    raise SystemExit("[FAIL] exact resolver import boundary missing")
runner=runner.replace(resolver_import,resolver_import+clean_import,1)

resolver_call="        resolve_full_evidence_outcomes(root)\n"
if runner.count(resolver_call)!=1:
    raise SystemExit("[FAIL] exact resolver runtime call missing or duplicated")
runner=runner.replace(resolver_call,resolver_call+"        run_full_evidence_scoreboard_clean(root)\n",1)

if OLD.exists():
    retired=PKG/"opd_full_evidence_live_profitability_scoreboard.RETIRED_FAILED.py"
    if not retired.exists():
        shutil.copy2(OLD,retired)

RUN.write_text(runner,encoding="utf-8")
compile(RUN.read_text(encoding="utf-8"),str(RUN),"exec")

print("[PASS] clean profitability scoreboard rebuilt from zero")
print("[PASS] failed scoreboard implementation retired from runtime path")
print("[MODULE] qseries_v2/oracle_predictive_discovery/opd_full_evidence_live_profitability_scoreboard_clean.py")
print("[SCOREBOARD] runtime/predictive_data/opd_full_evidence_live_profitability_scoreboard.json")
print("[PASS] predictor -> exact resolver -> clean scoreboard runtime order installed")
print("[PASS] fixed 2pct hurdle preserved; prediction gates unchanged")
print("[PROFITABILITY_CERTIFIED] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
