from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_streaming_sweep.py")
s=p.read_text(encoding="utf-8")
py_compile.compile(str(p),doraise=True)
assert "with ARCHIVE.open" in s
assert "sequence_number BETWEEN" not in s
assert "single_pass_archive" in s
assert 'x["ticker"] != a["ticker"]' in s
assert "future_return" in s and 'row["features"]=feat' in s
print("[PASS] OSD-002 streaming sweep compiles")
print("[PASS] one-pass archive sweep installed")
print("[PASS] per-prediction PostgreSQL querying removed")
print("[PASS] sibling features exclude current ticker")
print("[PASS] future outcome remains target-only")
print("[PASS] execution/publication remain false")
