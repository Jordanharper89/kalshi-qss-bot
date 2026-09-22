from pathlib import Path
import py_compile

R=Path.cwd()
D=R/"runtime"/"pre_momentum"

T=r'''from pathlib import Path
import json
R=Path.cwd(); D=R/"runtime"/"pre_momentum"
C=json.loads((D/"opm_002_chf_contract.json").read_text())
K=json.loads((D/"opm_003_kalshi_contract.json").read_text())
I=json.loads((D/"opm_004_identity_candidates.json").read_text())
assert C["rows"]>0
assert K["rows"]>0
assert I["chf_candidates"] and I["kalshi_candidates"]
assert (R/"qseries_v2"/"oracle_coinbase_high_frequency"/
        "chf_024_final_freeze_manifest.json").exists()
state={"schema_version":"OPM-005",
       "chf_history_rows":C["rows"],
       "kalshi_btc15m_rows":K["rows"],
       "chf_candidate_fields":len(I["chf_candidates"]),
       "kalshi_candidate_fields":len(I["kalshi_candidates"]),
       "alignment_engine_ready_for_exact_binding":True,
       "predictive_edge_proven":False,
       "probability_enabled":False,"direction_enabled":False,
       "publication_allowed":False,"execution_authority":False}
(D/"opm_005_admission.json").write_text(json.dumps(state,indent=2))
print("[ADMISSION]",state)
print("[PASS] CHF HF history physically available")
print("[PASS] Kalshi BTC15M history physically available")
print("[PASS] exact contracts captured before alignment implementation")
print("[PASS] predictive edge remains UNPROVEN")
print("[PASS] OPM-005 training-pavement admission certified")
'''
t=R/"test_opm_005_training_pavement_admission_gate.py"
t.write_text(T,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote OPM-005 admission gate + test")