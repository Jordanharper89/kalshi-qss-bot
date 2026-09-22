from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_170_CONVERGENCE_MARKET_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_170_convergence_market_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_170_convergence_market_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_169_convergence_market_profile import ConvergenceMarketProfile,ConvergenceMarketProfileSet,verify_umd_169_convergence_market_profile\n\nUMD_170_BUILD_ID="UMD-170"\nUMD_170_REVISION="UMD_170_CONVERGENCE_MARKET_REGISTRY_V1"\nUMD_170_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceMarketRegistry:\n    profiles:Tuple[ConvergenceMarketProfile,...]\n    change_type_index:Mapping[str,Tuple[str,...]]\n    ladder_index:Mapping[str,Tuple[str,...]]\n    partition_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    dependency_index:Mapping[str,Tuple[str,...]]\n    role_index:Mapping[str,Tuple[str,...]]\n    constraint_index:Mapping[str,Tuple[str,...]]\n    relation_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"profiles",tuple(self.profiles))\n        for name in (\n            "change_type_index","ladder_index","partition_index","venue_index",\n            "dependency_index","role_index","constraint_index","relation_index"\n        ):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.profiles!=tuple(sorted(self.profiles,key=lambda p:(p.canonical_market_id,p.profile_hash))):\n            raise ValueError("profiles must be deterministically sorted")\n        if len({p.canonical_market_id for p in self.profiles})!=len(self.profiles):\n            raise ValueError("registry profiles must have unique market ids")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_170_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-170")\n        required={p.profile_hash for p in self.profiles}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every market profile hash")\n\n    def get(self,market_id:str)->ConvergenceMarketProfile|None:\n        for profile in self.profiles:\n            if profile.canonical_market_id==market_id:\n                return profile\n        return None\n\n    def markets_for_change_type(self,key:str)->Tuple[str,...]: return self.change_type_index.get(key,())\n    def markets_for_ladder(self,key:str)->Tuple[str,...]: return self.ladder_index.get(key,())\n    def markets_for_partition(self,key:str)->Tuple[str,...]: return self.partition_index.get(key,())\n    def markets_for_venue(self,key:str)->Tuple[str,...]: return self.venue_index.get(key,())\n    def markets_for_dependency(self,key:str)->Tuple[str,...]: return self.dependency_index.get(key,())\n    def markets_for_role(self,key:str)->Tuple[str,...]: return self.role_index.get(key,())\n    def markets_for_constraint(self,key:str)->Tuple[str,...]: return self.constraint_index.get(key,())\n    def markets_for_relation(self,key:str)->Tuple[str,...]: return self.relation_index.get(key,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "profile_hashes":tuple(p.profile_hash for p in self.profiles),\n            "change_type_index":self.change_type_index,\n            "ladder_index":self.ladder_index,\n            "partition_index":self.partition_index,\n            "venue_index":self.venue_index,\n            "dependency_index":self.dependency_index,\n            "role_index":self.role_index,\n            "constraint_index":self.constraint_index,\n            "relation_index":self.relation_index,\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceMarketRegistryBuilder:\n    __slots__=()\n\n    def build(self,profile_set:ConvergenceMarketProfileSet,*,lineage_factory)->ConvergenceMarketRegistry:\n        if not isinstance(profile_set,ConvergenceMarketProfileSet):\n            raise TypeError("profile_set must be ConvergenceMarketProfileSet")\n\n        indexes=[{} for _ in range(8)]\n        attrs=(\n            "change_types","ladder_hashes","partition_hashes","venue_keys",\n            "dependency_keys","dependency_roles","constraint_types","relation_types"\n        )\n        for profile in profile_set.profiles:\n            for index,attr in zip(indexes,attrs):\n                for key in getattr(profile,attr):\n                    index.setdefault(key,[]).append(profile.canonical_market_id)\n\n        for index in indexes:\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        lineage=lineage_factory(tuple(p.profile_hash for p in profile_set.profiles))\n        return ConvergenceMarketRegistry(profile_set.profiles,*indexes,lineage)\n\ndef build_umd_170_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_170_BUILD_ID,"revision":UMD_170_REVISION,\n        "schema_version":UMD_170_SCHEMA_VERSION,"upstream_builds":("UMD-169",),\n        "mode":"deterministic_read_only_convergence_market_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_170_convergence_market_registry()->bool:\n    if verify_umd_169_convergence_market_profile() is not True:\n        return False\n    m=build_umd_170_certification_manifest()\n    return m["build_id"]=="UMD-170" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import ConvergenceMarketProfile,ConvergenceMarketProfileSet\nfrom qseries_v2.universal_market_discovery.umd_170_convergence_market_registry import *\n\nFIXED=datetime(2026,8,10,16,10,tzinfo=timezone.utc)\nL="a"*64;P="b"*64\n\ndef profiles():\n    p1=ConvergenceMarketProfile(\n        "m1",("convergence-added",),(L,),(),("kalshi","polymarket"),\n        ("asset=bitcoin",),("required",),("implies",),("impacted",)\n    )\n    p2=ConvergenceMarketProfile(\n        "m2",("convergence-composition-changed",),(L,),(P,),("kalshi",),\n        ("metric=cpi",),("supporting",),("threshold_monotonic",),("boundary",)\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-169",revision="UMD_169_CONVERGENCE_MARKET_PROFILE_V1",\n        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash),\n        source_refs=("fixture://170/169",),created_at=FIXED\n    )\n    return ConvergenceMarketProfileSet((p1,p2),l)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-170",revision=UMD_170_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://170",),created_at=FIXED\n    )\n\nclass TestUMD170(unittest.TestCase):\n    def setUp(self):\n        self.r=ConvergenceMarketRegistryBuilder().build(profiles(),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_170_convergence_market_registry())\n    def test_get(self):\n        self.assertEqual(self.r.get("m1").dependency_keys,("asset=bitcoin",))\n        self.assertIsNone(self.r.get("missing"))\n    def test_change_type_query(self):\n        self.assertEqual(self.r.markets_for_change_type("convergence-added"),("m1",))\n    def test_topology_queries(self):\n        self.assertEqual(self.r.markets_for_ladder(L),("m1","m2"))\n        self.assertEqual(self.r.markets_for_partition(P),("m2",))\n    def test_venue_query(self):\n        self.assertEqual(self.r.markets_for_venue("kalshi"),("m1","m2"))\n        self.assertEqual(self.r.markets_for_venue("polymarket"),("m1",))\n    def test_context_queries(self):\n        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))\n        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))\n        self.assertEqual(self.r.markets_for_constraint("implies"),("m1",))\n        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))\n    def test_deterministic(self):\n        x=ConvergenceMarketRegistryBuilder().build(profiles(),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_bad_profile_set(self):\n        with self.assertRaises(TypeError):\n            ConvergenceMarketRegistryBuilder().build(object(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_170_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-170 CERTIFICATION TEST");print(" CONVERGENCE MARKET REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD170))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_170_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical convergence market registry and reverse structural queries certified")\n    print("[PASS] Market profiles remain deterministic, read-only, and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-170 CERTIFIED")\n'
UPSTREAM_MODULE='umd_169_convergence_market_profile'
UPSTREAM_VERIFIER='verify_umd_169_convergence_market_profile'
EXPORTED_NAMES=('UMD_170_REVISION', 'ConvergenceMarketRegistry', 'ConvergenceMarketRegistryBuilder', 'build_umd_170_certification_manifest', 'verify_umd_170_convergence_market_registry')

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
    marker="# UMD-170 exports"
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
            raise RuntimeError("UMD-170 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-170 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-170 INSTALLER")
    print(" CONVERGENCE MARKET REGISTRY")
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
        print("[ROLLBACK] UMD-170 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-170',
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
    print("[DONE] UMD-170 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
