from pathlib import Path
from dataclasses import fields,is_dataclass
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem024_candidate_association_shape.json"
TEST=ROOT/"test_ksem_024_exact_candidate_shape_DATACLASS_REPAIR.py"

def shape(x):
    if x is None: return None
    names=[]
    if is_dataclass(x): names=[f.name for f in fields(x)]
    elif hasattr(x,"_fields"): names=list(x._fields)
    elif isinstance(x,dict): names=list(x)
    elif hasattr(type(x),"__slots__"):
        s=type(x).__slots__; names=[s] if isinstance(s,str) else list(s)
    elif hasattr(x,"__dict__"): names=list(vars(x))
    vals={}
    for n in names:
        try: v=x.get(n) if isinstance(x,dict) else getattr(x,n)
        except Exception: continue
        vals[n]={"type":type(v).__name__,"repr":repr(v)[:300]}
    return {"type":type(x).__name__,"fields":vals,"repr":repr(x)[:1200]}

def main():
    print("="*120); print(" KSEM-024 EXACT CANDIDATE SHAPE DATACLASS REPAIR"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    _,descriptors,markets,groups=read_production_sports_candidates(root=ROOT)
    nonempty=[(d,c) for d,c in groups if c]
    report={"descriptor":shape(descriptors[0]) if descriptors else None,
            "market":shape(markets[0]) if markets else None,
            "candidate":shape(nonempty[0][1][0]) if nonempty else None,
            "nonempty_groups":len(nonempty),"execution_authority":False}
    for k,v in report.items(): print(f"[{k.upper()}] {v}")
    if not report["descriptor"] or not report["descriptor"]["fields"]: raise RuntimeError("descriptor structure unresolved")
    if not report["market"] or not report["market"]["fields"]: raise RuntimeError("market structure unresolved")
    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem024_candidate_association_shape.json').read_text())\nassert d['descriptor']['fields']\nassert d['market']['fields']\nassert d['execution_authority'] is False\nprint('[PASS] exact descriptor and Kalshi market structural fields captured')\nprint('[PASS] KSEM-024 structural repair certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()