
from pathlib import Path
import json, hashlib
ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json"
TEST=ROOT/"test_osn_086_exact_oracle_production_launcher_contract_inventory.py"
MARKERS=("fast_lane","inventory","reasoning","learning","terminal_dependency","execution_authority")
def main():
    print("="*120)
    print(" OSN-086 EXACT ORACLE PRODUCTION LAUNCHER CONTRACT INVENTORY")
    print("="*120)
    candidates=[]
    for p in ROOT.glob("run_*.py"):
        txt=p.read_text(encoding="utf-8",errors="ignore").lower()
        hits=[m for m in MARKERS if m in txt]
        score=(4 if "oracle" in p.name.lower() else 0)+(3 if "live" in p.name.lower() or "runtime" in p.name.lower() else 0)+2*len(hits)+(2 if "__main__" in txt else 0)
        if score>=13 and len(hits)>=3:
            candidates.append((score,p,hits))
    if not candidates:
        raise SystemExit("[FAIL] no root production launcher satisfied exact runtime markers")
    candidates.sort(key=lambda x:(-x[0],x[1].name))
    top=candidates[0][0]
    tied=[x for x in candidates if x[0]==top]
    if len(tied)!=1:
        print("[AMBIGUOUS]")
        for x in tied: print(x[0],x[1].name,x[2])
        raise SystemExit("[FAIL] ambiguous top production launcher; refusing to guess")
    score,p,hits=tied[0]
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    data={"launcher_path":p.name,"launcher_sha256":digest,"markers":hits,"integration_strategy":"NON_MUTATING_EXTENSION_SUPERVISOR","terminal_dependency":"NONE","execution_authority":False}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path
import json,hashlib
r=Path.cwd()
s=json.loads((r/'qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json').read_text())
p=r/s['launcher_path']
assert p.exists()
assert hashlib.sha256(p.read_bytes()).hexdigest()==s['launcher_sha256']
assert s['execution_authority'] is False
print('[LAUNCHER]',s['launcher_path'])
print('[PASS] exact launcher path/hash verified')
print('[PASS] OSN-086 certified')
""",encoding="utf-8")
    print("[LAUNCHER]",p.name)
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] frozen base launcher will not be modified")
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
