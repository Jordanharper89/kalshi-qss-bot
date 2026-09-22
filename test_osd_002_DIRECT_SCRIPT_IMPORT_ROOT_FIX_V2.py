from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
s=p.read_text(encoding="utf-8")
py_compile.compile(str(p), doraise=True)
assert "REPO_ROOT = Path(__file__).resolve().parents[2]" in s
assert "sys.path.insert(0, str(REPO_ROOT))" in s
assert "from qseries_v2.oracle_production_hardening" in s
print("[PASS] OSD-002 direct-script import root fix V2 installed")
print("[PASS] qseries_v2 repo root injected before package import")
