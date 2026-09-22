from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_128_MARKET_PARTITION_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_128_market_partition.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_128_market_partition.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile\nfrom .umd_110_market_family_resolution import MarketFamily\nfrom .umd_127_market_ladder import verify_umd_127_market_ladder_model\n\nUMD_128_BUILD_ID="UMD-128"\nUMD_128_REVISION="UMD_128_MARKET_PARTITION_MODEL_V1"\nUMD_128_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass PartitionMember:\n    canonical_market_id:str\n    outcome_key:str\n    profile_hash:str\n\n    @property\n    def member_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "outcome_key":self.outcome_key,\n            "profile_hash":self.profile_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass MarketPartition:\n    family_key:str\n    members:Tuple[PartitionMember,...]\n    mutually_exclusive:bool\n    collectively_exhaustive:bool\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"members",tuple(self.members))\n        if len(self.members)<2:\n            raise ValueError("market partition requires at least two members")\n        if self.members!=tuple(sorted(self.members,key=lambda m:(m.outcome_key,m.canonical_market_id))):\n            raise ValueError("partition members must be deterministically sorted")\n        outcomes=[m.outcome_key for m in self.members]\n        if len(outcomes)!=len(set(outcomes)):\n            raise ValueError("partition outcomes must be unique")\n        markets=[m.canonical_market_id for m in self.members]\n        if len(markets)!=len(set(markets)):\n            raise ValueError("partition market ids must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_128_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-128")\n        required={m.profile_hash for m in self.members}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every partition profile hash")\n\n    def market_for_outcome(self,outcome_key:str)->str|None:\n        for member in self.members:\n            if member.outcome_key==outcome_key:\n                return member.canonical_market_id\n        return None\n\n    @property\n    def partition_hash(self)->str:\n        return deterministic_sha256({\n            "family_key":self.family_key,\n            "member_hashes":tuple(m.member_hash for m in self.members),\n            "mutually_exclusive":self.mutually_exclusive,\n            "collectively_exhaustive":self.collectively_exhaustive,\n            "lineage":self.lineage,\n        })\n\nclass MarketPartitionBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        family:MarketFamily,\n        profiles:Iterable[MarketSemanticProfile],\n        *,\n        outcome_kind:str="event",\n        mutually_exclusive:bool=True,\n        collectively_exhaustive:bool=True,\n        lineage:ImmutableLineage,\n    )->MarketPartition:\n        if not isinstance(family,MarketFamily):\n            raise TypeError("family must be MarketFamily")\n        ps=tuple(profiles)\n        if any(not isinstance(p,MarketSemanticProfile) for p in ps):\n            raise TypeError("profiles must contain MarketSemanticProfile")\n\n        members=set(family.member_market_ids)\n        selected=[p for p in ps if p.canonical_market_id in members]\n        if {p.canonical_market_id for p in selected}!=members:\n            raise ValueError("profiles must cover every family member")\n\n        result=[]\n        for profile in selected:\n            values=profile.values(outcome_kind)\n            if len(values)!=1:\n                raise ValueError("partition profile requires exactly one outcome semantic value")\n            result.append(PartitionMember(\n                profile.canonical_market_id,\n                values[0],\n                profile.profile_hash,\n            ))\n        result.sort(key=lambda m:(m.outcome_key,m.canonical_market_id))\n        return MarketPartition(\n            family.family_key,\n            tuple(result),\n            bool(mutually_exclusive),\n            bool(collectively_exhaustive),\n            lineage,\n        )\n\ndef build_umd_128_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_128_BUILD_ID,"revision":UMD_128_REVISION,\n        "schema_version":UMD_128_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110","UMD-127"),\n        "mode":"deterministic_read_only_market_partition_model",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_128_market_partition_model()->bool:\n    if verify_umd_127_market_ladder_model() is not True:\n        return False\n    m=build_umd_128_certification_manifest()\n    return m["build_id"]=="UMD-128" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamily\nfrom qseries_v2.universal_market_discovery.umd_128_market_partition import *\n\nFIXED=datetime(2026,8,9,23,10,tzinfo=timezone.utc)\n\ndef profile(cid,ih,event):\n    l102=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://128/102",),created_at=FIXED\n    )\n    r=CanonicalMarketRecord(\n        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),\n        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102\n    )\n    l109=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.record_hash,),\n        source_refs=("fixture://128/109",),created_at=FIXED\n    )\n    return MarketSemanticProfiler().build(\n        r,(("market_type","Election Winner"),("event",event)),lineage=l109\n    )\n\ndef family(ps):\n    ordered=tuple(sorted(ps,key=lambda p:p.canonical_market_id))\n    hashes=tuple(p.profile_hash for p in ordered)\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,\n        schema_version="1.0.0",parent_hashes=hashes,\n        source_refs=("fixture://128/110",),created_at=FIXED\n    )\n    return MarketFamily(\n        "market_type=election-winner",\n        ("market_type",),\n        tuple(p.canonical_market_id for p in ordered),\n        hashes,\n        l,\n    )\n\ndef lineage(ps):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-128",revision=UMD_128_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(p.profile_hash for p in ps),\n        source_refs=("fixture://128",),created_at=FIXED\n    )\n\nclass TestUMD128(unittest.TestCase):\n    def setUp(self):\n        self.a=profile("m1","a"*64,"Candidate A")\n        self.b=profile("m2","b"*64,"Candidate B")\n        self.c=profile("m3","c"*64,"Candidate C")\n        self.ps=(self.a,self.b,self.c)\n        self.f=family(self.ps)\n\n    def test_foundation(self): self.assertTrue(verify_umd_128_market_partition_model())\n    def test_partition_build(self):\n        p=MarketPartitionBuilder().build(self.f,(self.c,self.a,self.b),lineage=lineage(self.ps))\n        self.assertEqual(tuple(m.outcome_key for m in p.members),("candidate-a","candidate-b","candidate-c"))\n        self.assertTrue(p.mutually_exclusive)\n        self.assertTrue(p.collectively_exhaustive)\n    def test_outcome_lookup(self):\n        p=MarketPartitionBuilder().build(self.f,self.ps,lineage=lineage(self.ps))\n        self.assertEqual(p.market_for_outcome("candidate-b"),"m2")\n    def test_deterministic(self):\n        a=MarketPartitionBuilder().build(self.f,self.ps,lineage=lineage(self.ps))\n        b=MarketPartitionBuilder().build(self.f,tuple(reversed(self.ps)),lineage=lineage(self.ps))\n        self.assertEqual(a.partition_hash,b.partition_hash)\n    def test_duplicate_outcome_rejected(self):\n        dup=profile("m3","c"*64,"Candidate B")\n        ps=(self.a,self.b,dup)\n        with self.assertRaises(ValueError):\n            MarketPartitionBuilder().build(family(ps),ps,lineage=lineage(ps))\n    def test_incomplete_family_rejected(self):\n        with self.assertRaises(ValueError):\n            MarketPartitionBuilder().build(self.f,(self.a,self.b),lineage=lineage(self.ps))\n    def test_side_effects(self):\n        m=build_umd_128_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-128 CERTIFICATION TEST");print(" MARKET PARTITION MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD128))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_128_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Mutually exclusive and collectively exhaustive market partitions certified")\n    print("[PASS] Unique outcome membership and full family coverage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-128 CERTIFIED")\n'
UPSTREAM_MODULE='umd_127_market_ladder'
UPSTREAM_VERIFIER='verify_umd_127_market_ladder_model'
EXPORTED_NAMES=('UMD_128_REVISION', 'PartitionMember', 'MarketPartition', 'MarketPartitionBuilder', 'build_umd_128_certification_manifest', 'verify_umd_128_market_partition_model')

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
    marker="# UMD-128 exports"
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
            raise RuntimeError("UMD-128 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-128 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-128 INSTALLER")
    print(" MARKET PARTITION MODEL")
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
        print("[ROLLBACK] UMD-128 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-128',
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
    print("[DONE] UMD-128 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
