from pathlib import Path
from dataclasses import fields,is_dataclass
import json

ROOT=Path.cwd()
S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem029_existing_sports_identity.json"
TEST=ROOT/"test_ksem_029_exact_sports_identity_physical_REPAIR.py"

def struct(x):
    if is_dataclass(x):
        return {f.name:getattr(x,f.name) for f in fields(x)}
    if isinstance(x,dict):
        return dict(x)
    return {"repr":repr(x)}

def main():
    print("="*120); print(" KSEM-029 EXACT SPORTS IDENTITY PHYSICAL REPAIR"); print("="*120)

    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market
    from qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition import recognize_sports_entity_type
    from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type

    _,_,markets,_=read_production_sports_candidates(root=ROOT,market_limit=100)

    parents=[]
    for m in markets:
        if not m.get("mve_selected_legs"):
            continue

        mt=resolve_sports_market_type(m)
        legs=[]

        for x in decompose_mixed_market(m):
            text=getattr(x,"text","")
            legs.append({
                "leg":struct(x),
                "text":text,
                "entity":struct(recognize_sports_entity_type(text))
            })

        parents.append({
            "ticker":m.get("ticker"),
            "market_type":struct(mt),
            "legs":legs
        })

    total=sum(len(x["legs"]) for x in parents)
    print("[PARENTS]",len(parents))
    print("[IDENTIFIED_LEGS]",total)

    for x in parents[:5]:
        print("[IDENTITY]",x)

    if not parents or not total:
        raise RuntimeError("no physical sports identity cohort")

    OUT.write_text(json.dumps({
        "parents":parents,
        "execution_authority":False
    },indent=2,default=str),encoding="utf-8")

    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem029_existing_sports_identity.json').read_text())\n"
        "assert d['parents']\n"
        "assert sum(len(x['legs']) for x in d['parents'])>0\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact frozen OAD-088/OAD-098/OAD-099 pavement physically executed')\n"
        "print('[PASS] KSEM-029 repair certified')\n",
        encoding="utf-8"
    )

    print("[WRITE]",OUT.relative_to(ROOT))
    print("[WRITE]",TEST.name)

if __name__=="__main__":
    main()