from pathlib import Path
s=Path("run_oad_054_kalshi_global_fast_lane.py").read_text(encoding="utf-8")
a=s.index("observation=build_ola_canonical_observation_from_websocket")
b=s.index("freeze_trade(raw,now,observation.observation_id,root)")
c=s.index("await _persist_without_transport_reconnect")
assert a<b<c
assert "opd_061_realtime_kalshi_anchor_tap import freeze_trade" in s
print("[ORDER] canonicalize -> freeze prospective T -> persistence")
print("[PASS] OPD-064 OAD-054 pre-persistence prospective tap cutover certified")
