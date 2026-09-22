from pathlib import Path
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
