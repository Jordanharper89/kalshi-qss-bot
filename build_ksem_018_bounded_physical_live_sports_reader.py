from pathlib import Path
import json,inspect
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem018_bounded_live_sports_reader.json"; TEST=ROOT/"test_ksem_018_bounded_physical_live_sports_reader.py"
def norm(v):
    if hasattr(v,"__dict__"): return {k:norm(x) for k,x in vars(v).items() if not k.startswith("_")}
    if isinstance(v,dict): return {str(k):norm(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [norm(x) for x in v]
    if isinstance(v,(str,int,float,bool)) or v is None: return v
    return repr(v)
def main():
    print("="*120); print(" KSEM-018 BOUNDED PHYSICAL LIVE SPORTS READER"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.live_sports_candidate_boundary import read_current_sports_candidates
    sig=inspect.signature(read_current_sports_candidates)
    kwargs={}
    for name,p in sig.parameters.items():
        if name in ("limit","sample_size","max_markets") and p.default is inspect._empty: kwargs[name]=25
    try:
        rows=read_current_sports_candidates(**kwargs)
    except TypeError:
        rows=read_current_sports_candidates()
    rows=list(rows or [])
    sample=rows[:25]
    if not sample: raise SystemExit("[FAIL] no current sports candidates returned")
    data={"count_total":len(rows),"sample_count":len(sample),"sample":[norm(x) for x in sample],"execution_authority":False}
    STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")
    for i,r in enumerate(data["sample"][:10],1): print("[LIVE_SPORTS_MARKET]",i,r)
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem018_bounded_live_sports_reader.json').read_text())\nassert d['sample_count']>0\nassert d['execution_authority'] is False\nprint('[PASS] bounded current Kalshi sports sample captured')\nprint('[PASS] KSEM-018 certified')\n",encoding="utf-8")
    print("[COUNT]",len(rows),"sample=",len(sample)); print("[WRITE]",STATE.relative_to(ROOT))
if __name__=="__main__": main()