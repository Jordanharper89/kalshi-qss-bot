from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_152_CHANGE_CONSTRAINT_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_152_change_constraint_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_152_change_constraint_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_113_market_constraints import MarketConstraintGraph\nfrom .umd_151_change_dependency_projection import ChangeDependencyProjection,verify_umd_151_change_dependency_projection\n\nUMD_152_BUILD_ID="UMD-152"\nUMD_152_REVISION="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1"\nUMD_152_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ChangeConstraintBinding:\n    source_market_id:str\n    target_market_id:str\n    constraint_type:str\n    basis:str\n    source_impacted:bool\n    target_impacted:bool\n    constraint_hash:str\n\n    @property\n    def boundary(self)->bool:\n        return self.source_impacted != self.target_impacted\n\n    @property\n    def internal(self)->bool:\n        return self.source_impacted and self.target_impacted\n\n    @property\n    def binding_hash(self)->str:\n        return deterministic_sha256({\n            "source_market_id":self.source_market_id,\n            "target_market_id":self.target_market_id,\n            "constraint_type":self.constraint_type,\n            "basis":self.basis,\n            "source_impacted":self.source_impacted,\n            "target_impacted":self.target_impacted,\n            "constraint_hash":self.constraint_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeConstraintProjection:\n    change_hash:str\n    impacted_market_ids:Tuple[str,...]\n    constraints:Tuple[ChangeConstraintBinding,...]\n    internal_constraint_hashes:Tuple[str,...]\n    boundary_constraint_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in ("impacted_market_ids","internal_constraint_hashes","boundary_constraint_hashes"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        object.__setattr__(self,"constraints",tuple(self.constraints))\n        if self.constraints!=tuple(sorted(\n            self.constraints,\n            key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash)\n        )):\n            raise ValueError("constraints must be deterministically sorted")\n        if set(self.internal_constraint_hashes)&set(self.boundary_constraint_hashes):\n            raise ValueError("constraint cannot be both internal and boundary")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_152_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-152")\n        if self.change_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include change hash")\n\n    def constraints_of_type(self,constraint_type:str)->Tuple[ChangeConstraintBinding,...]:\n        return tuple(c for c in self.constraints if c.constraint_type==constraint_type)\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "impacted_market_ids":self.impacted_market_ids,\n            "constraint_binding_hashes":tuple(c.binding_hash for c in self.constraints),\n            "internal_constraint_hashes":self.internal_constraint_hashes,\n            "boundary_constraint_hashes":self.boundary_constraint_hashes,\n            "lineage":self.lineage,\n        })\n\nclass ChangeConstraintProjector:\n    __slots__=("graph",)\n\n    def __init__(self,graph:MarketConstraintGraph):\n        if not isinstance(graph,MarketConstraintGraph):\n            raise TypeError("graph must be MarketConstraintGraph")\n        self.graph=graph\n\n    def project(\n        self,\n        dependency_projection:ChangeDependencyProjection,\n        *,\n        lineage:ImmutableLineage,\n    )->ChangeConstraintProjection:\n        if not isinstance(dependency_projection,ChangeDependencyProjection):\n            raise TypeError("dependency_projection must be ChangeDependencyProjection")\n\n        impacted=set(dependency_projection.market_ids)\n        bindings=[]\n        internal=[]\n        boundary=[]\n\n        for constraint in self.graph.constraints:\n            source_hit=constraint.source_market_id in impacted\n            target_hit=constraint.target_market_id in impacted\n            if not source_hit and not target_hit:\n                continue\n            binding=ChangeConstraintBinding(\n                constraint.source_market_id,\n                constraint.target_market_id,\n                constraint.constraint_type,\n                constraint.basis,\n                source_hit,\n                target_hit,\n                constraint.constraint_hash,\n            )\n            bindings.append(binding)\n            if binding.internal:\n                internal.append(constraint.constraint_hash)\n            elif binding.boundary:\n                boundary.append(constraint.constraint_hash)\n\n        bindings.sort(key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash))\n        return ChangeConstraintProjection(\n            dependency_projection.change_hash,\n            dependency_projection.market_ids,\n            tuple(bindings),\n            tuple(sorted(set(internal))),\n            tuple(sorted(set(boundary))),\n            lineage,\n        )\n\ndef build_umd_152_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_152_BUILD_ID,"revision":UMD_152_REVISION,\n        "schema_version":UMD_152_SCHEMA_VERSION,"upstream_builds":("UMD-113","UMD-151"),\n        "mode":"deterministic_read_only_change_constraint_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_152_change_constraint_projection()->bool:\n    if verify_umd_151_change_dependency_projection() is not True:\n        return False\n    m=build_umd_152_certification_manifest()\n    return m["build_id"]=="UMD-152" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_113_market_constraints import MarketConstraint,MarketConstraintGraph\nfrom qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyProjection\nfrom qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import *\n\nFIXED=datetime(2026,8,10,10,10,tzinfo=timezone.utc)\nCHANGE="1"*64\n\ndef dependency_projection():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(CHANGE,),\n        source_refs=("fixture://152/151",),created_at=FIXED\n    )\n    return ChangeDependencyProjection(CHANGE,("m1","m2"),(),{},{},(),l)\n\ndef graph():\n    constraints=(\n        MarketConstraint("m1","m2","implies","basis:internal"),\n        MarketConstraint("m2","m3","threshold_monotonic","basis:boundary"),\n        MarketConstraint("m3","m4","mutually_exclusive","basis:outside"),\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-113",revision="UMD_113_MARKET_CONSTRAINT_GRAPH_V1",\n        schema_version="1.0.0",parent_hashes=(),\n        source_refs=("fixture://152/113",),created_at=FIXED\n    )\n    return MarketConstraintGraph(("m1","m2","m3","m4"),constraints,(),l)\n\ndef lineage():\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-152",revision=UMD_152_REVISION,\n        schema_version="1.0.0",parent_hashes=(CHANGE,),\n        source_refs=("fixture://152",),created_at=FIXED\n    )\n\nclass TestUMD152(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_152_change_constraint_projection())\n    def test_projection(self):\n        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())\n        self.assertEqual(len(p.constraints),2)\n    def test_internal_boundary(self):\n        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())\n        self.assertEqual(len(p.internal_constraint_hashes),1)\n        self.assertEqual(len(p.boundary_constraint_hashes),1)\n    def test_type_query(self):\n        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())\n        self.assertEqual(len(p.constraints_of_type("implies")),1)\n        self.assertEqual(len(p.constraints_of_type("mutually_exclusive")),0)\n    def test_outside_constraint_excluded(self):\n        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())\n        self.assertFalse(any(c.basis=="basis:outside" for c in p.constraints))\n    def test_deterministic(self):\n        projector=ChangeConstraintProjector(graph()); d=dependency_projection(); l=lineage()\n        a=projector.project(d,lineage=l); b=projector.project(d,lineage=l)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_graph(self):\n        with self.assertRaises(TypeError): ChangeConstraintProjector(object())\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError): ChangeConstraintProjector(graph()).project(object(),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_152_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-152 CERTIFICATION TEST");print(" CHANGE CONSTRAINT PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD152))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_152_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Internal and boundary market constraints for world-state changes certified")\n    print("[PASS] Unrelated external constraints excluded deterministically")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-152 CERTIFIED")\n'
UPSTREAM_MODULE='umd_151_change_dependency_projection'
UPSTREAM_VERIFIER='verify_umd_151_change_dependency_projection'
EXPORTED_NAMES=('UMD_152_REVISION', 'ChangeConstraintBinding', 'ChangeConstraintProjection', 'ChangeConstraintProjector', 'build_umd_152_certification_manifest', 'verify_umd_152_change_constraint_projection')

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
    marker="# UMD-152 exports"
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
            raise RuntimeError("UMD-152 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-152 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-152 INSTALLER")
    print(" CHANGE CONSTRAINT PROJECTION")
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
        print("[ROLLBACK] UMD-152 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-152',
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
    print("[DONE] UMD-152 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
