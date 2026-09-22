from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_147_observation_change_impact_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_147_observation_change_impact_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_146_observation_change_impact_surface import ObservationChangeImpactSurface,verify_umd_146_observation_change_impact_surface\n\nUMD_147_BUILD_ID="UMD-147"\nUMD_147_REVISION="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1"\nUMD_147_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationChangeImpactRegistry:\n    surfaces:Tuple[ObservationChangeImpactSurface,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    family_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"surfaces",tuple(self.surfaces))\n        for name in ("market_index","family_index","venue_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.surfaces!=tuple(sorted(self.surfaces,key=lambda s:s.surface_hash)):\n            raise ValueError("surfaces must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_147_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-147")\n        required={s.surface_hash for s in self.surfaces}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every surface hash")\n\n    def change_hashes_for_market(self,key:str)->Tuple[str,...]:\n        return self.market_index.get(key,())\n    def change_hashes_for_family(self,key:str)->Tuple[str,...]:\n        return self.family_index.get(key,())\n    def change_hashes_for_venue(self,key:str)->Tuple[str,...]:\n        return self.venue_index.get(key,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "surface_hashes":tuple(s.surface_hash for s in self.surfaces),\n            "market_index":self.market_index,\n            "family_index":self.family_index,\n            "venue_index":self.venue_index,\n            "lineage":self.lineage,\n        })\n\nclass ObservationChangeImpactRegistryBuilder:\n    __slots__=()\n\n    def build(self,surfaces:Iterable[ObservationChangeImpactSurface],*,lineage_factory)->ObservationChangeImpactRegistry:\n        values=tuple(surfaces)\n        if any(not isinstance(s,ObservationChangeImpactSurface) for s in values):\n            raise TypeError("surfaces must contain ObservationChangeImpactSurface")\n        values=tuple(sorted(values,key=lambda s:s.surface_hash))\n\n        market={}; family={}; venue={}\n\n        for surface in values:\n            for key,changes in surface.market_to_changes.items():\n                market.setdefault(key,[]).extend(changes)\n            for key,changes in surface.family_to_changes.items():\n                family.setdefault(key,[]).extend(changes)\n            for key,changes in surface.venue_to_changes.items():\n                venue.setdefault(key,[]).extend(changes)\n\n        for index in (market,family,venue):\n            for key,changes in index.items():\n                index[key]=tuple(sorted(set(changes)))\n\n        lineage=lineage_factory(tuple(s.surface_hash for s in values))\n        return ObservationChangeImpactRegistry(values,market,family,venue,lineage)\n\ndef build_umd_147_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_147_BUILD_ID,"revision":UMD_147_REVISION,\n        "schema_version":UMD_147_SCHEMA_VERSION,"upstream_builds":("UMD-146",),\n        "mode":"deterministic_read_only_observation_change_impact_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_147_observation_change_impact_registry()->bool:\n    if verify_umd_146_observation_change_impact_surface() is not True:\n        return False\n    m=build_umd_147_certification_manifest()\n    return m["build_id"]=="UMD-147" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_146_observation_change_impact_surface import ObservationChangeImpactSurface\nfrom qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import *\n\nFIXED=datetime(2026,8,10,8,20,tzinfo=timezone.utc)\n\ndef surface(seed,market,family,venue,change):\n    routing_hash=seed*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-146",revision="UMD_146_OBSERVATION_CHANGE_IMPACT_SURFACE_V1",\n        schema_version="1.0.0",parent_hashes=(routing_hash,),source_refs=("fixture://147/146",),created_at=FIXED)\n    return ObservationChangeImpactSurface(\n        routing_hash,\n        {market:(change,)},\n        {family:(change,)},\n        {venue:(change,)},\n        {change:(market,)},\n        l,\n    )\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision=UMD_147_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://147",),created_at=FIXED)\n\nclass TestUMD147(unittest.TestCase):\n    def setUp(self):\n        self.a=surface("a","m1","f1","kalshi","1"*64)\n        self.b=surface("b","m1","f2","polymarket","2"*64)\n        self.r=ObservationChangeImpactRegistryBuilder().build((self.b,self.a),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_147_observation_change_impact_registry())\n    def test_market_query(self):\n        self.assertEqual(self.r.change_hashes_for_market("m1"),("1"*64,"2"*64))\n    def test_family_query(self):\n        self.assertEqual(self.r.change_hashes_for_family("f2"),("2"*64,))\n    def test_venue_query(self):\n        self.assertEqual(self.r.change_hashes_for_venue("kalshi"),("1"*64,))\n    def test_unknown(self):\n        self.assertEqual(self.r.change_hashes_for_market("missing"),())\n    def test_deterministic(self):\n        x=ObservationChangeImpactRegistryBuilder().build((self.a,self.b),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ObservationChangeImpactRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(x.surfaces,())\n    def test_bad_surface(self):\n        with self.assertRaises(TypeError):\n            ObservationChangeImpactRegistryBuilder().build((object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_147_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-147 CERTIFICATION TEST");print(" OBSERVATION CHANGE IMPACT REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD147))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_147_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] World-state change impact registry across markets, families, and venues certified")\n    print("[PASS] Cross-surface reverse change queries certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-147 CERTIFIED")\n'
UPSTREAM_MODULE='umd_146_observation_change_impact_surface'
UPSTREAM_VERIFIER='verify_umd_146_observation_change_impact_surface'
EXPORTED_NAMES=('UMD_147_REVISION', 'ObservationChangeImpactRegistry', 'ObservationChangeImpactRegistryBuilder', 'build_umd_147_certification_manifest', 'verify_umd_147_observation_change_impact_registry')

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
    marker="# UMD-147 exports"
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
            raise RuntimeError("UMD-147 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-147 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-147 INSTALLER")
    print(" OBSERVATION CHANGE IMPACT REGISTRY")
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
        print("[ROLLBACK] UMD-147 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-147',
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
    print("[DONE] UMD-147 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
