from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_166_convergence_dependency_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_166_convergence_dependency_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_159_change_convergence_registry import ChangeConvergenceRegistry\nfrom .umd_162_convergence_change_registry import ConvergenceChangeRegistry,verify_umd_162_convergence_change_registry\n\nUMD_166_BUILD_ID="UMD-166"\nUMD_166_REVISION="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1"\nUMD_166_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceDependencyContext:\n    canonical_market_id:str\n    convergence_change_types:Tuple[str,...]\n    dependency_keys:Tuple[str,...]\n    dependency_roles:Tuple[str,...]\n\n    def __post_init__(self):\n        for name in ("convergence_change_types","dependency_keys","dependency_roles"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        if not self.convergence_change_types:\n            raise ValueError("convergence change context requires at least one change type")\n\n    @property\n    def context_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "convergence_change_types":self.convergence_change_types,\n            "dependency_keys":self.dependency_keys,\n            "dependency_roles":self.dependency_roles,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceDependencyProjection:\n    contexts:Tuple[ConvergenceDependencyContext,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"contexts",tuple(self.contexts))\n        if self.contexts!=tuple(sorted(\n            self.contexts,key=lambda c:(c.canonical_market_id,c.context_hash)\n        )):\n            raise ValueError("contexts must be deterministically sorted")\n        if len({c.canonical_market_id for c in self.contexts})!=len(self.contexts):\n            raise ValueError("market dependency contexts must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_166_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-166")\n        required={c.context_hash for c in self.contexts}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every dependency context hash")\n\n    def context_for_market(self,market_id:str)->ConvergenceDependencyContext|None:\n        for context in self.contexts:\n            if context.canonical_market_id==market_id:\n                return context\n        return None\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "context_hashes":tuple(c.context_hash for c in self.contexts),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceDependencyProjector:\n    __slots__=("convergence_registry","change_registry")\n\n    def __init__(\n        self,\n        convergence_registry:ChangeConvergenceRegistry,\n        change_registry:ConvergenceChangeRegistry,\n    ):\n        if not isinstance(convergence_registry,ChangeConvergenceRegistry):\n            raise TypeError("convergence_registry must be ChangeConvergenceRegistry")\n        if not isinstance(change_registry,ConvergenceChangeRegistry):\n            raise TypeError("change_registry must be ConvergenceChangeRegistry")\n        self.convergence_registry=convergence_registry\n        self.change_registry=change_registry\n\n    def project(self,*,lineage_factory)->ConvergenceDependencyProjection:\n        market_types={}\n        for record in self.change_registry.records:\n            market_types.setdefault(record.canonical_market_id,[]).append(record.change_type)\n\n        contexts=[]\n        for market_id,types in sorted(market_types.items()):\n            dependencies=tuple(sorted(\n                key for key,markets in self.convergence_registry.dependency_index.items()\n                if market_id in markets\n            ))\n            roles=tuple(sorted(\n                role for role,markets in self.convergence_registry.role_index.items()\n                if market_id in markets\n            ))\n            contexts.append(ConvergenceDependencyContext(\n                market_id,\n                tuple(sorted(set(types))),\n                dependencies,\n                roles,\n            ))\n\n        contexts.sort(key=lambda c:(c.canonical_market_id,c.context_hash))\n        lineage=lineage_factory(tuple(c.context_hash for c in contexts))\n        return ConvergenceDependencyProjection(tuple(contexts),lineage)\n\ndef build_umd_166_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_166_BUILD_ID,"revision":UMD_166_REVISION,\n        "schema_version":UMD_166_SCHEMA_VERSION,"upstream_builds":("UMD-159","UMD-162"),\n        "mode":"deterministic_read_only_convergence_dependency_projection",\n        "semantics":"dependency_context_only_no_score_or_prediction",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_166_convergence_dependency_projection()->bool:\n    if verify_umd_162_convergence_change_registry() is not True:\n        return False\n    m=build_umd_166_certification_manifest()\n    return m["build_id"]=="UMD-166" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistry\nfrom qseries_v2.universal_market_discovery.umd_162_convergence_change_registry import ConvergenceChangeRecord,ConvergenceChangeRegistry\nfrom qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import *\n\nFIXED=datetime(2026,8,10,15,0,tzinfo=timezone.utc)\n\ndef convergence_registry():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://166/159",),created_at=FIXED\n    )\n    return ChangeConvergenceRegistry(\n        (),{},\n        {},\n        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},\n        {"required":("m1",),"supporting":("m2",)},\n        {},\n        {},\n        l,\n    )\n\ndef change_registry():\n    r1=ConvergenceChangeRecord("convergence-added","m1","1"*64,(),())\n    r2=ConvergenceChangeRecord("convergence-composition-changed","m2","2"*64,("3"*64,),())\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-162",revision="UMD_162_CONVERGENCE_CHANGE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://166/162",),created_at=FIXED\n    )\n    return ConvergenceChangeRegistry(\n        (),\n        tuple(sorted((r1,r2),key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash))),\n        {},{}, {},l\n    )\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-166",revision=UMD_166_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://166",),created_at=FIXED\n    )\n\nclass TestUMD166(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_166_convergence_dependency_projection())\n    def test_projection(self):\n        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)\n        self.assertEqual(tuple(c.canonical_market_id for c in p.contexts),("m1","m2"))\n    def test_dependency_context(self):\n        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m1").dependency_keys,("asset=bitcoin",))\n        self.assertEqual(p.context_for_market("m2").dependency_keys,("metric=cpi",))\n    def test_role_context(self):\n        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m1").dependency_roles,("required",))\n        self.assertEqual(p.context_for_market("m2").dependency_roles,("supporting",))\n    def test_change_type_preserved(self):\n        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)\n        self.assertEqual(p.context_for_market("m1").convergence_change_types,("convergence-added",))\n    def test_unknown(self):\n        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)\n        self.assertIsNone(p.context_for_market("missing"))\n    def test_deterministic(self):\n        projector=ConvergenceDependencyProjector(convergence_registry(),change_registry())\n        a=projector.project(lineage_factory=lf); b=projector.project(lineage_factory=lf)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ConvergenceDependencyProjector(object(),change_registry())\n    def test_side_effects(self):\n        m=build_umd_166_certification_manifest()\n        self.assertEqual(m["semantics"],"dependency_context_only_no_score_or_prediction")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-166 CERTIFICATION TEST");print(" CONVERGENCE DEPENDENCY PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD166))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_166_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Convergence-changing markets enriched with certified dependency keys and roles")\n    print("[PASS] Dependency context remains structural, deterministic, and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-166 CERTIFIED")\n'
UPSTREAM_MODULE='umd_165_convergence_surface_registry'
UPSTREAM_VERIFIER='verify_umd_165_convergence_surface_registry'
EXPORTED_NAMES=('UMD_166_REVISION', 'ConvergenceDependencyContext', 'ConvergenceDependencyProjection', 'ConvergenceDependencyProjector', 'build_umd_166_certification_manifest', 'verify_umd_166_convergence_dependency_projection')

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
    marker="# UMD-166 exports"
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
            raise RuntimeError("UMD-166 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-166 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-166 INSTALLER")
    print(" CONVERGENCE DEPENDENCY PROJECTION")
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
        print("[ROLLBACK] UMD-166 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-166',
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
    print("[DONE] UMD-166 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
