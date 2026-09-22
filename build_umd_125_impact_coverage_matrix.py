from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_125_IMPACT_COVERAGE_MATRIX_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_125_impact_coverage_matrix.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_125_impact_coverage_matrix.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_121_impact_family_projection import FamilyImpactProjection\nfrom .umd_124_cross_venue_cohort import CrossVenueImpactCohort, verify_umd_124_cross_venue_impact_cohort\n\nUMD_125_BUILD_ID="UMD-125"\nUMD_125_REVISION="UMD_125_IMPACT_COVERAGE_MATRIX_V1"\nUMD_125_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ImpactCoverageMatrix:\n    observation_hash:str\n    family_to_markets:Mapping[str,Tuple[str,...]]\n    venue_to_markets:Mapping[str,Tuple[str,...]]\n    cross_venue_market_ids:Tuple[str,...]\n    direct_market_ids:Tuple[str,...]\n    propagated_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"family_to_markets",_freeze_index(self.family_to_markets))\n        object.__setattr__(self,"venue_to_markets",_freeze_index(self.venue_to_markets))\n        for name in ("cross_venue_market_ids","direct_market_ids","propagated_market_ids"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if set(self.direct_market_ids)&set(self.propagated_market_ids):\n            raise ValueError("direct and propagated market sets must not overlap")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_125_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-125")\n\n    def markets_for_family(self,family_key:str)->Tuple[str,...]:\n        return self.family_to_markets.get(family_key,())\n\n    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:\n        return self.venue_to_markets.get(venue_key,())\n\n    @property\n    def matrix_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "family_to_markets":self.family_to_markets,\n            "venue_to_markets":self.venue_to_markets,\n            "cross_venue_market_ids":self.cross_venue_market_ids,\n            "direct_market_ids":self.direct_market_ids,\n            "propagated_market_ids":self.propagated_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ImpactCoverageMatrixBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        family_projection:FamilyImpactProjection,\n        cohort:CrossVenueImpactCohort,\n        *,\n        lineage:ImmutableLineage,\n    )->ImpactCoverageMatrix:\n        if not isinstance(family_projection,FamilyImpactProjection):\n            raise TypeError("family_projection must be FamilyImpactProjection")\n        if not isinstance(cohort,CrossVenueImpactCohort):\n            raise TypeError("cohort must be CrossVenueImpactCohort")\n        if family_projection.observation_hash!=cohort.observation_hash:\n            raise ValueError("observation hashes do not match")\n\n        family={}\n        direct=set()\n        propagated=set()\n        for impact in family_projection.family_impacts:\n            family[impact.family_key]=tuple(impact.impacted_market_ids)\n            direct.update(impact.direct_market_ids)\n            propagated.update(impact.propagated_market_ids)\n\n        venue={}\n        for market in cohort.markets:\n            target=direct if market.direct else propagated\n            target.add(market.canonical_market_id)\n            for venue_key in market.venue_keys:\n                venue.setdefault(venue_key,[]).append(market.canonical_market_id)\n\n        for key,values in venue.items():\n            venue[key]=tuple(sorted(set(values)))\n\n        return ImpactCoverageMatrix(\n            family_projection.observation_hash,\n            family,\n            venue,\n            cohort.cross_venue_market_ids(),\n            tuple(sorted(direct)),\n            tuple(sorted(propagated)),\n            lineage,\n        )\n\ndef build_umd_125_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_125_BUILD_ID,"revision":UMD_125_REVISION,\n        "schema_version":UMD_125_SCHEMA_VERSION,"upstream_builds":("UMD-121","UMD-124"),\n        "mode":"deterministic_read_only_impact_coverage_matrix",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_125_impact_coverage_matrix()->bool:\n    if verify_umd_124_cross_venue_impact_cohort() is not True:\n        return False\n    m=build_umd_125_certification_manifest()\n    return m["build_id"]=="UMD-125" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_121_impact_family_projection import FamilyImpact,FamilyImpactProjection\nfrom qseries_v2.universal_market_discovery.umd_124_cross_venue_cohort import MarketVenueCohort,CrossVenueImpactCohort\nfrom qseries_v2.universal_market_discovery.umd_125_impact_coverage_matrix import *\n\nFIXED=datetime(2026,8,9,22,10,tzinfo=timezone.utc)\n\ndef family_projection():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision="UMD_121_IMPACT_FAMILY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125/121",),created_at=FIXED)\n    return FamilyImpactProjection(\n        "a"*64,\n        (\n            FamilyImpact("asset=bitcoin","b"*64,("m1","m2"),("m1",),("m2",)),\n            FamilyImpact("asset=ethereum","c"*64,("m3",),("m3",),()),\n        ),\n        (),\n        l,\n    )\n\ndef cohort():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-124",revision="UMD_124_CROSS_VENUE_IMPACT_COHORT_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125/124",),created_at=FIXED)\n    return CrossVenueImpactCohort(\n        "a"*64,\n        (\n            MarketVenueCohort("m1",("kalshi","polymarket"),(("kalshi","K-1"),("polymarket","P-1")),True),\n            MarketVenueCohort("m2",("kalshi",),(("kalshi","K-2"),),False),\n            MarketVenueCohort("m3",("polymarket",),(("polymarket","P-3"),),True),\n        ),\n        l,\n    )\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-125",revision=UMD_125_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125",),created_at=FIXED)\n\nclass TestUMD125(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_125_impact_coverage_matrix())\n    def test_family_matrix(self):\n        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        self.assertEqual(m.markets_for_family("asset=bitcoin"),("m1","m2"))\n    def test_venue_matrix(self):\n        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        self.assertEqual(m.markets_for_venue("kalshi"),("m1","m2"))\n        self.assertEqual(m.markets_for_venue("polymarket"),("m1","m3"))\n    def test_cross_venue_markets(self):\n        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        self.assertEqual(m.cross_venue_market_ids,("m1",))\n    def test_direct_propagated(self):\n        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        self.assertEqual(m.direct_market_ids,("m1","m3"))\n        self.assertEqual(m.propagated_market_ids,("m2",))\n    def test_mismatch_rejected(self):\n        c=cohort()\n        wrong=CrossVenueImpactCohort("b"*64,c.markets,c.lineage)\n        with self.assertRaises(ValueError):\n            ImpactCoverageMatrixBuilder().build(family_projection(),wrong,lineage=lineage())\n    def test_deterministic(self):\n        a=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        b=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())\n        self.assertEqual(a.matrix_hash,b.matrix_hash)\n    def test_side_effects(self):\n        m=build_umd_125_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-125 CERTIFICATION TEST");print(" IMPACT COVERAGE MATRIX");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD125))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_125_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation coverage matrix across families and venues certified")\n    print("[PASS] Cross-venue, direct, and propagated market coverage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-125 CERTIFIED")\n'
UPSTREAM_MODULE='umd_124_cross_venue_cohort'
UPSTREAM_VERIFIER='verify_umd_124_cross_venue_impact_cohort'
EXPORTED_NAMES=('UMD_125_REVISION', 'ImpactCoverageMatrix', 'ImpactCoverageMatrixBuilder', 'build_umd_125_certification_manifest', 'verify_umd_125_impact_coverage_matrix')

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        mod=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        verifier=getattr(mod,UPSTREAM_VERIFIER,None)
        if verifier is None:
            raise RuntimeError(f"Certified upstream verifier missing: {UPSTREAM_MODULE}.{UPSTREAM_VERIFIER}")
        if verifier() is not True:
            raise RuntimeError(f"Certified upstream verification failed: {UPSTREAM_MODULE}")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker="# UMD-125 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {name},\n" for name in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None)
        importlib.invalidate_caches()
        mod=importlib.import_module(name)
        missing=[name for name in EXPORTED_NAMES if not hasattr(mod,name)]
        if missing:
            raise RuntimeError("UMD-125 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-125 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-125 INSTALLER")
    print(" IMPACT COVERAGE MATRIX")
    print("="*72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")
    verify_upstream()
    print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        verify_current()
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-125 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-125',
        "revision":REVISION,
        "module":MODULE.name,
        "test":TEST.name,
        "files":{
            str(MODULE.relative_to(ROOT)):sha256_file(MODULE),
            str(INIT.relative_to(ROOT)):sha256_file(INIT),
            str(TEST.relative_to(ROOT)):sha256_file(TEST),
        },
        "network_enabled":False,
        "persistence_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {digest}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-125 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
