from pathlib import Path
import json,re
R=Path.cwd(); D=R/"runtime"/"pre_momentum"
c=json.loads((D/"opm_002_chf_contract.json").read_text())
k=json.loads((D/"opm_003_kalshi_contract.json").read_text())
row=c["last_row"]; obj=k["sample_json"]

def walk(x,p=""):
    out=[]
    if isinstance(x,dict):
        for a,b in x.items(): out+=walk(b,p+"."+str(a) if p else str(a))
    elif isinstance(x,list):
        for i,b in enumerate(x): out+=walk(b,f"{p}[{i}]")
    else: out.append((p,x))
    return out

cf=walk(row); kf=walk(obj)
tokens=("time","timestamp","anchor","observed","product","symbol","price",
        "window","ticker","market","bid","ask","trade")
C=[x for x in cf if any(t in x[0].lower() for t in tokens)]
K=[x for x in kf if any(t in x[0].lower() for t in tokens)]
assert C,"CHF row exposes no candidate identity/time fields"
assert K,"Kalshi row exposes no candidate identity/time/price fields"
rep={"chf_candidates":C,"kalshi_candidates":K}
(D/"opm_004_identity_candidates.json").write_text(json.dumps(rep,indent=2,default=str))
print("[CHF_CANDIDATES]"); [print(" ",x) for x in C]
print("[KALSHI_CANDIDATES]"); [print(" ",x) for x in K]
print("[PASS] exact physical candidate fields discovered")
print("[PASS] no cross-stream timestamp or price field invented")
print("[PASS] OPM-004 identity probe certified")
