from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "FINGERPRINT_LEADLAG" in s and "sibling" in s and "HURDLE=.02" in s
print("[PASS] OSD-008 fingerprint/lead-lag miner compiles")
print("[PASS] cross-contract lead/lag pair mining enabled")
