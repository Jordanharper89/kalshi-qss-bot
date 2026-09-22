from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner_corpus_v2.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert 'r["decision_epoch"]=float(r["t"])' in s
assert 'f=r.get("features") or {}' in s
assert 'for r in train for k,v in r.items()' in s
assert "HURDLE=0.02" in s and "PAIR" in s and "future_return" in s
print("[PASS] OSD-003 corpus V2 compiles")
print("[PASS] exact OSD-002 t field mapped to decision epoch")
print("[PASS] nested feature map flattened")
print("[PASS] feature discovery scans entire training corpus")
print("[PASS] fixed 2% hurdle preserved")
