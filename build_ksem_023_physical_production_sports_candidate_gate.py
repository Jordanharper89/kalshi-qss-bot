from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem023_physical_production_sports_candidate_gate.json"
TEST=ROOT/"test_ksem_023_physical_production_sports_candidate_gate.py"

def main():
    print("="*120); print(" KSEM-023 PHYSICAL PRODUCTION SPORTS CANDIDATE GATE"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    cohort,descriptors,markets,groups=read_production_sports_candidates(root=ROOT)
    with_candidates=sum(1 for _,candidates in groups if candidates)
    candidate_count=sum(len(candidates) for _,candidates in groups)
    report={
        "persisted_observations":int(cohort.cohort_size),
        "providers":list(cohort.providers),
        "structured_descriptors":len(descriptors),
        "current_markets":len(markets),
        "descriptor_groups":len(groups),
        "observations_with_candidates":with_candidates,
        "association_candidates":candidate_count,
        "execution_authority":False}
    for k,v in report.items(): print(f"[{k.upper()}] {v}")
    if not descriptors: raise RuntimeError("no persisted sports descriptors")
    if not markets: raise RuntimeError("no current Kalshi markets")
    if len(groups)!=len(descriptors): raise RuntimeError("descriptor/group accounting mismatch")
    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem023_physical_production_sports_candidate_gate.json').read_text())\n"
        "assert d['structured_descriptors']>0\nassert d['current_markets']>0\n"
        "assert d['descriptor_groups']==d['structured_descriptors']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] persisted sports descriptors physically compared with current Kalshi markets')\n"
        "print('[PASS] KSEM-023 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()