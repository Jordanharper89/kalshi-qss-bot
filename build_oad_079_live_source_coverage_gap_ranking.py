from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-079"
REVISION="OAD_079_PRODUCTION_INSTALLER_V1"
TITLE='LIVE SOURCE COVERAGE GAP RANKING'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_079_live_source_coverage_gap_ranking.py'
TEST=ROOT/'test_oad_079_live_source_coverage_gap_ranking.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import build_live_topic_inventory\nfrom qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import requirements_for_topic\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass CoverageGap:\n    topic:str\n    live_markets:int\n    required_source_families:tuple[str,...]\n    missing_source_families:tuple[str,...]\n    covered:bool\n    priority_score:int\n\ndef rank_live_source_coverage_gaps(limit=1000):\n    inv=build_live_topic_inventory(limit)\n    out=[]\n    for topic,count in inv.topic_counts:\n        req=requirements_for_topic(topic)\n        required=tuple(x.source_family for x in req if x.source_family!="Unmapped")\n        missing=tuple(x.source_family for x in req if not x.existing_adapter and x.source_family!="Unmapped")\n        covered=bool(req) and not missing\n        # Market count is intentionally dominant; missing family count breaks ties.\n        score=int(count)*100+len(missing)\n        out.append(CoverageGap(topic,int(count),required,missing,covered,score))\n    return tuple(sorted(out,key=lambda x:(-x.priority_score,x.topic)))\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        rows=rank_live_source_coverage_gaps(1000)\n        print("[PHYSICAL] ranked_topics=",len(rows))\n        for x in rows:\n            print("[GAP]",x.topic,"markets=",x.live_markets,"covered=",x.covered,"missing=",x.missing_source_families,"priority=",x.priority_score)\n        self.assertGreater(len(rows),0)\n        self.assertTrue(all(rows[i].priority_score>=rows[i+1].priority_score for i in range(len(rows)-1)))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-079 PHYSICAL CERTIFICATION TEST");print(" LIVE SOURCE COVERAGE GAP RANKING");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Missing adapter families ranked by actual live-market demand")\n    print("[DONE] OAD-079 CERTIFIED")\n'

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
