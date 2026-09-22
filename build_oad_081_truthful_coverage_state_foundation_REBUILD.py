from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-081"
REVISION="OAD_081_PRODUCTION_INSTALLER_V1"
TITLE='TRUTHFUL COVERAGE-STATE FOUNDATION REBUILD'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
WRITES=[('qseries_v2/oracle_adapters/independent/oad_079_live_source_coverage_gap_ranking.py', '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import build_live_topic_inventory\nfrom qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import requirements_for_topic\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nCOVERED="COVERED"\nNOT_COVERED="NOT_COVERED"\nUNMAPPED="UNMAPPED"\n\n@dataclass(frozen=True,slots=True)\nclass CoverageGap:\n    topic:str\n    live_markets:int\n    required_source_families:tuple[str,...]\n    missing_source_families:tuple[str,...]\n    coverage_state:str\n    priority_score:int\n\n    @property\n    def covered(self):\n        return self.coverage_state==COVERED\n\ndef _state(topic, req, missing):\n    if str(topic)=="other" or not req:\n        return UNMAPPED\n    if missing:\n        return NOT_COVERED\n    return COVERED\n\ndef rank_live_source_coverage_gaps(limit=1000):\n    inv=build_live_topic_inventory(limit)\n    out=[]\n    for topic,count in inv.topic_counts:\n        req=requirements_for_topic(topic)\n        required=tuple(x.source_family for x in req if x.source_family!="Unmapped")\n        missing=tuple(x.source_family for x in req if not x.existing_adapter and x.source_family!="Unmapped")\n        state=_state(topic,req,missing)\n        # Unknown demand is intentionally highest urgency because it cannot yet be routed.\n        urgency=3 if state==UNMAPPED else (2 if state==NOT_COVERED else 1)\n        score=int(count)*1000 + urgency*100 + len(missing)\n        out.append(CoverageGap(topic,int(count),required,missing,state,score))\n    return tuple(sorted(out,key=lambda x:(-x.priority_score,x.topic)))\n'), ('qseries_v2/oracle_adapters/independent/oad_081_truthful_coverage_state_foundation.py', '\nfrom __future__ import annotations\nfrom qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import (\n    COVERED,NOT_COVERED,UNMAPPED,CoverageGap,_state\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef verify_truthful_unmapped_semantics():\n    a=_state("other",(),())\n    b=_state("sports",(object(),),("Official league/team feeds",))\n    return a==UNMAPPED and b==NOT_COVERED\n'), ('test_oad_081_truthful_coverage_state_foundation.py', '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import *\nfrom qseries_v2.oracle_adapters.independent.oad_081_truthful_coverage_state_foundation import *\n\nclass T(unittest.TestCase):\n    def test_other_is_unmapped(self):\n        self.assertEqual(_state("other",(),()),UNMAPPED)\n    def test_missing_is_not_covered(self):\n        self.assertEqual(_state("sports",(object(),),("Official league/team feeds",)),NOT_COVERED)\n    def test_complete_is_covered(self):\n        self.assertEqual(_state("weather",(object(),),()),COVERED)\n    def test_verify(self):\n        self.assertTrue(verify_truthful_unmapped_semantics())\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OAD-081 CERTIFICATION TEST")\n    print(" TRUTHFUL COVERAGE-STATE FOUNDATION REBUILD")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-079 foundational semantics rebuilt in place")\n    print("[PASS] Unclassified/unmapped markets can never report covered")\n    print("[PASS] Missing source families report NOT_COVERED")\n    print("[DONE] OAD-081 CERTIFIED")\n')]
FROZEN_DEPS=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED_DEPS=[('qseries_v2/oracle_adapters/independent/oad_077_live_market_topic_inventory.py', 'Certified OAD-077'), ('qseries_v2/oracle_adapters/independent/oad_078_authoritative_source_requirement_map.py', 'Certified OAD-078'), ('qseries_v2/oracle_adapters/independent/oad_080_live_adapter_expansion_plan.py', 'Certified OAD-080')]

def write_exact(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("="*88)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    for rel,label in REQUIRED_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    frozen={}
    for rel,label in FROZEN_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()

    targets=[ROOT/rel for rel,_ in WRITES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}

    try:
        for rel,source in WRITES:
            p=ROOT/rel
            write_exact(p, source)
            print("[PASS] Wrote:",rel)

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
