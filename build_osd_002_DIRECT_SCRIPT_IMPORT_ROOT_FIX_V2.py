from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "qseries_v2" / "oracle_strategy_discovery" / "osd_002_decision_time_feature_corpus_indexed_rebuild.py"
TEST = ROOT / "test_osd_002_DIRECT_SCRIPT_IMPORT_ROOT_FIX_V2.py"

s = TARGET.read_text(encoding="utf-8")

needle = "from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect"
if needle not in s:
    raise SystemExit("[FAIL] exact qseries_v2 import line not found; source not mutated")

prefix = """import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

"""

s = s.replace("from pathlib import Path\n", "", 1)
s = s.replace(needle, prefix + needle, 1)

TARGET.write_text(s, encoding="utf-8")

TEST.write_text("""from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
s=p.read_text(encoding="utf-8")
py_compile.compile(str(p), doraise=True)
assert "REPO_ROOT = Path(__file__).resolve().parents[2]" in s
assert "sys.path.insert(0, str(REPO_ROOT))" in s
assert "from qseries_v2.oracle_production_hardening" in s
print("[PASS] OSD-002 direct-script import root fix V2 installed")
print("[PASS] qseries_v2 repo root injected before package import")
""", encoding="utf-8")

print("[PASS] OSD-002 direct-script import root fix V2 installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)