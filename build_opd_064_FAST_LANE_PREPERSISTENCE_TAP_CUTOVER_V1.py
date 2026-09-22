from pathlib import Path
RUNNER=Path("run_oad_054_kalshi_global_fast_lane.py")
s=RUNNER.read_text(encoding="utf-8")
needle="from qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification import classify_persistence_failure"
imp=needle+"\nfrom qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap import freeze_trade"
if "opd_061_realtime_kalshi_anchor_tap" not in s:
    if needle not in s:raise RuntimeError("EXACT_OAD054_IMPORT_BOUNDARY_NOT_FOUND")
    s=s.replace(needle,imp,1)
needle2='observation=build_ola_canonical_observation_from_websocket(raw,received_at=now,acquisition_batch_id=f"batch.oad054.{persisted+1}.{now.strftime(\'%Y%m%dT%H%M%S%fZ\')}")'
repl=needle2+'\n                    freeze_trade(raw,now,observation.observation_id,root)'
if "freeze_trade(raw,now,observation.observation_id,root)" not in s:
    if needle2 not in s:raise RuntimeError("EXACT_OAD054_PREPERSIST_BOUNDARY_NOT_FOUND")
    s=s.replace(needle2,repl,1)
RUNNER.write_text(s,encoding="utf-8")
TEST=r'''from pathlib import Path
s=Path("run_oad_054_kalshi_global_fast_lane.py").read_text(encoding="utf-8")
a=s.index("observation=build_ola_canonical_observation_from_websocket")
b=s.index("freeze_trade(raw,now,observation.observation_id,root)")
c=s.index("await _persist_without_transport_reconnect")
assert a<b<c
assert "opd_061_realtime_kalshi_anchor_tap import freeze_trade" in s
print("[ORDER] canonicalize -> freeze prospective T -> persistence")
print("[PASS] OPD-064 OAD-054 pre-persistence prospective tap cutover certified")
'''
Path("test_opd_064_fast_lane_prepersistence_tap_cutover_V1.py").write_text(TEST,encoding="utf-8")
print("[PASS] OPD-064 V1 installed")
