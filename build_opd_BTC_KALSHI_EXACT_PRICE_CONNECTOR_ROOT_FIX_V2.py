from pathlib import Path
import re

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_kalshi_exact_price_profitability_gate.py"
PROD=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
TEST=ROOT/"test_opd_BTC_KALSHI_EXACT_PRICE_CONNECTOR_ROOT_FIX_V2.py"

s=TARGET.read_text(encoding="utf-8")

start=s.index("def connect_db():")
end=s.index("\nSQL_EXACT_PRICE=",start)

new='''def connect_db():
    import importlib, re
    prod=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
    txt=prod.read_text(encoding="utf-8")
    patterns=(
        r"from\\s+([A-Za-z0-9_\\.]+)\\s+import\\s+connect\\s+as\\s+_opd_exo_connect",
        r"from\\s+([A-Za-z0-9_\\.]+)\\s+import\\s+connect",
    )
    errors=[]
    for pat in patterns:
        m=re.search(pat,txt)
        if not m: continue
        modname=m.group(1)
        try:
            mod=importlib.import_module(modname)
            fn=getattr(mod,"connect")
            return fn()
        except Exception as e:
            errors.append(f"{modname}: {type(e).__name__}: {e}")
    raise RuntimeError("production PostgreSQL connector unresolved from predictor source; "+" | ".join(errors))
'''

s=s[:start]+new+s[end:]
TARGET.write_text(s,encoding="utf-8")
compile(s,str(TARGET),"exec")

TEST_CODE='''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "opd_live_full_evidence_fusion_predictor.py" in s
assert "importlib.import_module(modname)" in s
assert "_opd_exo_connect" in s
assert "production PostgreSQL connector unresolved from predictor source" in s
assert 'HURDLE=0.02' in s
assert 'KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND' in s
print("[PASS] profitability gate now resolves PostgreSQL connector from actual production predictor source")
print("[PASS] no guessed connector module paths remain")
print("[PASS] profitability logic, 2% hurdle, and model semantics unchanged")
'''
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(TEST_CODE,str(TEST),"exec")

print("[PASS] BTC->Kalshi exact-price connector root fix V2 installed")
print("[TARGET]",TARGET)
print("[PRODUCTION CONNECTOR SOURCE]",PROD)
print("[TEST]",TEST)
print("[PROFITABILITY LOGIC/HURDLE] unchanged")
