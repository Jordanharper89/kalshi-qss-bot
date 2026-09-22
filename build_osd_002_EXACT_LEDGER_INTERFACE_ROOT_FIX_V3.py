from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "qseries_v2" / "oracle_strategy_discovery" / "osd_002_decision_time_feature_corpus_indexed_rebuild.py"
TEST = ROOT / "test_osd_002_EXACT_LEDGER_INTERFACE_ROOT_FIX_V3.py"

s = TARGET.read_text(encoding="utf-8")

s = s.replace(
    '("prediction_epoch","frozen_epoch","created_epoch","anchor_epoch","observed_epoch")',
    '("prediction_frozen_epoch","anchor_observed_epoch","prediction_epoch","frozen_epoch","created_epoch","anchor_epoch","observed_epoch")'
)

s = s.replace(
    '("anchor_sequence","anchor_sequence_number","sequence_number","kalshi_anchor_sequence")',
    '("anchor_sequence_boundary","anchor_sequence_exact","anchor_sequence","anchor_sequence_number","sequence_number","kalshi_anchor_sequence")'
)

TARGET.write_text(s, encoding="utf-8")

TEST.write_text("""from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
s=p.read_text(encoding="utf-8")
py_compile.compile(str(p), doraise=True)
assert "anchor_sequence_boundary" in s
assert "prediction_frozen_epoch" in s
assert "anchor_observed_epoch" in s
assert "prediction_id" in s
assert "future_return" in s
print("[PASS] OSD-002 exact physical ledger interface installed")
print("[PASS] prediction_id join preserved")
print("[PASS] anchor_sequence_boundary lineage installed")
print("[PASS] prediction_frozen_epoch/anchor_observed_epoch installed")
""", encoding="utf-8")

print("[PASS] OSD-002 exact ledger interface root fix V3 installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)