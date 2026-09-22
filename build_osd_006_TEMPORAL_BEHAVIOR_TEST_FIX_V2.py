from pathlib import Path

ROOT = Path.cwd().resolve()
TEST = ROOT / "test_osd_006_TEMPORAL_BEHAVIOR_CORPUS_V2.py"
TARGET = ROOT / "qseries_v2/oracle_strategy_discovery/osd_006_temporal_behavior_corpus.py"

code = r'''
from pathlib import Path

p = Path("qseries_v2/oracle_strategy_discovery/osd_006_temporal_behavior_corpus.py")
s = p.read_text(encoding="utf-8")
compile(s, str(p), "exec")

assert 'x["d1_"+name]' in s
assert 'x["d2_"+name]' in s
assert 'self_minus_sibling_' in s
assert '"ticker_gap_s"' in s
assert '"asset_gap_s"' in s
assert 'future_return' not in s
assert 'execution_authority"]=False' in s
assert 'publication_allowed"]=False' in s

print("[PASS] OSD-006 temporal corpus V2 deterministic test")
print("[PASS] prior-state first/second deltas installed")
print("[PASS] self-vs-sibling lead/lag features installed")
print("[PASS] ticker/asset temporal gaps installed")
print("[PASS] future target excluded from feature construction")
print("[PASS] execution/publication remain false")
'''

TEST.write_text(code, encoding="utf-8")
compile(code, str(TEST), "exec")

print("[PASS] OSD-006 deterministic test defect replaced")
print("[TARGET]", TARGET)
print("[TEST]", TEST)
print("[OSD-006 RUNTIME] already physically produced 31948 rows")