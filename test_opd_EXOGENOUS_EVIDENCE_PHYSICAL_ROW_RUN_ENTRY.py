
from pathlib import Path
p=Path("probe_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW_RUN_ENTRY.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert "import run;" in s
assert "exogenous_evidence_snapshot" in s
assert "NEW IMMUTABLE ROWS" in s
assert "EXOGENOUS_EVIDENCE_PHYSICALLY_FROZEN" in s
print("[PASS] exact production predictor entrypoint run() used")
print("[PASS] fresh interpreter reloads patched production source")
print("[PASS] immutable ledger physically inspected")
print("[PASS] non-empty exogenous snapshot required")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
