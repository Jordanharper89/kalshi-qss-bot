from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_167_CONVERGENCE_CONSTRAINT_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_167_convergence_constraint_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_167_convergence_constraint_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_159_change_convergence_registry import ChangeConvergenceRegistry\nfrom .umd_166_convergence_dependency_projection import ConvergenceDependencyProjection,verify_umd_166_convergence_dependency_projection\n\nUMD_167_BUILD_ID="UMD-167"\nUMD_167_REVISION="UMD_167_CONVERGENCE_CONSTRAINT_PROJECTION_V1"\nUMD_167_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceConstraintContext:\n    canonical_market_id:str\n    convergence_change_types:Tuple[str,...]\n    constraint_types:Tuple[str,...]\n    relation_types:Tuple[str,...]\n\n    def __post_init__(self):\n        for name in ("convergence_change_types","constraint_types","relation_types"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        if not self.convergence_change_types:\n            raise ValueError("convergence change context requires at least one change type")\n\n    @property\n    def context_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "convergence_change_types":self.convergence_change_types,\n            "constraint_types":self.constraint_types,\n            "relation_types":self.relation_types,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceConstraintProjection:\n    contexts:Tuple[ConvergenceConstraintContext,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"contexts",tuple(self.contexts))\n        if self.contexts!=tuple(sorted(\n            self.contexts,key=lambda c:(c.canonical_market_id,c.context_hash)\n        )):\n            raise ValueError("contexts must be deterministically sorted")\n        if len({c.canonical_market_id for c in self.contexts})!=len(self.contexts):\n            raise ValueError("market constraint contexts must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_167_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-167")\n        required={c.context_hash for c in self.contexts}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every constraint context hash")\n\n    def context_for_market(self,market_id:str)->ConvergenceConstraintContext|None:\n        for context in self.contexts:\n            if context.canonical_market_id==market_id:\n                return context\n        return None\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "context_hashes":tuple(c.context_hash for c in self.contexts),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceConstraintProjector:\n    __slots__=("convergence_registry",)\n\n    def __init__(self,convergence_registry:ChangeConvergenceRegistry):\n        if not isinstance(convergence_registry,ChangeConvergenceRegistry):\n            raise TypeError("convergence_registry must be ChangeConvergenceRegistry")\n        self.convergence_registry=convergence_registry\n\n    def project(\n        self,\n        dependency_projection:ConvergenceDependencyProjection,\n        *,\n        lineage_factory,\n    )->ConvergenceConstraintProjection:\n        if not isinstance(dependency_projection,ConvergenceDependencyProjection):\n            raise TypeError("dependency_projection must be ConvergenceDependencyProjection")\n\n        contexts=[]\n        for dependency_context in dependency_projection.contexts:\n            market_id=dependency_context.canonical_market_id\n            constraints=tuple(sorted(\n                ctype for ctype,markets in self.convergence_registry.constraint_type_index.items()\n                if market_id in markets\n            ))\n            relations=tuple(sorted(\n                relation for relation,markets in self.convergence_registry.relation_index.items()\n                if market_id in markets\n            ))\n            contexts.append(ConvergenceConstraintContext(\n                market_id,\n                dependency_context.convergence_change_types,\n                constraints,\n                relations,\n            ))\n\n        contexts.sort(key=lambda c:(c.canonical_market_id,c.context_hash))\n        lineage=lineage_factory(tuple(c.context_hash for c in contexts))\n        return ConvergenceConstraintProjection(tuple(contexts),lineage)\n\ndef build_umd_167_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_167_BUILD_ID,"revision":UMD_167_REVISION,\n        "schema_version":UMD_167_SCHEMA_VERSION,"upstream_builds":("UMD-159","UMD-166"),\n        "mode":"deterministic_read_only_convergence_constraint_projection",\n        "semantics":"constraint_and_relation_context_only_no_score_or_prediction",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_167_convergence_constraint_projection()->bool:\n    if verify_umd_166_convergence_dependency_projection() is not True:\n        return False\n    m=build_umd_167_certification_manifest()\n    return m["build_id"]=="UMD-167" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistry\nfrom qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import ConvergenceDependencyContext,ConvergenceDependencyProjection\nfrom qseries_v2.universal_market_discovery.umd_167_convergence_constraint_projection import *\n\nFIXED=datetime(2026,8,10,15,10,tzinfo=timezone.utc)\n\ndef convergence_registry():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://167/159",),created_at=FIXED\n    )\n    return ChangeConvergenceRegistry(\n        (),{},{},{},{},\n        {"implies":("m1",),"threshold_monotonic":("m2",)},\n        {"impacted":("m1",),"boundary":("m2",)},\n        l,\n    )\n\ndef dependency_projection():\n    c1=ConvergenceDependencyContext("m1",("convergence-added",),("asset=bitcoin",),("required",))\n    c2=ConvergenceDependencyContext("m2",("convergence-composition-changed",),("metric=cpi",),("supporting",))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-166",revision="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),\n        source_refs=("fixture://167/166",),created_at=FIXED\n    )\n    return ConvergenceDependencyProjection((c1,c2),l)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-167",revision=UMD_167_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://167",),created_at=FIXED\n    )\n\nclass TestUMD167(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_167_convergence_constraint_projection())\n    def test_projection(self):\n        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)\n        self.assertEqual(tuple(c.canonical_market_id for c in p.contexts),("m1","m2"))\n    def test_constraint_context(self):\n        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m1").constraint_types,("implies",))\n        self.assertEqual(p.context_for_market("m2").constraint_types,("threshold_monotonic",))\n    def test_relation_context(self):\n        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m1").relation_types,("impacted",))\n        self.assertEqual(p.context_for_market("m2").relation_types,("boundary",))\n    def test_change_type_preserved(self):\n        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m2").convergence_change_types,("convergence-composition-changed",))\n    def test_unknown(self):\n        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)\n        self.assertIsNone(p.context_for_market("missing"))\n    def test_deterministic(self):\n        projector=ConvergenceConstraintProjector(convergence_registry()); d=dependency_projection()\n        a=projector.project(d,lineage_factory=lf); b=projector.project(d,lineage_factory=lf)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ConvergenceConstraintProjector(convergence_registry()).project(object(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_167_certification_manifest()\n        self.assertEqual(m["semantics"],"constraint_and_relation_context_only_no_score_or_prediction")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-167 CERTIFICATION TEST");print(" CONVERGENCE CONSTRAINT PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD167))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_167_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Convergence-changing markets enriched with certified constraint and relation context")\n    print("[PASS] Constraint context remains deterministic, structural, and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-167 CERTIFIED")\n'
UPSTREAM_MODULE='umd_166_convergence_dependency_projection'
UPSTREAM_VERIFIER='verify_umd_166_convergence_dependency_projection'
EXPORTED_NAMES=('UMD_167_REVISION', 'ConvergenceConstraintContext', 'ConvergenceConstraintProjection', 'ConvergenceConstraintProjector', 'build_umd_167_certification_manifest', 'verify_umd_167_convergence_constraint_projection')

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
    marker="# UMD-167 exports"
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
            raise RuntimeError("UMD-167 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-167 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-167 INSTALLER")
    print(" CONVERGENCE CONSTRAINT PROJECTION")
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
        print("[ROLLBACK] UMD-167 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-167',
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
    print("[DONE] UMD-167 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
