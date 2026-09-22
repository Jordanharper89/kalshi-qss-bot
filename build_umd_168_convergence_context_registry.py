from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_168_CONVERGENCE_CONTEXT_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_168_convergence_context_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_168_convergence_context_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_166_convergence_dependency_projection import ConvergenceDependencyProjection\nfrom .umd_167_convergence_constraint_projection import ConvergenceConstraintProjection,verify_umd_167_convergence_constraint_projection\n\nUMD_168_BUILD_ID="UMD-168"\nUMD_168_REVISION="UMD_168_CONVERGENCE_CONTEXT_REGISTRY_V1"\nUMD_168_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceContextRegistry:\n    dependency_projections:Tuple[ConvergenceDependencyProjection,...]\n    constraint_projections:Tuple[ConvergenceConstraintProjection,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    dependency_index:Mapping[str,Tuple[str,...]]\n    role_index:Mapping[str,Tuple[str,...]]\n    constraint_index:Mapping[str,Tuple[str,...]]\n    relation_index:Mapping[str,Tuple[str,...]]\n    change_type_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"dependency_projections",tuple(self.dependency_projections))\n        object.__setattr__(self,"constraint_projections",tuple(self.constraint_projections))\n        for name in (\n            "market_index","dependency_index","role_index","constraint_index",\n            "relation_index","change_type_index"\n        ):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.dependency_projections!=tuple(sorted(self.dependency_projections,key=lambda p:p.projection_hash)):\n            raise ValueError("dependency projections must be deterministically sorted")\n        if self.constraint_projections!=tuple(sorted(self.constraint_projections,key=lambda p:p.projection_hash)):\n            raise ValueError("constraint projections must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_168_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-168")\n        required={p.projection_hash for p in self.dependency_projections}|{\n            p.projection_hash for p in self.constraint_projections\n        }\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every convergence context projection hash")\n\n    def change_types_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n    def markets_for_dependency(self,key:str)->Tuple[str,...]:\n        return self.dependency_index.get(key,())\n    def markets_for_role(self,role:str)->Tuple[str,...]:\n        return self.role_index.get(role,())\n    def markets_for_constraint(self,constraint_type:str)->Tuple[str,...]:\n        return self.constraint_index.get(constraint_type,())\n    def markets_for_relation(self,relation:str)->Tuple[str,...]:\n        return self.relation_index.get(relation,())\n    def markets_for_change_type(self,change_type:str)->Tuple[str,...]:\n        return self.change_type_index.get(change_type,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "dependency_projection_hashes":tuple(p.projection_hash for p in self.dependency_projections),\n            "constraint_projection_hashes":tuple(p.projection_hash for p in self.constraint_projections),\n            "market_index":self.market_index,\n            "dependency_index":self.dependency_index,\n            "role_index":self.role_index,\n            "constraint_index":self.constraint_index,\n            "relation_index":self.relation_index,\n            "change_type_index":self.change_type_index,\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceContextRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        dependency_projections:Iterable[ConvergenceDependencyProjection],\n        constraint_projections:Iterable[ConvergenceConstraintProjection],\n        *,\n        lineage_factory,\n    )->ConvergenceContextRegistry:\n        deps=tuple(dependency_projections)\n        cons=tuple(constraint_projections)\n        if any(not isinstance(p,ConvergenceDependencyProjection) for p in deps):\n            raise TypeError("dependency_projections must contain ConvergenceDependencyProjection")\n        if any(not isinstance(p,ConvergenceConstraintProjection) for p in cons):\n            raise TypeError("constraint_projections must contain ConvergenceConstraintProjection")\n\n        deps=tuple(sorted(deps,key=lambda p:p.projection_hash))\n        cons=tuple(sorted(cons,key=lambda p:p.projection_hash))\n\n        market={}; dependency={}; role={}; constraint={}; relation={}; change_type={}\n\n        for projection in deps:\n            for context in projection.contexts:\n                market.setdefault(context.canonical_market_id,[]).extend(context.convergence_change_types)\n                for key in context.dependency_keys:\n                    dependency.setdefault(key,[]).append(context.canonical_market_id)\n                for key in context.dependency_roles:\n                    role.setdefault(key,[]).append(context.canonical_market_id)\n                for key in context.convergence_change_types:\n                    change_type.setdefault(key,[]).append(context.canonical_market_id)\n\n        for projection in cons:\n            for context in projection.contexts:\n                market.setdefault(context.canonical_market_id,[]).extend(context.convergence_change_types)\n                for key in context.constraint_types:\n                    constraint.setdefault(key,[]).append(context.canonical_market_id)\n                for key in context.relation_types:\n                    relation.setdefault(key,[]).append(context.canonical_market_id)\n                for key in context.convergence_change_types:\n                    change_type.setdefault(key,[]).append(context.canonical_market_id)\n\n        for index in (market,dependency,role,constraint,relation,change_type):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        parents=tuple(p.projection_hash for p in deps)+tuple(p.projection_hash for p in cons)\n        lineage=lineage_factory(parents)\n        return ConvergenceContextRegistry(\n            deps,cons,market,dependency,role,constraint,relation,change_type,lineage\n        )\n\ndef build_umd_168_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_168_BUILD_ID,"revision":UMD_168_REVISION,\n        "schema_version":UMD_168_SCHEMA_VERSION,"upstream_builds":("UMD-166","UMD-167"),\n        "mode":"deterministic_read_only_convergence_context_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_168_convergence_context_registry()->bool:\n    if verify_umd_167_convergence_constraint_projection() is not True:\n        return False\n    m=build_umd_168_certification_manifest()\n    return m["build_id"]=="UMD-168" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import ConvergenceDependencyContext,ConvergenceDependencyProjection\nfrom qseries_v2.universal_market_discovery.umd_167_convergence_constraint_projection import ConvergenceConstraintContext,ConvergenceConstraintProjection\nfrom qseries_v2.universal_market_discovery.umd_168_convergence_context_registry import *\n\nFIXED=datetime(2026,8,10,15,20,tzinfo=timezone.utc)\n\ndef dp():\n    c1=ConvergenceDependencyContext("m1",("convergence-added",),("asset=bitcoin",),("required",))\n    c2=ConvergenceDependencyContext("m2",("convergence-composition-changed",),("metric=cpi",),("supporting",))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-166",revision="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),\n        source_refs=("fixture://168/166",),created_at=FIXED\n    )\n    return ConvergenceDependencyProjection((c1,c2),l)\n\ndef cp():\n    c1=ConvergenceConstraintContext("m1",("convergence-added",),("implies",),("impacted",))\n    c2=ConvergenceConstraintContext("m2",("convergence-composition-changed",),("threshold_monotonic",),("boundary",))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-167",revision="UMD_167_CONVERGENCE_CONSTRAINT_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),\n        source_refs=("fixture://168/167",),created_at=FIXED\n    )\n    return ConvergenceConstraintProjection((c1,c2),l)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-168",revision=UMD_168_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://168",),created_at=FIXED\n    )\n\nclass TestUMD168(unittest.TestCase):\n    def setUp(self):\n        self.r=ConvergenceContextRegistryBuilder().build((dp(),),(cp(),),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_168_convergence_context_registry())\n    def test_market_query(self):\n        self.assertEqual(self.r.change_types_for_market("m1"),("convergence-added",))\n    def test_dependency_query(self):\n        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))\n    def test_role_query(self):\n        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))\n    def test_constraint_query(self):\n        self.assertEqual(self.r.markets_for_constraint("implies"),("m1",))\n    def test_relation_query(self):\n        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))\n    def test_change_type_query(self):\n        self.assertEqual(self.r.markets_for_change_type("convergence-composition-changed"),("m2",))\n    def test_unknown(self):\n        self.assertEqual(self.r.markets_for_dependency("missing"),())\n    def test_deterministic(self):\n        x=ConvergenceContextRegistryBuilder().build((dp(),),(cp(),),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ConvergenceContextRegistryBuilder().build((),(),lineage_factory=lf)\n        self.assertEqual(x.dependency_projections,())\n        self.assertEqual(x.constraint_projections,())\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ConvergenceContextRegistryBuilder().build((object(),),(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_168_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-168 CERTIFICATION TEST");print(" CONVERGENCE CONTEXT REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD168))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_168_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Convergence context queries by market, dependency, role, constraint, relation, and change type certified")\n    print("[PASS] Temporal convergence now retains deterministic structural context without prediction or scoring")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-168 CERTIFIED")\n'
UPSTREAM_MODULE='umd_167_convergence_constraint_projection'
UPSTREAM_VERIFIER='verify_umd_167_convergence_constraint_projection'
EXPORTED_NAMES=('UMD_168_REVISION', 'ConvergenceContextRegistry', 'ConvergenceContextRegistryBuilder', 'build_umd_168_certification_manifest', 'verify_umd_168_convergence_context_registry')

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
    marker="# UMD-168 exports"
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
            raise RuntimeError("UMD-168 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-168 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-168 INSTALLER")
    print(" CONVERGENCE CONTEXT REGISTRY")
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
        print("[ROLLBACK] UMD-168 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-168',
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
    print("[DONE] UMD-168 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
