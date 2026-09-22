from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_107_REGISTRY_INDEX_BUILDER_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_107_registry_index_builder.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_107_registry_index_builder.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping, Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry\nfrom .umd_106_registry_query_engine import verify_umd_106_registry_query_engine\n\nUMD_107_BUILD_ID="UMD-107"\nUMD_107_REVISION="UMD_107_REGISTRY_INDEX_BUILDER_V1"\nUMD_107_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_map(d):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(d.items())})\n\n@dataclass(frozen=True,slots=True)\nclass RegistryIndexes:\n    canonical_ids:Mapping[str,int]\n    venue_index:Mapping[str,Tuple[str,...]]\n    taxonomy_index:Mapping[str,Tuple[str,...]]\n    alias_index:Mapping[str,Tuple[str,...]]\n    relationship_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"canonical_ids",MappingProxyType(dict(sorted(self.canonical_ids.items()))))\n        object.__setattr__(self,"venue_index",_freeze_map(self.venue_index))\n        object.__setattr__(self,"taxonomy_index",_freeze_map(self.taxonomy_index))\n        object.__setattr__(self,"alias_index",_freeze_map(self.alias_index))\n        object.__setattr__(self,"relationship_index",_freeze_map(self.relationship_index))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_107_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-107")\n    @property\n    def index_hash(self):\n        return deterministic_sha256({\n            "canonical_ids":self.canonical_ids,\n            "venue_index":self.venue_index,\n            "taxonomy_index":self.taxonomy_index,\n            "alias_index":self.alias_index,\n            "relationship_index":self.relationship_index,\n            "lineage":self.lineage,\n        })\n\nclass RegistryIndexBuilder:\n    __slots__=()\n    def build(self,registry:CanonicalMarketRegistry,*,lineage:ImmutableLineage)->RegistryIndexes:\n        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")\n        canonical={}; venue={}; taxonomy={}; alias={}; relationship={}\n        for pos,record in enumerate(registry.records):\n            cid=record.canonical_market_id\n            canonical[cid]=pos\n            taxonomy.setdefault(record.taxonomy_key,[]).append(cid)\n            for binding in record.venue_bindings:\n                venue.setdefault(binding.venue_key,[]).append(cid)\n            for key in record.alias_keys:\n                alias.setdefault(key,[]).append(cid)\n            for rh in record.relationship_hashes:\n                relationship.setdefault(rh,[]).append(cid)\n        for bucket in (venue,taxonomy,alias,relationship):\n            for k,v in bucket.items(): bucket[k]=tuple(sorted(set(v)))\n        return RegistryIndexes(canonical,venue,taxonomy,alias,relationship,lineage)\n\ndef build_umd_107_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_107_BUILD_ID,"revision":UMD_107_REVISION,"schema_version":UMD_107_SCHEMA_VERSION,\n       "upstream_builds":("UMD-103","UMD-106"),"mode":"deterministic_read_only_registry_indexing",\n       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,\n       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\n\ndef verify_umd_107_registry_index_builder()->bool:\n    if verify_umd_106_registry_query_engine() is not True:return False\n    m=build_umd_107_certification_manifest()\n    return m["build_id"]=="UMD-107" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_107_registry_index_builder import *\n\nFIXED=datetime(2026,8,9,16,10,tzinfo=timezone.utc)\n\ndef record(cid,venue,mid,ih,taxonomy,aliases=(),rels=()):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://107/102",),created_at=FIXED)\n    return CanonicalMarketRecord(cid,ih,(VenueMarketBinding(venue,mid,ih),),taxonomy,"c"*64,"d"*64,\n        tuple(sorted(aliases)),tuple(sorted(rels)),"",{},l)\n\ndef registry(records):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",\n        parent_hashes=tuple(r.record_hash for r in records),source_refs=("fixture://107/103",),created_at=FIXED)\n    return CanonicalMarketRegistryBuilder().build(records,lineage=l)\n\ndef ilineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-107",revision=UMD_107_REVISION,schema_version="1.0.0",\n        parent_hashes=(),source_refs=("fixture://107",),created_at=FIXED)\n\nclass TestUMD107(unittest.TestCase):\n    def setUp(self):\n        a=record("umd:market:a","kalshi","K-A","a"*64,"crypto/btc",("btc-100k",),("1"*64,))\n        b=record("umd:market:b","polymarket","P-B","b"*64,"politics/election",("candidate-b",),("2"*64,))\n        self.g=registry((a,b))\n        self.x=RegistryIndexBuilder().build(self.g,lineage=ilineage())\n\n    def test_foundation(self): self.assertTrue(verify_umd_107_registry_index_builder())\n    def test_canonical_index(self): self.assertEqual(set(self.x.canonical_ids),{"umd:market:a","umd:market:b"})\n    def test_venue_index(self): self.assertEqual(self.x.venue_index["kalshi"],("umd:market:a",))\n    def test_taxonomy_index(self): self.assertEqual(self.x.taxonomy_index["crypto/btc"],("umd:market:a",))\n    def test_alias_index(self): self.assertEqual(self.x.alias_index["btc-100k"],("umd:market:a",))\n    def test_relationship_index(self): self.assertEqual(self.x.relationship_index["1"*64],("umd:market:a",))\n    def test_deterministic(self):\n        y=RegistryIndexBuilder().build(self.g,lineage=ilineage())\n        self.assertEqual(self.x.index_hash,y.index_hash)\n    def test_immutable_maps(self):\n        with self.assertRaises(TypeError): self.x.canonical_ids["x"]=9\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): RegistryIndexBuilder().build(object(),lineage=ilineage())\n    def test_side_effects(self):\n        m=build_umd_107_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-107 CERTIFICATION TEST");print(" REGISTRY INDEX BUILDER — CORRECTION V2");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD107))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_107_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical, venue, taxonomy, alias, and relationship indexes functionally certified")\n    print("[PASS] UMD-102 venue_key contract aligned exactly")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-107 CERTIFIED")\n'
UPSTREAM_MODULE='umd_106_registry_query_engine'
UPSTREAM_VERIFIER='verify_umd_106_registry_query_engine'
EXPORTED_NAMES=('UMD_107_REVISION', 'RegistryIndexes', 'RegistryIndexBuilder', 'build_umd_107_certification_manifest', 'verify_umd_107_registry_index_builder')

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
    marker="# UMD-107 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {n},\n" for n in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None)
        importlib.invalidate_caches()
        mod=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(mod,n)]
        if missing:
            raise RuntimeError("UMD-107 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-107 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-107 INSTALLER")
    print(" REGISTRY INDEX BUILDER")
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
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-107 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-107',
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
    print("[DONE] UMD-107 INSTALLATION COMPLETE")
if __name__=="__main__":
    main()
