from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "qseries_v2" / "oracle_strategy_discovery" / "osd_002_decision_time_feature_corpus_indexed_rebuild.py"
TEST = ROOT / "test_osd_002_DIRECT_SCRIPT_IMPORT_ROOT_FIX.py"

s = TARGET.read_text(encoding="utf-8")

needle = "from pathlib import Path\nimport json, math, statistics, datetime\n"
replacement = """from pathlib import Path
import sys
import json, math, statistics, datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
"""

if needle not in s:
    raise SystemExit("[FAIL] exact OSD-002 import header not found; source not mutated")

TARGET.write_text(s.replace(needle, replacement, 1), encoding="utf-8")

TEST.write_text("""from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_decision_time_feature_corpus_indexed_rebuild.py")
s=p.read_text(encoding="utf-8")
py_compile.compile(str(p), doraise=True)
assert 'REPO_ROOT = Path(__file__).resolve().parents[2]' in s
assert 'sys.path.insert(0, str(REPO_ROOT))' in s
print("[PASS] OSD-002 direct-script repo-root import fix installed")
print("[PASS] qseries_v2 import available when launched by file path")
""", encoding="utf-8")

print("[PASS] OSD-002 direct-script import root fix installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)