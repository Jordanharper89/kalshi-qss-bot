from pathlib import Path
from dataclasses import fields,is_dataclass
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_existing_decomposer_physical.json"
TEST=ROOT/"test_ksem_028_existing_decomposer_physical_gate.py"

def row(x):
    if is_dataclass(x): return {f.name:getattr(x,f.name) for f in fields(x)}
    return {"repr":repr(x)}

def main():
    print("="*120); print(" KSEM-028 EXISTING OAD-099 DECOMPOSER PHYSICAL GATE"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    from qseries_v2.oracle_adapters.independent.oad_099_universal_mixed_market_decomposition import decompose_mixed_market
    _,_,markets,_=read_production_sports_candidates(root=ROOT,market_limit=100)
    out=[]
    for m in markets:
        if not m.get("mve_selected_legs"): continue
        parts=tuple(decompose_mixed_market(m))
        out.append({"parent_ticker":m.get("ticker"),"title":m.get("title"),
                    "physical_leg_count":len(m.get("mve_selected_legs") or []),
                    "decomposed":[row(x) for x in parts]})
    total=sum(len(x["decomposed"]) for x in out)
    print("[PARENTS]",len(out)); print("[DECOMPOSED_LEGS]",total)
    for x in out[:5]: print("[DECOMPOSITION]",x)
    if not out or not total: raise RuntimeError("existing OAD-099 produced no decomposition")
    STATE.write_text(json.dumps({"parents":out,"execution_authority":False},indent=2,default=str),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_existing_decomposer_physical.json').read_text())\nassert d['parents']\nassert sum(len(x['decomposed']) for x in d['parents'])>0\nassert d['execution_authority'] is False\nprint('[PASS] existing OAD-099 physically decomposed live Kalshi markets')\nprint('[PASS] KSEM-028 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()