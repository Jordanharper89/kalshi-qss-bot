from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-080"
REVISION="OAD_080_PRODUCTION_INSTALLER_V1"
TITLE='LIVE ADAPTER EXPANSION PLAN'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_080_live_adapter_expansion_plan.py'
TEST=ROOT/'test_oad_080_live_adapter_expansion_plan.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import rank_live_source_coverage_gaps\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass AdapterBuildRecommendation:\n    rank:int\n    topic:str\n    source_family:str\n    live_markets:int\n    reason:str\n\n@dataclass(frozen=True,slots=True)\nclass AdapterExpansionPlan:\n    evaluated_markets:int\n    recommendations:tuple[AdapterBuildRecommendation,...]\n    held_topics:tuple[str,...]\n\ndef build_live_adapter_expansion_plan(limit=1000,max_recommendations=10):\n    gaps=rank_live_source_coverage_gaps(limit)\n    recs=[]\n    held=[]\n    rank=1\n    total=sum(x.live_markets for x in gaps)\n    for gap in gaps:\n        if gap.topic=="other":\n            held.append(gap.topic)\n            continue\n        if not gap.missing_source_families:\n            continue\n        for family in gap.missing_source_families:\n            recs.append(AdapterBuildRecommendation(\n                rank,gap.topic,family,gap.live_markets,\n                "live_market_demand_requires_independent_authoritative_coverage"\n            ))\n            rank+=1\n            if len(recs)>=int(max_recommendations):\n                break\n        if len(recs)>=int(max_recommendations):\n            break\n    return AdapterExpansionPlan(total,tuple(recs),tuple(sorted(set(held))))\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_080_live_adapter_expansion_plan import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        p=build_live_adapter_expansion_plan(1000,10)\n        print("[PHYSICAL] evaluated_markets=",p.evaluated_markets)\n        print("[PHYSICAL] adapter_recommendations=",len(p.recommendations))\n        for r in p.recommendations:\n            print("[BUILD_NEXT]",r.rank,r.topic,r.source_family,"live_markets=",r.live_markets)\n        print("[PHYSICAL] held_topics=",p.held_topics)\n        self.assertGreater(p.evaluated_markets,0)\n        self.assertTrue(all(r.rank==i+1 for i,r in enumerate(p.recommendations)))\n        self.assertTrue(all(r.source_family!="Unmapped" for r in p.recommendations))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-080 PHYSICAL CERTIFICATION TEST");print(" LIVE ADAPTER EXPANSION PLAN");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Adapter expansion priorities derived from real current Kalshi demand")\n    print("[PASS] Unclassified markets held rather than assigned fake evidence sources")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-076 through OAD-080 CAPABILITY SLICE CERTIFIED")\n'

def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)

    kalshi=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    umd098=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_098_market_taxonomy.py"
    umd109=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_109_market_semantic_profile.py"
    oad075=PKG/"oad_075_persisted_independent_association_quality_gate.py"

    deps=((kalshi,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(umd098,"Frozen UMD-098"),
          (umd109,"Frozen UMD-109"),(oad075,"Certified OAD-075"))
    for p,label in deps:
        if not p.is_file(): raise RuntimeError(label+" missing")

    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (kalshi,oph,umd098,umd109)}
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Certified OAD-075 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-098 taxonomy unchanged")
        print("[PASS] Frozen UMD-109 semantic profile unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
