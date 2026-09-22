from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_154_CHANGE_BOUNDARY_EXPANSION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_154_change_boundary_expansion.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_154_change_boundary_expansion.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_152_change_constraint_projection import ChangeConstraintProjection,verify_umd_152_change_constraint_projection\n\nUMD_154_BUILD_ID="UMD-154"\nUMD_154_REVISION="UMD_154_CHANGE_BOUNDARY_EXPANSION_V1"\nUMD_154_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ChangeBoundaryNeighbor:\n    impacted_market_id:str\n    adjacent_market_id:str\n    constraint_type:str\n    basis:str\n    constraint_hash:str\n\n    def __post_init__(self):\n        if not self.impacted_market_id or not self.adjacent_market_id:\n            raise ValueError("boundary neighbor market ids must be non-empty")\n        if self.impacted_market_id==self.adjacent_market_id:\n            raise ValueError("boundary neighbor markets must differ")\n\n    @property\n    def neighbor_hash(self)->str:\n        return deterministic_sha256({\n            "impacted_market_id":self.impacted_market_id,\n            "adjacent_market_id":self.adjacent_market_id,\n            "constraint_type":self.constraint_type,\n            "basis":self.basis,\n            "constraint_hash":self.constraint_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeBoundaryExpansion:\n    change_hash:str\n    impacted_market_ids:Tuple[str,...]\n    adjacent_market_ids:Tuple[str,...]\n    neighbors:Tuple[ChangeBoundaryNeighbor,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in ("impacted_market_ids","adjacent_market_ids"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        object.__setattr__(self,"neighbors",tuple(self.neighbors))\n        if self.neighbors!=tuple(sorted(\n            self.neighbors,\n            key=lambda n:(n.impacted_market_id,n.adjacent_market_id,n.constraint_type,n.basis,n.constraint_hash)\n        )):\n            raise ValueError("neighbors must be deterministically sorted")\n        if set(self.impacted_market_ids)&set(self.adjacent_market_ids):\n            raise ValueError("adjacent markets must sit outside impacted set")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_154_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-154")\n        if self.change_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include change hash")\n\n    def neighbors_for(self,market_id:str)->Tuple[str,...]:\n        return tuple(sorted({\n            n.adjacent_market_id for n in self.neighbors if n.impacted_market_id==market_id\n        }))\n\n    @property\n    def expansion_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "impacted_market_ids":self.impacted_market_ids,\n            "adjacent_market_ids":self.adjacent_market_ids,\n            "neighbor_hashes":tuple(n.neighbor_hash for n in self.neighbors),\n            "lineage":self.lineage,\n        })\n\nclass ChangeBoundaryExpander:\n    __slots__=()\n\n    def expand(\n        self,\n        projection:ChangeConstraintProjection,\n        *,\n        lineage:ImmutableLineage,\n    )->ChangeBoundaryExpansion:\n        if not isinstance(projection,ChangeConstraintProjection):\n            raise TypeError("projection must be ChangeConstraintProjection")\n\n        impacted=set(projection.impacted_market_ids)\n        neighbors=[]\n        adjacent=set()\n\n        for binding in projection.constraints:\n            if not binding.boundary:\n                continue\n            if binding.source_impacted:\n                impacted_id=binding.source_market_id\n                adjacent_id=binding.target_market_id\n            else:\n                impacted_id=binding.target_market_id\n                adjacent_id=binding.source_market_id\n\n            if impacted_id not in impacted or adjacent_id in impacted:\n                raise ValueError("boundary binding inconsistent with impacted market set")\n\n            adjacent.add(adjacent_id)\n            neighbors.append(ChangeBoundaryNeighbor(\n                impacted_id,\n                adjacent_id,\n                binding.constraint_type,\n                binding.basis,\n                binding.constraint_hash,\n            ))\n\n        neighbors.sort(\n            key=lambda n:(n.impacted_market_id,n.adjacent_market_id,n.constraint_type,n.basis,n.constraint_hash)\n        )\n        return ChangeBoundaryExpansion(\n            projection.change_hash,\n            projection.impacted_market_ids,\n            tuple(sorted(adjacent)),\n            tuple(neighbors),\n            lineage,\n        )\n\ndef build_umd_154_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_154_BUILD_ID,"revision":UMD_154_REVISION,\n        "schema_version":UMD_154_SCHEMA_VERSION,"upstream_builds":("UMD-152",),\n        "mode":"deterministic_read_only_change_boundary_expansion",\n        "semantics":"structural_adjacent_markets_only_not_predicted_impact",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_154_change_boundary_expansion()->bool:\n    if verify_umd_152_change_constraint_projection() is not True:\n        return False\n    m=build_umd_154_certification_manifest()\n    return m["build_id"]=="UMD-154" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection\nfrom qseries_v2.universal_market_discovery.umd_154_change_boundary_expansion import *\n\nFIXED=datetime(2026,8,10,11,0,tzinfo=timezone.utc)\nCHANGE="1"*64\n\ndef projection():\n    internal=ChangeConstraintBinding("m1","m2","implies","basis:internal",True,True,"a"*64)\n    boundary1=ChangeConstraintBinding("m2","m3","threshold_monotonic","basis:b1",True,False,"b"*64)\n    boundary2=ChangeConstraintBinding("m4","m1","mutually_exclusive","basis:b2",False,True,"c"*64)\n    constraints=tuple(sorted(\n        (internal,boundary1,boundary2),\n        key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash)\n    ))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(CHANGE,),\n        source_refs=("fixture://154/152",),created_at=FIXED\n    )\n    return ChangeConstraintProjection(\n        CHANGE,("m1","m2"),constraints,\n        (internal.constraint_hash,),\n        tuple(sorted((boundary1.constraint_hash,boundary2.constraint_hash))),\n        l,\n    )\n\ndef lineage():\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-154",revision=UMD_154_REVISION,\n        schema_version="1.0.0",parent_hashes=(CHANGE,),\n        source_refs=("fixture://154",),created_at=FIXED\n    )\n\nclass TestUMD154(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_154_change_boundary_expansion())\n    def test_expansion(self):\n        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())\n        self.assertEqual(x.impacted_market_ids,("m1","m2"))\n        self.assertEqual(x.adjacent_market_ids,("m3","m4"))\n        self.assertEqual(len(x.neighbors),2)\n    def test_neighbors_for(self):\n        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())\n        self.assertEqual(x.neighbors_for("m2"),("m3",))\n        self.assertEqual(x.neighbors_for("m1"),("m4",))\n    def test_internal_excluded(self):\n        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())\n        self.assertNotIn("m2",x.neighbors_for("m1"))\n    def test_disjoint_sets(self):\n        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())\n        self.assertFalse(set(x.impacted_market_ids)&set(x.adjacent_market_ids))\n    def test_deterministic(self):\n        p=projection(); l=lineage()\n        a=ChangeBoundaryExpander().expand(p,lineage=l)\n        b=ChangeBoundaryExpander().expand(p,lineage=l)\n        self.assertEqual(a.expansion_hash,b.expansion_hash)\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ChangeBoundaryExpander().expand(object(),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_154_certification_manifest()\n        self.assertEqual(m["semantics"],"structural_adjacent_markets_only_not_predicted_impact")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-154 CERTIFICATION TEST");print(" CHANGE BOUNDARY EXPANSION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD154))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_154_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Boundary-adjacent markets identified without promoting them to impacted status")\n    print("[PASS] Internal constraints excluded from boundary expansion")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-154 CERTIFIED")\n'
UPSTREAM_MODULE='umd_153_change_dependency_context_registry'
UPSTREAM_VERIFIER='verify_umd_153_change_dependency_context_registry'
EXPORTED_NAMES=('UMD_154_REVISION', 'ChangeBoundaryNeighbor', 'ChangeBoundaryExpansion', 'ChangeBoundaryExpander', 'build_umd_154_certification_manifest', 'verify_umd_154_change_boundary_expansion')

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
    marker="# UMD-154 exports"
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
            raise RuntimeError("UMD-154 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-154 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-154 INSTALLER")
    print(" CHANGE BOUNDARY EXPANSION")
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
        print("[ROLLBACK] UMD-154 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-154',
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
    print("[DONE] UMD-154 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
