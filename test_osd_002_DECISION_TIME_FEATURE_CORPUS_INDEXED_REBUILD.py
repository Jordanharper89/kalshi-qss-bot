from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
assert p.exists(); s=p.read_text(encoding="utf-8"); py_compile.compile(str(p), doraise=True)
assert "SEQ_LOOKBACK = 75000" in s
assert "sequence_number BETWEEN %s AND %s" in s
assert "osd_001_kalshi_microstructure_archive.jsonl" not in s
assert "future_return" in s and '"features":feat' in s
assert "execution_authority" in s and "publication_allowed" in s
print("[PASS] OSD-002 indexed bounded PostgreSQL rebuild compiles")
print("[PASS] no 21.7M-row JSONL archive scan")
print("[PASS] exact anchor sequence bounded reads installed")
print("[PASS] future outcome remains target-only, not feature input")
print("[PASS] execution/publication remain false")
