from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_155_change_structural_neighborhood.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_155_change_structural_neighborhood.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_111_semantic_registry import SemanticRegistry\nfrom .umd_129_market_topology import MarketTopologyRegistry\nfrom .umd_154_change_boundary_expansion import ChangeBoundaryExpansion,verify_umd_154_change_boundary_expansion\n\nUMD_155_BUILD_ID="UMD-155"\nUMD_155_REVISION="UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_V1"\nUMD_155_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeStructuralNeighborhood:\n    change_hash:str\n    impacted_market_ids:Tuple[str,...]\n    boundary_market_ids:Tuple[str,...]\n    family_neighbor_ids:Tuple[str,...]\n    topology_neighbor_ids:Tuple[str,...]\n    all_market_ids:Tuple[str,...]\n    relation_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in (\n            "impacted_market_ids","boundary_market_ids","family_neighbor_ids",\n            "topology_neighbor_ids","all_market_ids"\n        ):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        object.__setattr__(self,"relation_index",_freeze(self.relation_index))\n        expected=tuple(sorted(set(\n            self.impacted_market_ids+self.boundary_market_ids+\n            self.family_neighbor_ids+self.topology_neighbor_ids\n        )))\n        if self.all_market_ids!=expected:\n            raise ValueError("all_market_ids must equal union of neighborhood sets")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_155_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-155")\n        if self.change_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include change hash")\n\n    def markets_for_relation(self,relation:str)->Tuple[str,...]:\n        return self.relation_index.get(relation,())\n\n    @property\n    def neighborhood_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "impacted_market_ids":self.impacted_market_ids,\n            "boundary_market_ids":self.boundary_market_ids,\n            "family_neighbor_ids":self.family_neighbor_ids,\n            "topology_neighbor_ids":self.topology_neighbor_ids,\n            "all_market_ids":self.all_market_ids,\n            "relation_index":self.relation_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeStructuralNeighborhoodBuilder:\n    __slots__=("semantic_registry","topology_registry")\n\n    def __init__(self,semantic_registry:SemanticRegistry,topology_registry:MarketTopologyRegistry):\n        if not isinstance(semantic_registry,SemanticRegistry):\n            raise TypeError("semantic_registry must be SemanticRegistry")\n        if not isinstance(topology_registry,MarketTopologyRegistry):\n            raise TypeError("topology_registry must be MarketTopologyRegistry")\n        self.semantic_registry=semantic_registry\n        self.topology_registry=topology_registry\n\n    def build(\n        self,\n        expansion:ChangeBoundaryExpansion,\n        *,\n        lineage:ImmutableLineage,\n    )->ChangeStructuralNeighborhood:\n        if not isinstance(expansion,ChangeBoundaryExpansion):\n            raise TypeError("expansion must be ChangeBoundaryExpansion")\n\n        seeds=set(expansion.impacted_market_ids)|set(expansion.adjacent_market_ids)\n        family_neighbors=set()\n        topology_neighbors=set()\n\n        # Same semantic-family membership.\n        for family in self.semantic_registry.families:\n            if seeds.intersection(family.member_market_ids):\n                family_neighbors.update(family.member_market_ids)\n\n        # Same ladder or partition membership.\n        for market_id in sorted(seeds):\n            ladder_hashes=self.topology_registry.ladders_for_market(market_id)\n            partition_hashes=self.topology_registry.partitions_for_market(market_id)\n            for ladder in self.topology_registry.ladders:\n                if ladder.ladder_hash in ladder_hashes:\n                    topology_neighbors.update(r.canonical_market_id for r in ladder.rungs)\n            for partition in self.topology_registry.partitions:\n                if partition.partition_hash in partition_hashes:\n                    topology_neighbors.update(m.canonical_market_id for m in partition.members)\n\n        impacted=set(expansion.impacted_market_ids)\n        boundary=set(expansion.adjacent_market_ids)\n        family_neighbors.difference_update(impacted|boundary)\n        topology_neighbors.difference_update(impacted|boundary)\n\n        relation_index={\n            "impacted":tuple(sorted(impacted)),\n            "boundary":tuple(sorted(boundary)),\n            "family-neighbor":tuple(sorted(family_neighbors)),\n            "topology-neighbor":tuple(sorted(topology_neighbors)),\n        }\n        all_ids=tuple(sorted(impacted|boundary|family_neighbors|topology_neighbors))\n\n        return ChangeStructuralNeighborhood(\n            expansion.change_hash,\n            tuple(sorted(impacted)),\n            tuple(sorted(boundary)),\n            tuple(sorted(family_neighbors)),\n            tuple(sorted(topology_neighbors)),\n            all_ids,\n            relation_index,\n            lineage,\n        )\n\ndef build_umd_155_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_155_BUILD_ID,"revision":UMD_155_REVISION,\n        "schema_version":UMD_155_SCHEMA_VERSION,"upstream_builds":("UMD-111","UMD-129","UMD-154"),\n        "mode":"deterministic_read_only_change_structural_neighborhood",\n        "semantics":"structural_context_only_no_predicted_impact",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_155_change_structural_neighborhood()->bool:\n    if verify_umd_154_change_boundary_expansion() is not True:\n        return False\n    m=build_umd_155_certification_manifest()\n    return m["build_id"]=="UMD-155" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import MarketSemanticProfile,SemanticFact\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import MarketFamily\nfrom qseries_v2.universal_market_discovery.umd_111_semantic_registry import SemanticRegistry\nfrom qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder\nfrom qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition\nfrom qseries_v2.universal_market_discovery.umd_129_market_topology import MarketTopologyRegistry\nfrom qseries_v2.universal_market_discovery.umd_154_change_boundary_expansion import ChangeBoundaryNeighbor,ChangeBoundaryExpansion\nfrom qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import *\n\nFIXED=datetime(2026,8,10,11,10,tzinfo=timezone.utc)\nCHANGE="1"*64\n\ndef semantic_registry():\n    ph1="a"*64; ph2="b"*64; ph3="c"*64\n    def prof(mid,ph,value):\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision="UMD_109_MARKET_SEMANTIC_PROFILE_V1",\n            schema_version="1.0.0",parent_hashes=(ph,),source_refs=("fixture://155/109",),created_at=FIXED)\n        return MarketSemanticProfile(mid,ph,(SemanticFact("asset",value,value.lower()),),l)\n    p1=prof("m1",ph1,"Bitcoin"); p2=prof("m2",ph2,"Bitcoin"); p5=prof("m5",ph3,"Bitcoin")\n    lf=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,p5.profile_hash),\n        source_refs=("fixture://155/110",),created_at=FIXED)\n    fam=MarketFamily("asset=bitcoin",("asset",),("m1","m2","m5"),\n        tuple(sorted((p1.profile_hash,p2.profile_hash,p5.profile_hash))),lf)\n    l111=ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision="UMD_111_SEMANTIC_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,p5.profile_hash,fam.family_hash),\n        source_refs=("fixture://155/111",),created_at=FIXED)\n    return SemanticRegistry((p1,p2,p5),(fam,),{"asset=bitcoin":("m1","m2","m5")},{"asset=bitcoin":("m1","m2","m5")},l111)\n\ndef topology_registry():\n    p1="d"*64; p2="e"*64; p3="f"*64\n    l127=ImmutableLineage(subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(p1,p2,p3),source_refs=("fixture://155/127",),created_at=FIXED)\n    ladder=MarketLadder("family-l","above",(\n        LadderRung("m1","100","100","above",p1),\n        LadderRung("m3","200","200","above",p2),\n        LadderRung("m6","300","300","above",p3),\n    ),l127)\n\n    q1="1"*64; q2="2"*64\n    l128=ImmutableLineage(subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(q1,q2),source_refs=("fixture://155/128",),created_at=FIXED)\n    partition=MarketPartition("family-p",(\n        PartitionMember("m7","no",q2),\n        PartitionMember("m2","yes",q1),\n    ),True,True,l128)\n\n    l129=ImmutableLineage(subsystem_id="UMD",build_id="UMD-129",revision="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(ladder.ladder_hash,partition.partition_hash),\n        source_refs=("fixture://155/129",),created_at=FIXED)\n    return MarketTopologyRegistry(\n        (ladder,),(partition,),\n        {"m1":(ladder.ladder_hash,),"m3":(ladder.ladder_hash,),"m6":(ladder.ladder_hash,)},\n        {"m2":(partition.partition_hash,),"m7":(partition.partition_hash,)},\n        {"family-l":(ladder.ladder_hash,)},\n        {"family-p":(partition.partition_hash,)},\n        l129,\n    )\n\ndef expansion():\n    n=ChangeBoundaryNeighbor("m1","m3","implies","basis:x","9"*64)\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-154",revision="UMD_154_CHANGE_BOUNDARY_EXPANSION_V1",\n        schema_version="1.0.0",parent_hashes=(CHANGE,),source_refs=("fixture://155/154",),created_at=FIXED)\n    return ChangeBoundaryExpansion(CHANGE,("m1","m2"),("m3",),(n,),l)\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-155",revision=UMD_155_REVISION,\n        schema_version="1.0.0",parent_hashes=(CHANGE,),source_refs=("fixture://155",),created_at=FIXED)\n\nclass TestUMD155(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_155_change_structural_neighborhood())\n    def test_neighborhood(self):\n        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())\n        self.assertEqual(n.impacted_market_ids,("m1","m2"))\n        self.assertEqual(n.boundary_market_ids,("m3",))\n        self.assertEqual(n.family_neighbor_ids,("m5",))\n        self.assertEqual(n.topology_neighbor_ids,("m6","m7"))\n        self.assertEqual(n.all_market_ids,("m1","m2","m3","m5","m6","m7"))\n    def test_relation_query(self):\n        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())\n        self.assertEqual(n.markets_for_relation("topology-neighbor"),("m6","m7"))\n    def test_seed_not_repeated_as_neighbor(self):\n        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())\n        self.assertFalse(set(n.family_neighbor_ids)&set(n.impacted_market_ids+n.boundary_market_ids))\n        self.assertFalse(set(n.topology_neighbor_ids)&set(n.impacted_market_ids+n.boundary_market_ids))\n    def test_deterministic(self):\n        b=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()); e=expansion(); l=lineage()\n        a=b.build(e,lineage=l); c=b.build(e,lineage=l)\n        self.assertEqual(a.neighborhood_hash,c.neighborhood_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ChangeStructuralNeighborhoodBuilder(object(),topology_registry())\n    def test_bad_expansion(self):\n        with self.assertRaises(TypeError):\n            ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(object(),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_155_certification_manifest()\n        self.assertEqual(m["semantics"],"structural_context_only_no_predicted_impact")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-155 CERTIFICATION TEST");print(" CHANGE STRUCTURAL NEIGHBORHOOD");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD155))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_155_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Impacted, boundary, family-neighbor, and topology-neighbor markets certified")\n    print("[PASS] Structural neighborhood does not promote context markets to impacted status")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-155 CERTIFIED")\n'
UPSTREAM_MODULE='umd_154_change_boundary_expansion'
UPSTREAM_VERIFIER='verify_umd_154_change_boundary_expansion'
EXPORTED_NAMES=('UMD_155_REVISION', 'ChangeStructuralNeighborhood', 'ChangeStructuralNeighborhoodBuilder', 'build_umd_155_certification_manifest', 'verify_umd_155_change_structural_neighborhood')

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
    marker="# UMD-155 exports"
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
            raise RuntimeError("UMD-155 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-155 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-155 INSTALLER")
    print(" CHANGE STRUCTURAL NEIGHBORHOOD")
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
        print("[ROLLBACK] UMD-155 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-155',
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
    print("[DONE] UMD-155 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
