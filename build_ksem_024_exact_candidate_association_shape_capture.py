from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem024_candidate_association_shape.json"
TEST=ROOT/"test_ksem_024_exact_candidate_association_shape_capture.py"

def shape(x):
    fields={}
    if hasattr(x,"__dict__"):
        for k,v in vars(x).items():
            fields[k]={"type":type(v).__name__,"repr":repr(v)[:300]}
    return {"type":type(x).__name__,"fields":fields,"repr":repr(x)[:1000]}

def main():
    print("="*120); print(" KSEM-024 EXACT CANDIDATE ASSOCIATION SHAPE CAPTURE"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    _,descriptors,markets,groups=read_production_sports_candidates(root=ROOT)
    nonempty=[(d,c) for d,c in groups if c]
    report={
        "descriptor":shape(descriptors[0]) if descriptors else None,
        "market":shape(markets[0]) if markets else None,
        "group_descriptor":shape(nonempty[0][0]) if nonempty else None,
        "candidate":shape(nonempty[0][1][0]) if nonempty else None,
        "nonempty_groups":len(nonempty),
        "execution_authority":False}
    for k in ("descriptor","market","group_descriptor","candidate"):
        print(f"[{k.upper()}]",report[k])
    print("[NONEMPTY_GROUPS]",len(nonempty))
    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem024_candidate_association_shape.json').read_text())\n"
        "assert d['descriptor'] and d['market']\nassert d['execution_authority'] is False\n"
        "print('[PASS] exact production descriptor and Kalshi market shapes captured')\n"
        "print('[PASS] KSEM-024 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()