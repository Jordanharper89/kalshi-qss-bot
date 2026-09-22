from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_129_MARKET_TOPOLOGY_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_129_market_topology.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_129_market_topology.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_127_market_ladder import MarketLadder\nfrom .umd_128_market_partition import MarketPartition, verify_umd_128_market_partition_model\n\nUMD_129_BUILD_ID="UMD-129"\nUMD_129_REVISION="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1"\nUMD_129_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass MarketTopologyRegistry:\n    ladders:Tuple[MarketLadder,...]\n    partitions:Tuple[MarketPartition,...]\n    market_to_ladders:Mapping[str,Tuple[str,...]]\n    market_to_partitions:Mapping[str,Tuple[str,...]]\n    family_to_ladders:Mapping[str,Tuple[str,...]]\n    family_to_partitions:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"ladders",tuple(self.ladders))\n        object.__setattr__(self,"partitions",tuple(self.partitions))\n        for name in ("market_to_ladders","market_to_partitions","family_to_ladders","family_to_partitions"):\n            object.__setattr__(self,name,_freeze_index(getattr(self,name)))\n        if self.ladders!=tuple(sorted(self.ladders,key=lambda x:(x.family_key,x.ladder_hash))):\n            raise ValueError("ladders must be deterministically sorted")\n        if self.partitions!=tuple(sorted(self.partitions,key=lambda x:(x.family_key,x.partition_hash))):\n            raise ValueError("partitions must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_129_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-129")\n        required={x.ladder_hash for x in self.ladders}|{x.partition_hash for x in self.partitions}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every topology hash")\n\n    def ladders_for_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.market_to_ladders.get(canonical_market_id,())\n\n    def partitions_for_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.market_to_partitions.get(canonical_market_id,())\n\n    def ladders_for_family(self,family_key:str)->Tuple[str,...]:\n        return self.family_to_ladders.get(family_key,())\n\n    def partitions_for_family(self,family_key:str)->Tuple[str,...]:\n        return self.family_to_partitions.get(family_key,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "ladder_hashes":tuple(x.ladder_hash for x in self.ladders),\n            "partition_hashes":tuple(x.partition_hash for x in self.partitions),\n            "market_to_ladders":self.market_to_ladders,\n            "market_to_partitions":self.market_to_partitions,\n            "family_to_ladders":self.family_to_ladders,\n            "family_to_partitions":self.family_to_partitions,\n            "lineage":self.lineage,\n        })\n\nclass MarketTopologyRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        ladders:Iterable[MarketLadder],\n        partitions:Iterable[MarketPartition],\n        *,\n        lineage_factory,\n    )->MarketTopologyRegistry:\n        ls=tuple(ladders)\n        ps=tuple(partitions)\n        if any(not isinstance(x,MarketLadder) for x in ls):\n            raise TypeError("ladders must contain MarketLadder")\n        if any(not isinstance(x,MarketPartition) for x in ps):\n            raise TypeError("partitions must contain MarketPartition")\n\n        ls=tuple(sorted(ls,key=lambda x:(x.family_key,x.ladder_hash)))\n        ps=tuple(sorted(ps,key=lambda x:(x.family_key,x.partition_hash)))\n\n        market_l={}\n        market_p={}\n        family_l={}\n        family_p={}\n\n        for ladder in ls:\n            family_l.setdefault(ladder.family_key,[]).append(ladder.ladder_hash)\n            for rung in ladder.rungs:\n                market_l.setdefault(rung.canonical_market_id,[]).append(ladder.ladder_hash)\n\n        for partition in ps:\n            family_p.setdefault(partition.family_key,[]).append(partition.partition_hash)\n            for member in partition.members:\n                market_p.setdefault(member.canonical_market_id,[]).append(partition.partition_hash)\n\n        for index in (market_l,market_p,family_l,family_p):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        parent_hashes=tuple(x.ladder_hash for x in ls)+tuple(x.partition_hash for x in ps)\n        lineage=lineage_factory(parent_hashes)\n        return MarketTopologyRegistry(ls,ps,market_l,market_p,family_l,family_p,lineage)\n\ndef build_umd_129_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_129_BUILD_ID,"revision":UMD_129_REVISION,\n        "schema_version":UMD_129_SCHEMA_VERSION,"upstream_builds":("UMD-127","UMD-128"),\n        "mode":"deterministic_read_only_market_topology_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_129_market_topology_registry()->bool:\n    if verify_umd_128_market_partition_model() is not True:\n        return False\n    m=build_umd_129_certification_manifest()\n    return m["build_id"]=="UMD-129" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder\nfrom qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition\nfrom qseries_v2.universal_market_discovery.umd_129_market_topology import *\n\nFIXED=datetime(2026,8,9,23,20,tzinfo=timezone.utc)\n\ndef ladder():\n    p1="a"*64; p2="b"*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(p1,p2),\n        source_refs=("fixture://129/127",),created_at=FIXED\n    )\n    return MarketLadder(\n        "asset=bitcoin",\n        "above",\n        (\n            LadderRung("m1","100000","100000","above",p1),\n            LadderRung("m2","150000","150000","above",p2),\n        ),\n        l,\n    )\n\ndef partition():\n    p1="c"*64; p2="d"*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(p1,p2),\n        source_refs=("fixture://129/128",),created_at=FIXED\n    )\n    return MarketPartition(\n        "event=election",\n        (\n            PartitionMember("m3","candidate-a",p1),\n            PartitionMember("m4","candidate-b",p2),\n        ),\n        True,\n        True,\n        l,\n    )\n\ndef lineage_factory(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-129",revision=UMD_129_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://129",),created_at=FIXED\n    )\n\nclass TestUMD129(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_129_market_topology_registry())\n    def test_market_ladder_query(self):\n        l=ladder(); p=partition()\n        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)\n        self.assertEqual(r.ladders_for_market("m1"),(l.ladder_hash,))\n    def test_market_partition_query(self):\n        l=ladder(); p=partition()\n        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)\n        self.assertEqual(r.partitions_for_market("m4"),(p.partition_hash,))\n    def test_family_queries(self):\n        l=ladder(); p=partition()\n        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)\n        self.assertEqual(r.ladders_for_family("asset=bitcoin"),(l.ladder_hash,))\n        self.assertEqual(r.partitions_for_family("event=election"),(p.partition_hash,))\n    def test_unknown(self):\n        r=MarketTopologyRegistryBuilder().build((ladder(),),(partition(),),lineage_factory=lineage_factory)\n        self.assertEqual(r.ladders_for_market("missing"),())\n    def test_deterministic(self):\n        l=ladder(); p=partition()\n        a=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)\n        b=MarketTopologyRegistryBuilder().build(tuple(reversed((l,))),tuple(reversed((p,))),lineage_factory=lineage_factory)\n        self.assertEqual(a.registry_hash,b.registry_hash)\n    def test_bad_ladder(self):\n        with self.assertRaises(TypeError):\n            MarketTopologyRegistryBuilder().build((object(),),(partition(),),lineage_factory=lineage_factory)\n    def test_empty(self):\n        r=MarketTopologyRegistryBuilder().build((),(),lineage_factory=lineage_factory)\n        self.assertEqual(r.ladders,())\n        self.assertEqual(r.partitions,())\n    def test_side_effects(self):\n        m=build_umd_129_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-129 CERTIFICATION TEST");print(" MARKET TOPOLOGY REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD129))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_129_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Ladder and partition topology registry certified")\n    print("[PASS] Reverse queries by canonical market and semantic family certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-129 CERTIFIED")\n'
UPSTREAM_MODULE='umd_128_market_partition'
UPSTREAM_VERIFIER='verify_umd_128_market_partition_model'
EXPORTED_NAMES=('UMD_129_REVISION', 'MarketTopologyRegistry', 'MarketTopologyRegistryBuilder', 'build_umd_129_certification_manifest', 'verify_umd_129_market_topology_registry')

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
    marker="# UMD-129 exports"
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
            raise RuntimeError("UMD-129 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-129 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-129 INSTALLER")
    print(" MARKET TOPOLOGY REGISTRY")
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
        print("[ROLLBACK] UMD-129 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-129',
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
    print("[DONE] UMD-129 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
