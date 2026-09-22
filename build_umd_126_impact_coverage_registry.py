from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_126_IMPACT_COVERAGE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_126_impact_coverage_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_126_impact_coverage_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_125_impact_coverage_matrix import ImpactCoverageMatrix, verify_umd_125_impact_coverage_matrix\n\nUMD_126_BUILD_ID="UMD-126"\nUMD_126_REVISION="UMD_126_IMPACT_COVERAGE_REGISTRY_V1"\nUMD_126_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ImpactCoverageRegistry:\n    matrices:Tuple[ImpactCoverageMatrix,...]\n    family_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    cross_venue_index:Mapping[str,Tuple[str,...]]\n    market_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"matrices",tuple(self.matrices))\n        for name in ("family_index","venue_index","cross_venue_index","market_index"):\n            object.__setattr__(self,name,_freeze_index(getattr(self,name)))\n        if self.matrices!=tuple(sorted(self.matrices,key=lambda m:(m.observation_hash,m.matrix_hash))):\n            raise ValueError("matrices must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_126_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-126")\n        required={m.matrix_hash for m in self.matrices}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every matrix hash")\n\n    def observations_for_family(self,family_key:str)->Tuple[str,...]:\n        return self.family_index.get(family_key,())\n\n    def observations_for_venue(self,venue_key:str)->Tuple[str,...]:\n        return self.venue_index.get(venue_key,())\n\n    def observations_for_cross_venue_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.cross_venue_index.get(canonical_market_id,())\n\n    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.market_index.get(canonical_market_id,())\n\n    def observations_for_family_and_venue(self,family_key:str,venue_key:str)->Tuple[str,...]:\n        return tuple(sorted(\n            set(self.observations_for_family(family_key)) &\n            set(self.observations_for_venue(venue_key))\n        ))\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "matrix_hashes":tuple(m.matrix_hash for m in self.matrices),\n            "family_index":self.family_index,\n            "venue_index":self.venue_index,\n            "cross_venue_index":self.cross_venue_index,\n            "market_index":self.market_index,\n            "lineage":self.lineage,\n        })\n\nclass ImpactCoverageRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        matrices:Iterable[ImpactCoverageMatrix],\n        *,\n        lineage_factory,\n    )->ImpactCoverageRegistry:\n        values=tuple(matrices)\n        if any(not isinstance(m,ImpactCoverageMatrix) for m in values):\n            raise TypeError("matrices must contain ImpactCoverageMatrix")\n        values=tuple(sorted(values,key=lambda m:(m.observation_hash,m.matrix_hash)))\n\n        family={}\n        venue={}\n        cross={}\n        market={}\n\n        for matrix in values:\n            obs=matrix.observation_hash\n            for family_key in matrix.family_to_markets:\n                family.setdefault(family_key,[]).append(obs)\n            for venue_key in matrix.venue_to_markets:\n                venue.setdefault(venue_key,[]).append(obs)\n            for market_id in matrix.cross_venue_market_ids:\n                cross.setdefault(market_id,[]).append(obs)\n            all_markets=set(matrix.direct_market_ids)|set(matrix.propagated_market_ids)\n            for market_id in all_markets:\n                market.setdefault(market_id,[]).append(obs)\n\n        for index in (family,venue,cross,market):\n            for key,obs in index.items():\n                index[key]=tuple(sorted(set(obs)))\n\n        lineage=lineage_factory(tuple(m.matrix_hash for m in values))\n        return ImpactCoverageRegistry(values,family,venue,cross,market,lineage)\n\ndef build_umd_126_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_126_BUILD_ID,"revision":UMD_126_REVISION,\n        "schema_version":UMD_126_SCHEMA_VERSION,"upstream_builds":("UMD-125",),\n        "mode":"deterministic_read_only_impact_coverage_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_126_impact_coverage_registry()->bool:\n    if verify_umd_125_impact_coverage_matrix() is not True:\n        return False\n    m=build_umd_126_certification_manifest()\n    return m["build_id"]=="UMD-126" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\nfrom types import MappingProxyType\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_125_impact_coverage_matrix import ImpactCoverageMatrix\nfrom qseries_v2.universal_market_discovery.umd_126_impact_coverage_registry import *\n\nFIXED=datetime(2026,8,9,22,20,tzinfo=timezone.utc)\n\ndef matrix(obs_hash,family_key,venue_key,market_id,cross=False):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-125",revision="UMD_125_IMPACT_COVERAGE_MATRIX_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://126/125",),created_at=FIXED)\n    return ImpactCoverageMatrix(\n        obs_hash,\n        {family_key:(market_id,)},\n        {venue_key:(market_id,)},\n        (market_id,) if cross else (),\n        (market_id,),\n        (),\n        l,\n    )\n\ndef lineage_factory(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-126",revision=UMD_126_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://126",),created_at=FIXED)\n\nclass TestUMD126(unittest.TestCase):\n    def setUp(self):\n        self.a=matrix("a"*64,"asset=bitcoin","kalshi","m1",True)\n        self.b=matrix("b"*64,"asset=bitcoin","polymarket","m2",False)\n        self.c=matrix("c"*64,"asset=ethereum","kalshi","m3",False)\n        self.r=ImpactCoverageRegistryBuilder().build((self.c,self.b,self.a),lineage_factory=lineage_factory)\n\n    def test_foundation(self): self.assertTrue(verify_umd_126_impact_coverage_registry())\n    def test_family_query(self):\n        self.assertEqual(self.r.observations_for_family("asset=bitcoin"),("a"*64,"b"*64))\n    def test_venue_query(self):\n        self.assertEqual(self.r.observations_for_venue("kalshi"),("a"*64,"c"*64))\n    def test_cross_venue_query(self):\n        self.assertEqual(self.r.observations_for_cross_venue_market("m1"),("a"*64,))\n    def test_market_query(self):\n        self.assertEqual(self.r.observations_for_market("m3"),("c"*64,))\n    def test_family_venue_intersection(self):\n        self.assertEqual(self.r.observations_for_family_and_venue("asset=bitcoin","kalshi"),("a"*64,))\n    def test_unknown(self):\n        self.assertEqual(self.r.observations_for_venue("missing"),())\n    def test_deterministic(self):\n        x=ImpactCoverageRegistryBuilder().build((self.a,self.b,self.c),lineage_factory=lineage_factory)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_bad_matrix(self):\n        with self.assertRaises(TypeError):\n            ImpactCoverageRegistryBuilder().build((object(),),lineage_factory=lineage_factory)\n    def test_side_effects(self):\n        m=build_umd_126_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-126 CERTIFICATION TEST");print(" IMPACT COVERAGE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD126))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_126_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Coverage queries by family, venue, canonical market, and cross-venue market certified")\n    print("[PASS] Family-plus-venue intersection queries certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-126 CERTIFIED")\n'
UPSTREAM_MODULE='umd_125_impact_coverage_matrix'
UPSTREAM_VERIFIER='verify_umd_125_impact_coverage_matrix'
EXPORTED_NAMES=('UMD_126_REVISION', 'ImpactCoverageRegistry', 'ImpactCoverageRegistryBuilder', 'build_umd_126_certification_manifest', 'verify_umd_126_impact_coverage_registry')

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
    marker="# UMD-126 exports"
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
            raise RuntimeError("UMD-126 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-126 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-126 INSTALLER")
    print(" IMPACT COVERAGE REGISTRY")
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
        print("[ROLLBACK] UMD-126 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-126',
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
    print("[DONE] UMD-126 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
