from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_153_CHANGE_DEPENDENCY_CONTEXT_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_153_change_dependency_context_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_153_change_dependency_context_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_151_change_dependency_projection import ChangeDependencyProjection\nfrom .umd_152_change_constraint_projection import ChangeConstraintProjection,verify_umd_152_change_constraint_projection\n\nUMD_153_BUILD_ID="UMD-153"\nUMD_153_REVISION="UMD_153_CHANGE_DEPENDENCY_CONTEXT_REGISTRY_V1"\nUMD_153_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeDependencyContextRegistry:\n    dependency_projections:Tuple[ChangeDependencyProjection,...]\n    constraint_projections:Tuple[ChangeConstraintProjection,...]\n    dependency_index:Mapping[str,Tuple[str,...]]\n    role_index:Mapping[str,Tuple[str,...]]\n    constraint_type_index:Mapping[str,Tuple[str,...]]\n    market_index:Mapping[str,Tuple[str,...]]\n    boundary_market_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"dependency_projections",tuple(self.dependency_projections))\n        object.__setattr__(self,"constraint_projections",tuple(self.constraint_projections))\n        for name in ("dependency_index","role_index","constraint_type_index","market_index","boundary_market_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.dependency_projections!=tuple(sorted(\n            self.dependency_projections,key=lambda p:(p.change_hash,p.projection_hash)\n        )):\n            raise ValueError("dependency projections must be deterministically sorted")\n        if self.constraint_projections!=tuple(sorted(\n            self.constraint_projections,key=lambda p:(p.change_hash,p.projection_hash)\n        )):\n            raise ValueError("constraint projections must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_153_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-153")\n        required={p.projection_hash for p in self.dependency_projections}|{\n            p.projection_hash for p in self.constraint_projections\n        }\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every dependency and constraint projection hash")\n\n    def changes_for_dependency(self,kind:str,key:str)->Tuple[str,...]:\n        return self.dependency_index.get(kind+"="+key,())\n\n    def changes_for_role(self,role:str)->Tuple[str,...]:\n        return self.role_index.get(role,())\n\n    def changes_for_constraint_type(self,constraint_type:str)->Tuple[str,...]:\n        return self.constraint_type_index.get(constraint_type,())\n\n    def changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def boundary_changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.boundary_market_index.get(market_id,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "dependency_projection_hashes":tuple(p.projection_hash for p in self.dependency_projections),\n            "constraint_projection_hashes":tuple(p.projection_hash for p in self.constraint_projections),\n            "dependency_index":self.dependency_index,\n            "role_index":self.role_index,\n            "constraint_type_index":self.constraint_type_index,\n            "market_index":self.market_index,\n            "boundary_market_index":self.boundary_market_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeDependencyContextRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        dependency_projections:Iterable[ChangeDependencyProjection],\n        constraint_projections:Iterable[ChangeConstraintProjection],\n        *,\n        lineage_factory,\n    )->ChangeDependencyContextRegistry:\n        deps=tuple(dependency_projections)\n        cons=tuple(constraint_projections)\n        if any(not isinstance(p,ChangeDependencyProjection) for p in deps):\n            raise TypeError("dependency_projections must contain ChangeDependencyProjection")\n        if any(not isinstance(p,ChangeConstraintProjection) for p in cons):\n            raise TypeError("constraint_projections must contain ChangeConstraintProjection")\n\n        deps=tuple(sorted(deps,key=lambda p:(p.change_hash,p.projection_hash)))\n        cons=tuple(sorted(cons,key=lambda p:(p.change_hash,p.projection_hash)))\n\n        dep_index={}\n        role_index={}\n        constraint_index={}\n        market_index={}\n        boundary_index={}\n\n        for p in deps:\n            for binding in p.bindings:\n                dep_index.setdefault(binding.kind+"="+binding.key,[]).append(p.change_hash)\n                role_index.setdefault(binding.role,[]).append(p.change_hash)\n                market_index.setdefault(binding.canonical_market_id,[]).append(p.change_hash)\n            for market_id in p.market_ids:\n                market_index.setdefault(market_id,[]).append(p.change_hash)\n\n        for p in cons:\n            for binding in p.constraints:\n                constraint_index.setdefault(binding.constraint_type,[]).append(p.change_hash)\n                market_index.setdefault(binding.source_market_id,[]).append(p.change_hash)\n                market_index.setdefault(binding.target_market_id,[]).append(p.change_hash)\n                if binding.boundary:\n                    impacted_market = (\n                        binding.source_market_id if binding.source_impacted else binding.target_market_id\n                    )\n                    boundary_index.setdefault(impacted_market,[]).append(p.change_hash)\n\n        for index in (dep_index,role_index,constraint_index,market_index,boundary_index):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        parents=tuple(p.projection_hash for p in deps)+tuple(p.projection_hash for p in cons)\n        lineage=lineage_factory(parents)\n        return ChangeDependencyContextRegistry(\n            deps,cons,dep_index,role_index,constraint_index,market_index,boundary_index,lineage\n        )\n\ndef build_umd_153_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_153_BUILD_ID,"revision":UMD_153_REVISION,\n        "schema_version":UMD_153_SCHEMA_VERSION,"upstream_builds":("UMD-151","UMD-152"),\n        "mode":"deterministic_read_only_change_dependency_context_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_153_change_dependency_context_registry()->bool:\n    if verify_umd_152_change_constraint_projection() is not True:\n        return False\n    m=build_umd_153_certification_manifest()\n    return m["build_id"]=="UMD-153" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyBinding,ChangeDependencyProjection\nfrom qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection\nfrom qseries_v2.universal_market_discovery.umd_153_change_dependency_context_registry import *\n\nFIXED=datetime(2026,8,10,10,20,tzinfo=timezone.utc)\n\ndef dep(change,market,kind,key,role,seed):\n    binding=ChangeDependencyBinding(market,kind,key,role,seed*64)\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://153/151",),created_at=FIXED\n    )\n    return ChangeDependencyProjection(\n        change,(market,),(binding,),\n        {role:(market,)},{kind+"="+key:(market,)},(),l\n    )\n\ndef con(change,source,target,ctype,boundary,seed):\n    binding=ChangeConstraintBinding(\n        source,target,ctype,"basis:"+seed,\n        True,not boundary,seed*64\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://153/152",),created_at=FIXED\n    )\n    internal=() if boundary else (binding.constraint_hash,)\n    boundary_hashes=(binding.constraint_hash,) if boundary else ()\n    impacted=(source,) if boundary else tuple(sorted((source,target)))\n    return ChangeConstraintProjection(\n        change,impacted,(binding,),internal,boundary_hashes,l\n    )\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-153",revision=UMD_153_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://153",),created_at=FIXED\n    )\n\nclass TestUMD153(unittest.TestCase):\n    def setUp(self):\n        self.c1="1"*64; self.c2="2"*64\n        self.d1=dep(self.c1,"m1","asset","bitcoin","required","a")\n        self.d2=dep(self.c2,"m2","entity","federal-reserve","context","b")\n        self.k1=con(self.c1,"m1","m3","implies",True,"c")\n        self.k2=con(self.c2,"m2","m4","mutually_exclusive",False,"d")\n        self.r=ChangeDependencyContextRegistryBuilder().build(\n            (self.d2,self.d1),(self.k2,self.k1),lineage_factory=lf\n        )\n\n    def test_foundation(self): self.assertTrue(verify_umd_153_change_dependency_context_registry())\n    def test_dependency_query(self):\n        self.assertEqual(self.r.changes_for_dependency("asset","bitcoin"),(self.c1,))\n    def test_role_query(self):\n        self.assertEqual(self.r.changes_for_role("context"),(self.c2,))\n    def test_constraint_query(self):\n        self.assertEqual(self.r.changes_for_constraint_type("implies"),(self.c1,))\n    def test_market_query(self):\n        self.assertEqual(self.r.changes_for_market("m1"),(self.c1,))\n        self.assertEqual(self.r.changes_for_market("m4"),(self.c2,))\n    def test_boundary_query(self):\n        self.assertEqual(self.r.boundary_changes_for_market("m1"),(self.c1,))\n        self.assertEqual(self.r.boundary_changes_for_market("m2"),())\n    def test_deterministic(self):\n        x=ChangeDependencyContextRegistryBuilder().build(\n            (self.d1,self.d2),(self.k1,self.k2),lineage_factory=lf\n        )\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ChangeDependencyContextRegistryBuilder().build((),(),lineage_factory=lf)\n        self.assertEqual(x.dependency_projections,())\n        self.assertEqual(x.constraint_projections,())\n    def test_bad_dependency_projection(self):\n        with self.assertRaises(TypeError):\n            ChangeDependencyContextRegistryBuilder().build((object(),),(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_153_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-153 CERTIFICATION TEST");print(" CHANGE DEPENDENCY CONTEXT REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD153))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_153_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Change dependency, role, constraint, market, and boundary-context queries certified")\n    print("[PASS] World-state changes now retain deterministic dependency and constraint context")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-153 CERTIFIED")\n'
UPSTREAM_MODULE='umd_152_change_constraint_projection'
UPSTREAM_VERIFIER='verify_umd_152_change_constraint_projection'
EXPORTED_NAMES=('UMD_153_REVISION', 'ChangeDependencyContextRegistry', 'ChangeDependencyContextRegistryBuilder', 'build_umd_153_certification_manifest', 'verify_umd_153_change_dependency_context_registry')

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
    marker="# UMD-153 exports"
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
            raise RuntimeError("UMD-153 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-153 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-153 INSTALLER")
    print(" CHANGE DEPENDENCY CONTEXT REGISTRY")
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
        print("[ROLLBACK] UMD-153 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-153',
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
    print("[DONE] UMD-153 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
