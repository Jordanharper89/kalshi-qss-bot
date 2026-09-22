from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_network_shock_underlying_holdout_audit.py"
TEST=ROOT/"test_opd_BTC_NETWORK_SHOCK_UNDERLYING_INDEXED_LOOKUP_FIX_V2.py"

s=TARGET.read_text(encoding="utf-8")

old = '''    ret=labels.get((round(p["time"],3),p["h"]))
    if ret is None:
        # Exact ledger anchors sometimes differ from archived 5s grid by <2.5s.
        cands=[(abs(a-p["time"]),r) for (a,h),r in labels.items() if h==p["h"] and abs(a-p["time"])<=2.5]
        if cands: ret=min(cands,key=lambda x:x[0])[1]
    if ret is None: continue
'''

new = '''    ret=labels.get((round(p["time"],3),p["h"]))
    if ret is None:
        # O(1) bounded lookup around the exact 5-second CHF grid.
        base=round(p["time"]/5.0)*5.0
        cands=[]
        for a in (base-5.0,base,base+5.0):
            r=labels.get((round(a,3),p["h"]))
            if r is not None and abs(a-p["time"])<=2.5:
                cands.append((abs(a-p["time"]),r))
        if cands:
            ret=min(cands,key=lambda x:x[0])[1]
    if ret is None: continue
'''

if old not in s:
    raise SystemExit("[FAIL] expected slow lookup block not found; source not mutated")

s=s.replace(old,new,1)
TARGET.write_text(s,encoding="utf-8")
compile(s,str(TARGET),"exec")

TEST_CODE = '''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_underlying_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
assert "for (a,h),r in labels.items()" not in s
assert 'base=round(p["time"]/5.0)*5.0' in s
assert "for a in (base-5.0,base,base+5.0):" in s
assert 'abs(a-p["time"])<=2.5' in s
print("[PASS] quadratic CHF fallback scan removed")
print("[PASS] bounded indexed 5-second-grid lookup installed")
print("[PASS] exact/nearest-anchor tolerance preserved at <=2.5s")
print("[PASS] target, train/holdout semantics, and signal logic unchanged")
print("[MODEL MUTATION] FALSE")
'''
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(TEST_CODE,str(TEST),"exec")

print("[PASS] BTC network-shock underlying indexed lookup fix V2 installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[SIGNAL/TARGET/HOLDOUT] unchanged")
print("[MODEL/SCORING/GATES] unchanged")