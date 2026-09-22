from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_158_CHANGE_CONVERGENCE_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_158_change_convergence_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_158_change_convergence_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_153_change_dependency_context_registry import ChangeDependencyContextRegistry\nfrom .umd_157_change_co_occurrence_model import ChangeCoOccurrenceModel,ChangeCoOccurrence,verify_umd_157_change_co_occurrence_model\n\nUMD_158_BUILD_ID="UMD-158"\nUMD_158_REVISION="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1"\nUMD_158_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ChangeConvergence:\n    canonical_market_id:str\n    change_hashes:Tuple[str,...]\n    relation_types:Tuple[str,...]\n    dependency_keys:Tuple[str,...]\n    dependency_roles:Tuple[str,...]\n    constraint_types:Tuple[str,...]\n    boundary_change_hashes:Tuple[str,...]\n    occurrence_hash:str\n\n    def __post_init__(self):\n        for name in (\n            "change_hashes","relation_types","dependency_keys",\n            "dependency_roles","constraint_types","boundary_change_hashes"\n        ):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if len(self.change_hashes)<2:\n            raise ValueError("convergence requires at least two distinct changes")\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n\n    @property\n    def convergence_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "change_hashes":self.change_hashes,\n            "relation_types":self.relation_types,\n            "dependency_keys":self.dependency_keys,\n            "dependency_roles":self.dependency_roles,\n            "constraint_types":self.constraint_types,\n            "boundary_change_hashes":self.boundary_change_hashes,\n            "occurrence_hash":self.occurrence_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeConvergenceProjection:\n    convergences:Tuple[ChangeConvergence,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"convergences",tuple(self.convergences))\n        if self.convergences!=tuple(sorted(\n            self.convergences,key=lambda c:(c.canonical_market_id,c.convergence_hash)\n        )):\n            raise ValueError("convergences must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_158_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-158")\n        required={c.convergence_hash for c in self.convergences}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every convergence hash")\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "convergence_hashes":tuple(c.convergence_hash for c in self.convergences),\n            "lineage":self.lineage,\n        })\n\nclass ChangeConvergenceProjector:\n    __slots__=()\n\n    def project(\n        self,\n        co_occurrence_model:ChangeCoOccurrenceModel,\n        dependency_context:ChangeDependencyContextRegistry,\n        *,\n        lineage_factory,\n    )->ChangeConvergenceProjection:\n        if not isinstance(co_occurrence_model,ChangeCoOccurrenceModel):\n            raise TypeError("co_occurrence_model must be ChangeCoOccurrenceModel")\n        if not isinstance(dependency_context,ChangeDependencyContextRegistry):\n            raise TypeError("dependency_context must be ChangeDependencyContextRegistry")\n\n        convergences=[]\n\n        for occurrence in co_occurrence_model.occurrences:\n            market_id=occurrence.canonical_market_id\n            change_set=set(occurrence.change_hashes)\n\n            dependency_keys=tuple(sorted(\n                key for key,changes in dependency_context.dependency_index.items()\n                if change_set.intersection(changes)\n            ))\n            dependency_roles=tuple(sorted(\n                role for role,changes in dependency_context.role_index.items()\n                if change_set.intersection(changes)\n            ))\n            constraint_types=tuple(sorted(\n                ctype for ctype,changes in dependency_context.constraint_type_index.items()\n                if change_set.intersection(changes)\n            ))\n            boundary_changes=tuple(sorted(\n                change_set.intersection(\n                    dependency_context.boundary_market_index.get(market_id,())\n                )\n            ))\n\n            convergences.append(ChangeConvergence(\n                market_id,\n                occurrence.change_hashes,\n                tuple(sorted(occurrence.relation_types)),\n                dependency_keys,\n                dependency_roles,\n                constraint_types,\n                boundary_changes,\n                occurrence.occurrence_hash,\n            ))\n\n        convergences.sort(key=lambda c:(c.canonical_market_id,c.convergence_hash))\n        lineage=lineage_factory(tuple(c.convergence_hash for c in convergences))\n        return ChangeConvergenceProjection(tuple(convergences),lineage)\n\ndef build_umd_158_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_158_BUILD_ID,"revision":UMD_158_REVISION,\n        "schema_version":UMD_158_SCHEMA_VERSION,"upstream_builds":("UMD-153","UMD-157"),\n        "mode":"deterministic_read_only_change_convergence_projection",\n        "semantics":"context_enrichment_only_no_convergence_score",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_158_change_convergence_projection()->bool:\n    if verify_umd_157_change_co_occurrence_model() is not True:\n        return False\n    m=build_umd_158_certification_manifest()\n    return m["build_id"]=="UMD-158" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyBinding,ChangeDependencyProjection\nfrom qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection\nfrom qseries_v2.universal_market_discovery.umd_153_change_dependency_context_registry import ChangeDependencyContextRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_157_change_co_occurrence_model import ChangeCoOccurrence,ChangeCoOccurrenceModel\nfrom qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import *\n\nFIXED=datetime(2026,8,10,12,10,tzinfo=timezone.utc)\nC1="1"*64; C2="2"*64\n\ndef co_model():\n    o=ChangeCoOccurrence("m1",(C1,C2),((C1,C2),),("impacted","boundary"))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-157",revision="UMD_157_CHANGE_CO_OCCURRENCE_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(o.occurrence_hash,),\n        source_refs=("fixture://158/157",),created_at=FIXED\n    )\n    return ChangeCoOccurrenceModel((o,),{"m1":(C1,C2)},{C1:("m1",),C2:("m1",)},l)\n\ndef dep_proj(change,kind,key,role,seed):\n    b=ChangeDependencyBinding("m1",kind,key,role,seed*64)\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://158/151",),created_at=FIXED\n    )\n    return ChangeDependencyProjection(\n        change,("m1",),(b,),{role:("m1",)},{kind+"="+key:("m1",)},(),l\n    )\n\ndef con_proj(change,ctype,boundary,seed):\n    b=ChangeConstraintBinding(\n        "m1","m2",ctype,"basis:"+seed,True,not boundary,seed*64\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://158/152",),created_at=FIXED\n    )\n    return ChangeConstraintProjection(\n        change,("m1",),(b,),\n        () if boundary else (b.constraint_hash,),\n        (b.constraint_hash,) if boundary else (),\n        l,\n    )\n\ndef dependency_context():\n    d1=dep_proj(C1,"asset","bitcoin","required","a")\n    d2=dep_proj(C2,"metric","cpi","supporting","b")\n    k1=con_proj(C1,"implies",True,"c")\n    k2=con_proj(C2,"threshold_monotonic",False,"d")\n    def lf(parents):\n        return ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-153",revision="UMD_153_CHANGE_DEPENDENCY_CONTEXT_REGISTRY_V1",\n            schema_version="1.0.0",parent_hashes=parents,\n            source_refs=("fixture://158/153",),created_at=FIXED\n        )\n    return ChangeDependencyContextRegistryBuilder().build((d1,d2),(k1,k2),lineage_factory=lf)\n\ndef lf158(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-158",revision=UMD_158_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://158",),created_at=FIXED\n    )\n\nclass TestUMD158(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_158_change_convergence_projection())\n    def test_projection(self):\n        p=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)\n        self.assertEqual(len(p.convergences),1)\n        c=p.convergences[0]\n        self.assertEqual(c.canonical_market_id,"m1")\n        self.assertEqual(c.change_hashes,(C1,C2))\n    def test_dependency_context(self):\n        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]\n        self.assertEqual(c.dependency_keys,("asset=bitcoin","metric=cpi"))\n        self.assertEqual(c.dependency_roles,("required","supporting"))\n    def test_constraint_context(self):\n        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]\n        self.assertEqual(c.constraint_types,("implies","threshold_monotonic"))\n    def test_boundary_context(self):\n        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]\n        self.assertEqual(c.boundary_change_hashes,(C1,))\n    def test_relations_preserved(self):\n        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]\n        self.assertEqual(c.relation_types,("boundary","impacted"))\n    def test_deterministic(self):\n        a=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)\n        b=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_model(self):\n        with self.assertRaises(TypeError):\n            ChangeConvergenceProjector().project(object(),dependency_context(),lineage_factory=lf158)\n    def test_side_effects(self):\n        m=build_umd_158_certification_manifest()\n        self.assertEqual(m["semantics"],"context_enrichment_only_no_convergence_score")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-158 CERTIFICATION TEST");print(" CHANGE CONVERGENCE PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD158))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_158_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Multi-change market convergence enriched with dependency and constraint context")\n    print("[PASS] No convergence score, probability, or trade-value judgment introduced")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-158 CERTIFIED")\n'
UPSTREAM_MODULE='umd_157_change_co_occurrence_model'
UPSTREAM_VERIFIER='verify_umd_157_change_co_occurrence_model'
EXPORTED_NAMES=('UMD_158_REVISION', 'ChangeConvergence', 'ChangeConvergenceProjection', 'ChangeConvergenceProjector', 'build_umd_158_certification_manifest', 'verify_umd_158_change_convergence_projection')

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
    marker="# UMD-158 exports"
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
            raise RuntimeError("UMD-158 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-158 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-158 INSTALLER")
    print(" CHANGE CONVERGENCE PROJECTION")
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
        print("[ROLLBACK] UMD-158 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-158',
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
    print("[DONE] UMD-158 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
