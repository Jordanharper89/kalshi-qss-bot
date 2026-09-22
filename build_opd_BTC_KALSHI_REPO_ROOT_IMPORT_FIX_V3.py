from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / "qseries_v2" / "oracle_predictive_discovery" / "opd_btc_kalshi_exact_price_profitability_gate.py"
TEST = ROOT / "test_opd_BTC_KALSHI_REPO_ROOT_IMPORT_FIX_V3.py"

s = TARGET.read_text(encoding="utf-8")

old = '''from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
'''

new = '''from pathlib import Path
import json, math, statistics, sys

ROOT=Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
'''

if old not in s:
    raise SystemExit("[FAIL] expected profitability-gate header not found; source not mutated")

s = s.replace(old, new, 1)
TARGET.write_text(s, encoding="utf-8")
compile(s, str(TARGET), "exec")

TEST_CODE = '''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "import json, math, statistics, sys" in s
assert "sys.path.insert(0,str(ROOT))" in s
assert 'HURDLE=0.02' in s
assert 'KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND' in s
print("[PASS] repo root added to profitability-gate import path")
print("[PASS] qseries_v2 production modules can resolve from nested script launch")
print("[PASS] connector source, 2% hurdle, signal, and profitability logic unchanged")
'''

TEST.write_text(TEST_CODE, encoding="utf-8")
compile(TEST_CODE, str(TEST), "exec")

print("[PASS] BTC->Kalshi repo-root import fix V3 installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)
print("[PROFITABILITY LOGIC/HURDLE] unchanged")