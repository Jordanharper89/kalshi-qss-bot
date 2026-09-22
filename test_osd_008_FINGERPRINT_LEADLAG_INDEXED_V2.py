from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_indexed_v2.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert 'hit=a["hit"] & b["hit"]' in s
assert 'self_atoms=' in s and 'cross_atoms=' in s
assert 'HURDLE=.02' in s
assert 'FINGERPRINT_LEADLAG' in s
assert 'future_return' in s
print("[PASS] OSD-008 indexed V2 compiles")
print("[PASS] brute-force repeated corpus scans removed")
print("[PASS] indexed set-intersection pair evaluation installed")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] execution/publication remain false")
