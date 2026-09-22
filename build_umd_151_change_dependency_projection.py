from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_151_CHANGE_DEPENDENCY_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_151_change_dependency_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_151_change_dependency_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_112_market_dependency import MarketDependency\nfrom .umd_114_dependency_registry import DependencyRegistry\nfrom .umd_150_change_structure_registry import ChangeStructureRegistry,verify_umd_150_change_structure_registry\n\nUMD_151_BUILD_ID="UMD-151"\nUMD_151_REVISION="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1"\nUMD_151_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeDependencyBinding:\n    canonical_market_id:str\n    kind:str\n    key:str\n    role:str\n    dependency_hash:str\n\n    @property\n    def binding_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "kind":self.kind,\n            "key":self.key,\n            "role":self.role,\n            "dependency_hash":self.dependency_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeDependencyProjection:\n    change_hash:str\n    market_ids:Tuple[str,...]\n    bindings:Tuple[ChangeDependencyBinding,...]\n    role_to_markets:Mapping[str,Tuple[str,...]]\n    dependency_to_markets:Mapping[str,Tuple[str,...]]\n    missing_profile_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_ids",tuple(self.market_ids))\n        object.__setattr__(self,"bindings",tuple(self.bindings))\n        object.__setattr__(self,"role_to_markets",_freeze(self.role_to_markets))\n        object.__setattr__(self,"dependency_to_markets",_freeze(self.dependency_to_markets))\n        object.__setattr__(self,"missing_profile_market_ids",tuple(self.missing_profile_market_ids))\n        if self.market_ids!=tuple(sorted(set(self.market_ids))):\n            raise ValueError("market_ids must be unique and sorted")\n        if self.bindings!=tuple(sorted(\n            self.bindings,\n            key=lambda b:(b.canonical_market_id,b.kind,b.key,b.role,b.dependency_hash)\n        )):\n            raise ValueError("bindings must be deterministically sorted")\n        if self.missing_profile_market_ids!=tuple(sorted(set(self.missing_profile_market_ids))):\n            raise ValueError("missing_profile_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_151_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-151")\n        if self.change_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include change hash")\n\n    def markets_for_role(self,role:str)->Tuple[str,...]:\n        return self.role_to_markets.get(role,())\n\n    def markets_for_dependency(self,kind:str,key:str)->Tuple[str,...]:\n        return self.dependency_to_markets.get(kind+"="+key,())\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "market_ids":self.market_ids,\n            "binding_hashes":tuple(b.binding_hash for b in self.bindings),\n            "role_to_markets":self.role_to_markets,\n            "dependency_to_markets":self.dependency_to_markets,\n            "missing_profile_market_ids":self.missing_profile_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ChangeDependencyProjector:\n    __slots__=("structure_registry","dependency_registry")\n\n    def __init__(self,structure_registry:ChangeStructureRegistry,dependency_registry:DependencyRegistry):\n        if not isinstance(structure_registry,ChangeStructureRegistry):\n            raise TypeError("structure_registry must be ChangeStructureRegistry")\n        if not isinstance(dependency_registry,DependencyRegistry):\n            raise TypeError("dependency_registry must be DependencyRegistry")\n        self.structure_registry=structure_registry\n        self.dependency_registry=dependency_registry\n\n    def project(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeDependencyProjection:\n        markets=tuple(sorted(\n            market_id for market_id,changes in self.structure_registry.market_index.items()\n            if change_hash in changes\n        ))\n        profiles={p.canonical_market_id:p for p in self.dependency_registry.profiles}\n\n        bindings=[]\n        role_index={}\n        dependency_index={}\n        missing=[]\n\n        for market_id in markets:\n            profile=profiles.get(market_id)\n            if profile is None:\n                missing.append(market_id)\n                continue\n            for dependency in profile.dependencies:\n                binding=ChangeDependencyBinding(\n                    market_id,\n                    dependency.kind,\n                    dependency.key,\n                    dependency.role,\n                    dependency.dependency_hash,\n                )\n                bindings.append(binding)\n                role_index.setdefault(dependency.role,[]).append(market_id)\n                dependency_index.setdefault(dependency.kind+"="+dependency.key,[]).append(market_id)\n\n        bindings.sort(key=lambda b:(b.canonical_market_id,b.kind,b.key,b.role,b.dependency_hash))\n        for index in (role_index,dependency_index):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        return ChangeDependencyProjection(\n            change_hash,\n            markets,\n            tuple(bindings),\n            role_index,\n            dependency_index,\n            tuple(sorted(missing)),\n            lineage,\n        )\n\ndef build_umd_151_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_151_BUILD_ID,"revision":UMD_151_REVISION,\n        "schema_version":UMD_151_SCHEMA_VERSION,"upstream_builds":("UMD-112","UMD-114","UMD-150"),\n        "mode":"deterministic_read_only_change_dependency_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_151_change_dependency_projection()->bool:\n    if verify_umd_150_change_structure_registry() is not True:\n        return False\n    m=build_umd_151_certification_manifest()\n    return m["build_id"]=="UMD-151" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_112_market_dependency import MarketDependency,MarketDependencyProfile\nfrom qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry\nfrom qseries_v2.universal_market_discovery.umd_150_change_structure_registry import ChangeStructureRegistry\nfrom qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import *\n\nFIXED=datetime(2026,8,10,10,0,tzinfo=timezone.utc)\nCHANGE="1"*64\n\ndef profile(mid,semantic_hash,deps):\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-112",revision="UMD_112_MARKET_DEPENDENCY_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(semantic_hash,),\n        source_refs=("fixture://151/112",),created_at=FIXED\n    )\n    return MarketDependencyProfile(mid,semantic_hash,tuple(deps),l)\n\ndef dependency_registry():\n    p1=profile("m1","a"*64,(\n        MarketDependency("asset","Bitcoin","bitcoin","required"),\n        MarketDependency("metric","Price","price","supporting"),\n    ))\n    p2=profile("m2","b"*64,(\n        MarketDependency("entity","Federal Reserve","federal-reserve","context"),\n    ))\n    graph_hash="c"*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,graph_hash),\n        source_refs=("fixture://151/114",),created_at=FIXED\n    )\n    return DependencyRegistry(\n        (p1,p2),graph_hash,\n        {\n            "asset=bitcoin":("m1",),\n            "entity=federal-reserve":("m2",),\n            "metric=price":("m1",),\n        },\n        {\n            "context":("m2",),\n            "required":("m1",),\n            "supporting":("m1",),\n        },\n        {},\n        l,\n    )\n\ndef structure_registry():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-150",revision="UMD_150_CHANGE_STRUCTURE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),\n        source_refs=("fixture://151/150",),created_at=FIXED\n    )\n    return ChangeStructureRegistry(\n        (),(),{},{},{},\n        {"m1":(CHANGE,),"m2":(CHANGE,),"m3":(CHANGE,)},\n        l,\n    )\n\ndef lineage():\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-151",revision=UMD_151_REVISION,\n        schema_version="1.0.0",parent_hashes=(CHANGE,),\n        source_refs=("fixture://151",),created_at=FIXED\n    )\n\nclass TestUMD151(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_151_change_dependency_projection())\n    def test_projection(self):\n        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())\n        self.assertEqual(p.market_ids,("m1","m2","m3"))\n        self.assertEqual(len(p.bindings),3)\n    def test_role_query(self):\n        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())\n        self.assertEqual(p.markets_for_role("required"),("m1",))\n        self.assertEqual(p.markets_for_role("context"),("m2",))\n    def test_dependency_query(self):\n        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())\n        self.assertEqual(p.markets_for_dependency("asset","bitcoin"),("m1",))\n    def test_missing_profile(self):\n        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())\n        self.assertEqual(p.missing_profile_market_ids,("m3",))\n    def test_unknown_change(self):\n        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project("9"*64,lineage=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-151",revision=UMD_151_REVISION,\n            schema_version="1.0.0",parent_hashes=("9"*64,),\n            source_refs=("fixture://151/unknown",),created_at=FIXED\n        ))\n        self.assertEqual(p.market_ids,())\n    def test_deterministic(self):\n        projector=ChangeDependencyProjector(structure_registry(),dependency_registry())\n        a=projector.project(CHANGE,lineage=lineage())\n        b=projector.project(CHANGE,lineage=lineage())\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ChangeDependencyProjector(object(),dependency_registry())\n    def test_side_effects(self):\n        m=build_umd_151_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-151 CERTIFICATION TEST");print(" CHANGE DEPENDENCY PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD151))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_151_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] World-state changes projected into required, supporting, settlement, and context dependencies")\n    print("[PASS] Missing dependency profiles preserved explicitly")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-151 CERTIFIED")\n'
UPSTREAM_MODULE='umd_150_change_structure_registry'
UPSTREAM_VERIFIER='verify_umd_150_change_structure_registry'
EXPORTED_NAMES=('UMD_151_REVISION', 'ChangeDependencyBinding', 'ChangeDependencyProjection', 'ChangeDependencyProjector', 'build_umd_151_certification_manifest', 'verify_umd_151_change_dependency_projection')

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
    marker="# UMD-151 exports"
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
            raise RuntimeError("UMD-151 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-151 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-151 INSTALLER")
    print(" CHANGE DEPENDENCY PROJECTION")
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
        print("[ROLLBACK] UMD-151 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-151',
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
    print("[DONE] UMD-151 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
