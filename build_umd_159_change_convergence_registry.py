from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_159_CHANGE_CONVERGENCE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_159_change_convergence_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_159_change_convergence_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_158_change_convergence_projection import ChangeConvergenceProjection,verify_umd_158_change_convergence_projection\n\nUMD_159_BUILD_ID="UMD-159"\nUMD_159_REVISION="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1"\nUMD_159_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeConvergenceRegistry:\n    projections:Tuple[ChangeConvergenceProjection,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    change_index:Mapping[str,Tuple[str,...]]\n    dependency_index:Mapping[str,Tuple[str,...]]\n    role_index:Mapping[str,Tuple[str,...]]\n    constraint_type_index:Mapping[str,Tuple[str,...]]\n    relation_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"projections",tuple(self.projections))\n        for name in (\n            "market_index","change_index","dependency_index","role_index",\n            "constraint_type_index","relation_index"\n        ):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.projections!=tuple(sorted(self.projections,key=lambda p:p.projection_hash)):\n            raise ValueError("projections must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_159_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-159")\n        required={p.projection_hash for p in self.projections}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every convergence projection hash")\n\n    def convergence_hashes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def markets_for_change(self,change_hash:str)->Tuple[str,...]:\n        return self.change_index.get(change_hash,())\n\n    def markets_for_dependency(self,key:str)->Tuple[str,...]:\n        return self.dependency_index.get(key,())\n\n    def markets_for_role(self,role:str)->Tuple[str,...]:\n        return self.role_index.get(role,())\n\n    def markets_for_constraint_type(self,constraint_type:str)->Tuple[str,...]:\n        return self.constraint_type_index.get(constraint_type,())\n\n    def markets_for_relation(self,relation:str)->Tuple[str,...]:\n        return self.relation_index.get(relation,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "projection_hashes":tuple(p.projection_hash for p in self.projections),\n            "market_index":self.market_index,\n            "change_index":self.change_index,\n            "dependency_index":self.dependency_index,\n            "role_index":self.role_index,\n            "constraint_type_index":self.constraint_type_index,\n            "relation_index":self.relation_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeConvergenceRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        projections:Iterable[ChangeConvergenceProjection],\n        *,\n        lineage_factory,\n    )->ChangeConvergenceRegistry:\n        values=tuple(projections)\n        if any(not isinstance(p,ChangeConvergenceProjection) for p in values):\n            raise TypeError("projections must contain ChangeConvergenceProjection")\n        values=tuple(sorted(values,key=lambda p:p.projection_hash))\n\n        market={}\n        change={}\n        dependency={}\n        role={}\n        constraint={}\n        relation={}\n\n        for projection in values:\n            for convergence in projection.convergences:\n                market.setdefault(convergence.canonical_market_id,[]).append(convergence.convergence_hash)\n                for change_hash in convergence.change_hashes:\n                    change.setdefault(change_hash,[]).append(convergence.canonical_market_id)\n                for key in convergence.dependency_keys:\n                    dependency.setdefault(key,[]).append(convergence.canonical_market_id)\n                for key in convergence.dependency_roles:\n                    role.setdefault(key,[]).append(convergence.canonical_market_id)\n                for key in convergence.constraint_types:\n                    constraint.setdefault(key,[]).append(convergence.canonical_market_id)\n                for key in convergence.relation_types:\n                    relation.setdefault(key,[]).append(convergence.canonical_market_id)\n\n        for index in (market,change,dependency,role,constraint,relation):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        lineage=lineage_factory(tuple(p.projection_hash for p in values))\n        return ChangeConvergenceRegistry(\n            values,market,change,dependency,role,constraint,relation,lineage\n        )\n\ndef build_umd_159_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_159_BUILD_ID,"revision":UMD_159_REVISION,\n        "schema_version":UMD_159_SCHEMA_VERSION,"upstream_builds":("UMD-158",),\n        "mode":"deterministic_read_only_change_convergence_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_159_change_convergence_registry()->bool:\n    if verify_umd_158_change_convergence_projection() is not True:\n        return False\n    m=build_umd_159_certification_manifest()\n    return m["build_id"]=="UMD-159" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import ChangeConvergence,ChangeConvergenceProjection\nfrom qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import *\n\nFIXED=datetime(2026,8,10,12,20,tzinfo=timezone.utc)\nC1="1"*64; C2="2"*64; C3="3"*64\n\ndef projection(market,changes,deps,roles,constraints,relations,seed):\n    conv=ChangeConvergence(\n        market,tuple(changes),tuple(relations),tuple(deps),tuple(roles),\n        tuple(constraints),(),seed*64\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-158",revision="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(conv.convergence_hash,),\n        source_refs=("fixture://159/158",),created_at=FIXED\n    )\n    return ChangeConvergenceProjection((conv,),l)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-159",revision=UMD_159_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://159",),created_at=FIXED\n    )\n\nclass TestUMD159(unittest.TestCase):\n    def setUp(self):\n        self.p1=projection(\n            "m1",(C1,C2),("asset=bitcoin",),("required",),("implies",),\n            ("impacted",),"a"\n        )\n        self.p2=projection(\n            "m2",(C2,C3),("metric=cpi",),("supporting",),("threshold_monotonic",),\n            ("boundary",),"b"\n        )\n        self.r=ChangeConvergenceRegistryBuilder().build((self.p2,self.p1),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_159_change_convergence_registry())\n    def test_market_query(self):\n        self.assertEqual(len(self.r.convergence_hashes_for_market("m1")),1)\n    def test_change_query(self):\n        self.assertEqual(self.r.markets_for_change(C2),("m1","m2"))\n    def test_dependency_query(self):\n        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))\n    def test_role_query(self):\n        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))\n    def test_constraint_query(self):\n        self.assertEqual(self.r.markets_for_constraint_type("implies"),("m1",))\n    def test_relation_query(self):\n        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))\n    def test_unknown(self):\n        self.assertEqual(self.r.markets_for_change("9"*64),())\n    def test_deterministic(self):\n        x=ChangeConvergenceRegistryBuilder().build((self.p1,self.p2),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ChangeConvergenceRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(x.projections,())\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ChangeConvergenceRegistryBuilder().build((object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_159_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-159 CERTIFICATION TEST");print(" CHANGE CONVERGENCE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD159))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_159_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Multi-change convergence reverse queries by market, dependency, role, constraint, and relation certified")\n    print("[PASS] Convergence registry remains deterministic, structural, read-only, and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-159 CERTIFIED")\n'
UPSTREAM_MODULE='umd_158_change_convergence_projection'
UPSTREAM_VERIFIER='verify_umd_158_change_convergence_projection'
EXPORTED_NAMES=('UMD_159_REVISION', 'ChangeConvergenceRegistry', 'ChangeConvergenceRegistryBuilder', 'build_umd_159_certification_manifest', 'verify_umd_159_change_convergence_registry')

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
    marker="# UMD-159 exports"
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
            raise RuntimeError("UMD-159 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-159 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-159 INSTALLER")
    print(" CHANGE CONVERGENCE REGISTRY")
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
        print("[ROLLBACK] UMD-159 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-159',
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
    print("[DONE] UMD-159 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
