from pathlib import Path
import py_compile
p=Path("qseries_v2/oracle_strategy_discovery/osd_002_ledger_interface_inspector.py")
py_compile.compile(str(p),doraise=True)
s=p.read_text(encoding="utf-8")
assert "PREDICTION LEDGER" in s and "OUTCOME LEDGER" in s
print("[PASS] OSD-002 ledger interface inspector installed")
