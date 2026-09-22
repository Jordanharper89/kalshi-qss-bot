from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_156_CHANGE_MARKET_CONTEXT_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_156_change_market_context_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_156_change_market_context_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood,verify_umd_155_change_structural_neighborhood\n\nUMD_156_BUILD_ID="UMD-156"\nUMD_156_REVISION="UMD_156_CHANGE_MARKET_CONTEXT_REGISTRY_V1"\nUMD_156_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\nRELATION_TYPES=("impacted","boundary","family-neighbor","topology-neighbor")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeMarketContextRegistry:\n    neighborhoods:Tuple[ChangeStructuralNeighborhood,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    impacted_index:Mapping[str,Tuple[str,...]]\n    boundary_index:Mapping[str,Tuple[str,...]]\n    family_neighbor_index:Mapping[str,Tuple[str,...]]\n    topology_neighbor_index:Mapping[str,Tuple[str,...]]\n    change_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"neighborhoods",tuple(self.neighborhoods))\n        for name in (\n            "market_index","impacted_index","boundary_index",\n            "family_neighbor_index","topology_neighbor_index","change_index"\n        ):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.neighborhoods!=tuple(sorted(\n            self.neighborhoods,key=lambda n:(n.change_hash,n.neighborhood_hash)\n        )):\n            raise ValueError("neighborhoods must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_156_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-156")\n        required={n.neighborhood_hash for n in self.neighborhoods}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every neighborhood hash")\n\n    def changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def impacted_changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.impacted_index.get(market_id,())\n\n    def boundary_changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.boundary_index.get(market_id,())\n\n    def family_neighbor_changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.family_neighbor_index.get(market_id,())\n\n    def topology_neighbor_changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.topology_neighbor_index.get(market_id,())\n\n    def markets_for_change(self,change_hash:str)->Tuple[str,...]:\n        return self.change_index.get(change_hash,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "neighborhood_hashes":tuple(n.neighborhood_hash for n in self.neighborhoods),\n            "market_index":self.market_index,\n            "impacted_index":self.impacted_index,\n            "boundary_index":self.boundary_index,\n            "family_neighbor_index":self.family_neighbor_index,\n            "topology_neighbor_index":self.topology_neighbor_index,\n            "change_index":self.change_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeMarketContextRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        neighborhoods:Iterable[ChangeStructuralNeighborhood],\n        *,\n        lineage_factory,\n    )->ChangeMarketContextRegistry:\n        values=tuple(neighborhoods)\n        if any(not isinstance(n,ChangeStructuralNeighborhood) for n in values):\n            raise TypeError("neighborhoods must contain ChangeStructuralNeighborhood")\n        values=tuple(sorted(values,key=lambda n:(n.change_hash,n.neighborhood_hash)))\n\n        market={}\n        impacted={}\n        boundary={}\n        family={}\n        topology={}\n        change={}\n\n        for n in values:\n            change[n.change_hash]=n.all_market_ids\n            for market_id in n.all_market_ids:\n                market.setdefault(market_id,[]).append(n.change_hash)\n            for market_id in n.impacted_market_ids:\n                impacted.setdefault(market_id,[]).append(n.change_hash)\n            for market_id in n.boundary_market_ids:\n                boundary.setdefault(market_id,[]).append(n.change_hash)\n            for market_id in n.family_neighbor_ids:\n                family.setdefault(market_id,[]).append(n.change_hash)\n            for market_id in n.topology_neighbor_ids:\n                topology.setdefault(market_id,[]).append(n.change_hash)\n\n        for index in (market,impacted,boundary,family,topology):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        lineage=lineage_factory(tuple(n.neighborhood_hash for n in values))\n        return ChangeMarketContextRegistry(\n            values,market,impacted,boundary,family,topology,change,lineage\n        )\n\ndef build_umd_156_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_156_BUILD_ID,"revision":UMD_156_REVISION,\n        "schema_version":UMD_156_SCHEMA_VERSION,"upstream_builds":("UMD-155",),\n        "mode":"deterministic_read_only_change_market_context_registry",\n        "relation_types":RELATION_TYPES,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_156_change_market_context_registry()->bool:\n    if verify_umd_155_change_structural_neighborhood() is not True:\n        return False\n    m=build_umd_156_certification_manifest()\n    return m["build_id"]=="UMD-156" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood\nfrom qseries_v2.universal_market_discovery.umd_156_change_market_context_registry import *\n\nFIXED=datetime(2026,8,10,11,20,tzinfo=timezone.utc)\n\ndef neighborhood(change,impacted,boundary,family,topology):\n    all_ids=tuple(sorted(set(impacted+boundary+family+topology)))\n    relation={\n        "impacted":tuple(impacted),\n        "boundary":tuple(boundary),\n        "family-neighbor":tuple(family),\n        "topology-neighbor":tuple(topology),\n    }\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-155",revision="UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://156/155",),created_at=FIXED\n    )\n    return ChangeStructuralNeighborhood(\n        change,tuple(impacted),tuple(boundary),tuple(family),tuple(topology),\n        all_ids,relation,l\n    )\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-156",revision=UMD_156_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://156",),created_at=FIXED\n    )\n\nclass TestUMD156(unittest.TestCase):\n    def setUp(self):\n        self.c1="1"*64; self.c2="2"*64\n        self.n1=neighborhood(self.c1,("m1",),("m2",),("m3",),("m4",))\n        self.n2=neighborhood(self.c2,("m2",),(),("m5",),("m4",))\n        self.r=ChangeMarketContextRegistryBuilder().build((self.n2,self.n1),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_156_change_market_context_registry())\n    def test_market_query(self):\n        self.assertEqual(self.r.changes_for_market("m4"),(self.c1,self.c2))\n    def test_impacted_query(self):\n        self.assertEqual(self.r.impacted_changes_for_market("m2"),(self.c2,))\n    def test_boundary_query(self):\n        self.assertEqual(self.r.boundary_changes_for_market("m2"),(self.c1,))\n    def test_family_query(self):\n        self.assertEqual(self.r.family_neighbor_changes_for_market("m3"),(self.c1,))\n    def test_topology_query(self):\n        self.assertEqual(self.r.topology_neighbor_changes_for_market("m4"),(self.c1,self.c2))\n    def test_change_query(self):\n        self.assertEqual(self.r.markets_for_change(self.c1),("m1","m2","m3","m4"))\n    def test_unknown(self):\n        self.assertEqual(self.r.changes_for_market("missing"),())\n    def test_deterministic(self):\n        x=ChangeMarketContextRegistryBuilder().build((self.n1,self.n2),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ChangeMarketContextRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(x.neighborhoods,())\n    def test_bad_neighborhood(self):\n        with self.assertRaises(TypeError):\n            ChangeMarketContextRegistryBuilder().build((object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_156_certification_manifest()\n        self.assertEqual(m["relation_types"],RELATION_TYPES)\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-156 CERTIFICATION TEST");print(" CHANGE MARKET CONTEXT REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD156))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_156_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Change market context queries by impacted, boundary, family, and topology relation certified")\n    print("[PASS] Complete structural neighborhood remains read-only and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-156 CERTIFIED")\n'
UPSTREAM_MODULE='umd_155_change_structural_neighborhood'
UPSTREAM_VERIFIER='verify_umd_155_change_structural_neighborhood'
EXPORTED_NAMES=('UMD_156_REVISION', 'RELATION_TYPES', 'ChangeMarketContextRegistry', 'ChangeMarketContextRegistryBuilder', 'build_umd_156_certification_manifest', 'verify_umd_156_change_market_context_registry')

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
    marker="# UMD-156 exports"
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
            raise RuntimeError("UMD-156 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-156 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-156 INSTALLER")
    print(" CHANGE MARKET CONTEXT REGISTRY")
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
        print("[ROLLBACK] UMD-156 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-156',
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
    print("[DONE] UMD-156 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
