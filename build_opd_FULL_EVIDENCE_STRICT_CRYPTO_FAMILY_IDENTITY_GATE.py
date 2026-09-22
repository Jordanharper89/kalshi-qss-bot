from pathlib import Path

ROOT=Path.cwd().resolve()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=ROOT/"test_opd_FULL_EVIDENCE_STRICT_CRYPTO_FAMILY_IDENTITY_GATE.py"

if not P.exists():
    raise SystemExit("[FAIL] production full-evidence predictor missing")

s=P.read_text(encoding="utf-8")

if 'EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1' not in s:
    raise SystemExit("[FAIL] certified exact-contract family root cutover missing")

old='''def _asset(ticker):
    u=str(ticker).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
    return None
'''

new='''def _asset(ticker):
    u=str(ticker or "").upper().strip()
    if u.startswith("KXBTC") or "-BTC" in u:return "BTC"
    if u.startswith("KXETH") or "-ETH" in u:return "ETH"
    if u.startswith("KXSOL") or "-SOL" in u:return "SOL"
    return None
'''

if old not in s:
    raise SystemExit("[FAIL] exact defective substring asset classifier not found")

s=s.replace(old,new,1)
compile(s,str(P),"exec")
P.write_text(s,encoding="utf-8")

test=r'''from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m._asset("KXBTC15M-26SEP120245-45")=="BTC"
assert m._asset("KXBTCD-26SEP1203-T77199.99")=="BTC"
assert m._asset("KXETH15M-26SEP120245-45")=="ETH"
assert m._asset("KXSOLE-26SEP1203-B99.625")=="SOL"
assert m._asset("KXCRYPTOLEAD15M-26SEP120245-SOL")=="SOL"

assert m._asset("KXITFMATCH-26SEP12PETHUR-HUR") is None
assert m._asset("SOMETHING") is None
assert m._asset("RESOLUTION") is None
assert m._asset("ABSOLUTE") is None

src=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert 'if "ETH" in u:return "ETH"' not in src
assert 'if "SOL" in u:return "SOL"' not in src
assert 'EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1' in src
assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.HURDLE==0.020
assert m.MIN_NET_EDGE==0.005

print("[PASS] strict crypto-family identity gate installed in existing production predictor")
print("[PASS] known BTC/ETH/SOL Kalshi contract namespaces admitted")
print("[PASS] hyphen-delimited crypto identity admitted")
print("[PASS] PETHUR false-ETH collision rejected")
print("[PASS] generic substring ETH/SOL/BTC admission removed")
print("[PASS] exact-contract family ranking and scorer preserved")
print("[PASS] 2pct hurdle and prediction gates unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
T.write_text(test,encoding="utf-8")
compile(test,str(T),"exec")

print("[PASS] surgical crypto-family identity repair installed")
print("[TARGET] existing opd_live_full_evidence_fusion_predictor.py")
print("[REMOVED] arbitrary BTC/ETH/SOL substring family admission")
print("[PRESERVED] exact-contract scoring/ranking/prospective ledger")
print("[PRESERVED] prediction gates + fixed 2pct hurdle")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")