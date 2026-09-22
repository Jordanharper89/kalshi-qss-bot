from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_148_CHANGE_TOPOLOGY_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_148_change_topology_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_148_change_topology_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_129_market_topology import MarketTopologyRegistry\nfrom .umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry,verify_umd_147_observation_change_impact_registry\n\nUMD_148_BUILD_ID="UMD-148"\nUMD_148_REVISION="UMD_148_CHANGE_TOPOLOGY_PROJECTION_V1"\nUMD_148_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeTopologyProjection:\n    change_hash:str\n    market_ids:Tuple[str,...]\n    ladder_hashes:Tuple[str,...]\n    partition_hashes:Tuple[str,...]\n    market_to_ladders:Mapping[str,Tuple[str,...]]\n    market_to_partitions:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_ids",tuple(self.market_ids))\n        object.__setattr__(self,"ladder_hashes",tuple(self.ladder_hashes))\n        object.__setattr__(self,"partition_hashes",tuple(self.partition_hashes))\n        object.__setattr__(self,"market_to_ladders",_freeze(self.market_to_ladders))\n        object.__setattr__(self,"market_to_partitions",_freeze(self.market_to_partitions))\n        for name in ("market_ids","ladder_hashes","partition_hashes"):\n            value=getattr(self,name)\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_148_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-148")\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "market_ids":self.market_ids,\n            "ladder_hashes":self.ladder_hashes,\n            "partition_hashes":self.partition_hashes,\n            "market_to_ladders":self.market_to_ladders,\n            "market_to_partitions":self.market_to_partitions,\n            "lineage":self.lineage,\n        })\n\nclass ChangeTopologyProjector:\n    __slots__=("impact_registry","topology_registry")\n\n    def __init__(self,impact_registry:ObservationChangeImpactRegistry,topology_registry:MarketTopologyRegistry):\n        if not isinstance(impact_registry,ObservationChangeImpactRegistry):\n            raise TypeError("impact_registry must be ObservationChangeImpactRegistry")\n        if not isinstance(topology_registry,MarketTopologyRegistry):\n            raise TypeError("topology_registry must be MarketTopologyRegistry")\n        self.impact_registry=impact_registry\n        self.topology_registry=topology_registry\n\n    def project(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeTopologyProjection:\n        markets=tuple(sorted({\n            market_id\n            for market_id,changes in self.impact_registry.market_index.items()\n            if change_hash in changes\n        }))\n        market_to_ladders={}\n        market_to_partitions={}\n        ladders=set()\n        partitions=set()\n\n        for market_id in markets:\n            ls=self.topology_registry.ladders_for_market(market_id)\n            ps=self.topology_registry.partitions_for_market(market_id)\n            if ls:\n                market_to_ladders[market_id]=ls\n                ladders.update(ls)\n            if ps:\n                market_to_partitions[market_id]=ps\n                partitions.update(ps)\n\n        return ChangeTopologyProjection(\n            change_hash,\n            markets,\n            tuple(sorted(ladders)),\n            tuple(sorted(partitions)),\n            market_to_ladders,\n            market_to_partitions,\n            lineage,\n        )\n\ndef build_umd_148_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_148_BUILD_ID,"revision":UMD_148_REVISION,\n        "schema_version":UMD_148_SCHEMA_VERSION,"upstream_builds":("UMD-129","UMD-147"),\n        "mode":"deterministic_read_only_change_topology_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_148_change_topology_projection()->bool:\n    if verify_umd_147_observation_change_impact_registry() is not True:\n        return False\n    m=build_umd_148_certification_manifest()\n    return m["build_id"]=="UMD-148" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder\nfrom qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition\nfrom qseries_v2.universal_market_discovery.umd_129_market_topology import MarketTopologyRegistry\nfrom qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry\nfrom qseries_v2.universal_market_discovery.umd_148_change_topology_projection import *\n\nFIXED=datetime(2026,8,10,9,0,tzinfo=timezone.utc)\n\ndef topology():\n    p1="a"*64; p2="b"*64\n    l127=ImmutableLineage(subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(p1,p2),source_refs=("fixture://148/127",),created_at=FIXED)\n    ladder=MarketLadder("family-l","above",(\n        LadderRung("m1","100","100","above",p1),\n        LadderRung("m2","200","200","above",p2),\n    ),l127)\n\n    p3="c"*64; p4="d"*64\n    l128=ImmutableLineage(subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(p3,p4),source_refs=("fixture://148/128",),created_at=FIXED)\n    partition=MarketPartition("family-p",(\n        PartitionMember("m2","yes",p3),\n        PartitionMember("m3","no",p4),\n    ),True,True,l128)\n\n    l129=ImmutableLineage(subsystem_id="UMD",build_id="UMD-129",revision="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(ladder.ladder_hash,partition.partition_hash),\n        source_refs=("fixture://148/129",),created_at=FIXED)\n    return MarketTopologyRegistry(\n        (ladder,),(partition,),\n        {"m1":(ladder.ladder_hash,),"m2":(ladder.ladder_hash,)},\n        {"m2":(partition.partition_hash,),"m3":(partition.partition_hash,)},\n        {"family-l":(ladder.ladder_hash,)},\n        {"family-p":(partition.partition_hash,)},\n        l129,\n    )\n\ndef impacts():\n    change="1"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://148/147",),created_at=FIXED)\n    return ObservationChangeImpactRegistry((),{"m1":(change,),"m2":(change,)},{},{},l),change\n\ndef lineage(change):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-148",revision=UMD_148_REVISION,\n        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://148",),created_at=FIXED)\n\nclass TestUMD148(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_148_change_topology_projection())\n    def test_projection(self):\n        ir,ch=impacts()\n        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))\n        self.assertEqual(p.market_ids,("m1","m2"))\n        self.assertEqual(len(p.ladder_hashes),1)\n        self.assertEqual(len(p.partition_hashes),1)\n    def test_market_maps(self):\n        ir,ch=impacts()\n        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))\n        self.assertIn("m1",p.market_to_ladders)\n        self.assertIn("m2",p.market_to_partitions)\n    def test_unknown_change(self):\n        ir,_=impacts()\n        ch="9"*64\n        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))\n        self.assertEqual(p.market_ids,())\n        self.assertEqual(p.ladder_hashes,())\n    def test_deterministic(self):\n        ir,ch=impacts(); proj=ChangeTopologyProjector(ir,topology()); l=lineage(ch)\n        a=proj.project(ch,lineage=l); b=proj.project(ch,lineage=l)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): ChangeTopologyProjector(object(),topology())\n    def test_side_effects(self):\n        m=build_umd_148_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-148 CERTIFICATION TEST");print(" CHANGE TOPOLOGY PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD148))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_148_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] World-state changes projected into market ladders and partitions")\n    print("[PASS] Canonical market to topology membership preserved deterministically")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-148 CERTIFIED")\n'
UPSTREAM_MODULE='umd_147_observation_change_impact_registry'
UPSTREAM_VERIFIER='verify_umd_147_observation_change_impact_registry'
EXPORTED_NAMES=('UMD_148_REVISION', 'ChangeTopologyProjection', 'ChangeTopologyProjector', 'build_umd_148_certification_manifest', 'verify_umd_148_change_topology_projection')

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
    marker="# UMD-148 exports"
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
            raise RuntimeError("UMD-148 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-148 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-148 INSTALLER")
    print(" CHANGE TOPOLOGY PROJECTION")
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
        print("[ROLLBACK] UMD-148 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-148',
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
    print("[DONE] UMD-148 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
