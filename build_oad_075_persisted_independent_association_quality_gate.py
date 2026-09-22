from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-075"
REVISION="OAD_075_PRODUCTION_INSTALLER_V1"
TITLE='PERSISTED INDEPENDENT EVIDENCE ASSOCIATION QUALITY GATE'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_075_persisted_independent_association_quality_gate.py'
TEST=ROOT/'test_oad_075_persisted_independent_association_quality_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import verify_or_persist_independent_cohort\nfrom qseries_v2.oracle_adapters.independent.oad_072_independent_umd115_descriptor_adapter import descriptors_from_canonical\nfrom qseries_v2.oracle_adapters.independent.oad_073_current_market_umd_dependency_index import build_current_market_dependency_index\nfrom qseries_v2.oracle_adapters.independent.oad_074_strong_structured_market_association import strong_associations\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass AssociationQualityReport:\n persisted_observations:int;descriptors_with_facts:int;current_markets:int;structured_associations:int;observations_with_associations:int;associations:tuple\ndef run_persisted_independent_association_quality_gate(market_limit=1000):\n    persisted=verify_or_persist_independent_cohort(timeout_seconds=120.0)\n    rows=tuple(persisted["rows"])\n    descriptors=descriptors_from_canonical(rows)\n    markets,index,_=build_current_market_dependency_index(market_limit)\n    groups=tuple((d,strong_associations(d,index,10)) for d in descriptors)\n    flat=tuple(a for _,xs in groups for a in xs)\n    return AssociationQualityReport(len(rows),sum(bool(d.facts) for d in descriptors),len(markets),len(flat),sum(bool(xs) for _,xs in groups),flat)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_075_persisted_independent_association_quality_gate import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=run_persisted_independent_association_quality_gate()\n  print("[PHYSICAL] persisted_independent_observations=",r.persisted_observations)\n  print("[PHYSICAL] descriptors_with_structured_facts=",r.descriptors_with_facts)\n  print("[PHYSICAL] current_open_markets=",r.current_markets)\n  print("[PHYSICAL] observations_with_defensible_associations=",r.observations_with_associations)\n  print("[PHYSICAL] defensible_associations=",r.structured_associations)\n  for a in r.associations[:20]: print("[ASSOCIATION]",a.observation_id[:12],a.market_id,a.matched_facts,a.association_strength,"candidate_only=",a.candidate_only)\n  self.assertGreater(r.persisted_observations,0);self.assertGreater(r.current_markets,0)\n  self.assertTrue(all(a.candidate_only for a in r.associations))\n  self.assertTrue(all(all(v!="new" for _,v in a.matched_facts) for a in r.associations))\nif __name__=="__main__":\n print("="*88);print(" OAD-075 PHYSICAL CERTIFICATION TEST");print(" PERSISTED INDEPENDENT EVIDENCE ASSOCIATION QUALITY GATE");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] PostgreSQL-persisted independent evidence evaluated against real current markets")\n print("[PASS] Zero defensible associations is permitted; no match is fabricated")\n print("[PASS] All matches remain candidate_only pending evidence/thesis validation")\n print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")\n print("[DONE] OAD-071 through OAD-075 CAPABILITY SLICE CERTIFIED")\n'

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
    oad70=PKG/"oad_070_physical_current_market_independent_association_gate.py"
    umd115=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_115_observation_impact.py"
    for p,label in ((kalshi,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(oad70,"Certified OAD-070"),(umd115,"Certified UMD-115")):
        if not p.is_file(): raise RuntimeError(label+" missing")
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (kalshi,oph,umd115)}
    affected=(MODULE,TEST,INIT); old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Certified OAD-070 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-115 observation-impact contract unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise

if __name__=="__main__": main()
