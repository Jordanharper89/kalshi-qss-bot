from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_103_CANONICAL_MARKET_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_103_canonical_market_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_103_canonical_market_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Any, Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_102_canonical_market_record import CanonicalMarketRecord, verify_umd_102_canonical_market_record_assembly\n\nUMD_103_BUILD_ID="UMD-103"\nUMD_103_REVISION="UMD_103_CANONICAL_MARKET_REGISTRY_V1"\nUMD_103_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass CanonicalMarketRegistry:\n    records:Tuple[CanonicalMarketRecord,...]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"records",tuple(self.records))\n        ids=[r.canonical_market_id for r in self.records]\n        if len(ids)!=len(set(ids)): raise ValueError("duplicate canonical_market_id in registry")\n        if tuple(ids)!=tuple(sorted(ids)): raise ValueError("records must be sorted by canonical_market_id")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_103_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-103")\n        required={r.record_hash for r in self.records}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every record hash")\n    def get(self,canonical_market_id:str)->CanonicalMarketRecord|None:\n        for r in self.records:\n            if r.canonical_market_id==canonical_market_id:return r\n        return None\n    def to_canonical_dict(self):\n        return {"record_hashes":tuple(r.record_hash for r in self.records),"lineage":self.lineage}\n    @property\n    def registry_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\nclass CanonicalMarketRegistryBuilder:\n    __slots__=()\n    def build(self,records:Iterable[CanonicalMarketRecord],*,lineage:ImmutableLineage)->CanonicalMarketRegistry:\n        vals=tuple(records)\n        if any(not isinstance(x,CanonicalMarketRecord) for x in vals): raise TypeError("records must contain CanonicalMarketRecord")\n        vals=tuple(sorted(vals,key=lambda r:r.canonical_market_id))\n        return CanonicalMarketRegistry(vals,lineage)\n\ndef build_umd_103_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_103_BUILD_ID,"revision":UMD_103_REVISION,"schema_version":UMD_103_SCHEMA_VERSION,\n       "upstream_builds":("UMD-102",),"mode":"deterministic_read_only_canonical_registry","prohibited_capabilities":PROHIBITED_CAPABILITIES,\n       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_103_canonical_market_registry()->bool:\n    if verify_umd_102_canonical_market_record_assembly() is not True:return False\n    m=build_umd_103_certification_manifest()\n    return m["build_id"]=="UMD-103" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord, VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import *\n\nFIXED=datetime(2026,8,9,14,0,tzinfo=timezone.utc)\n\ndef make_record(cid, identity_hash):\n    binding=VenueMarketBinding("fixture-venue",cid.rsplit(":",1)[-1],identity_hash)\n    lineage=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(identity_hash,),source_refs=("fixture://103/102",),created_at=FIXED\n    )\n    return CanonicalMarketRecord(\n        canonical_market_id=cid,\n        primary_identity_hash=identity_hash,\n        venue_bindings=(binding,),\n        taxonomy_key="fixture/domain/category/subcategory/type",\n        lifecycle_hash="c"*64,\n        outcome_schema_hash="d"*64,\n        alias_keys=(),\n        relationship_hashes=(),\n        duplicate_group_hash="",\n        metadata={},\n        lineage=lineage,\n    )\n\ndef registry_lineage(records):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",\n        parent_hashes=tuple(r.record_hash for r in records),source_refs=("fixture://103",),created_at=FIXED\n    )\n\nclass TestUMD103(unittest.TestCase):\n    def test_foundation(self):\n        self.assertTrue(verify_umd_103_canonical_market_registry())\n\n    def test_build_sorted(self):\n        a=make_record("umd:market:b","b"*64)\n        b=make_record("umd:market:a","a"*64)\n        g=CanonicalMarketRegistryBuilder().build((a,b),lineage=registry_lineage((a,b)))\n        self.assertEqual(g.records[0].canonical_market_id,"umd:market:a")\n\n    def test_lookup(self):\n        a=make_record("umd:market:a","a"*64)\n        g=CanonicalMarketRegistryBuilder().build((a,),lineage=registry_lineage((a,)))\n        self.assertIs(g.get("umd:market:a"),a)\n\n    def test_missing_lookup(self):\n        g=CanonicalMarketRegistryBuilder().build((),lineage=registry_lineage(()))\n        self.assertIsNone(g.get("missing"))\n\n    def test_duplicate_rejected(self):\n        a=make_record("umd:market:a","a"*64)\n        b=make_record("umd:market:a","b"*64)\n        with self.assertRaises(ValueError):\n            CanonicalMarketRegistryBuilder().build((a,b),lineage=registry_lineage((a,b)))\n\n    def test_lineage_required(self):\n        a=make_record("umd:market:a","a"*64)\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,schema_version="1.0.0",\n            parent_hashes=("0"*64,),source_refs=("fixture://103/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            CanonicalMarketRegistryBuilder().build((a,),lineage=bad)\n\n    def test_immutable(self):\n        g=CanonicalMarketRegistryBuilder().build((),lineage=registry_lineage(()))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            g.records=()\n\n    def test_deterministic(self):\n        a=make_record("umd:market:a","a"*64)\n        l=registry_lineage((a,))\n        x=CanonicalMarketRegistryBuilder().build((a,),lineage=l)\n        y=CanonicalMarketRegistryBuilder().build((a,),lineage=l)\n        self.assertEqual(x.registry_hash,y.registry_hash)\n\n    def test_side_effects(self):\n        m=build_umd_103_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-103 CERTIFICATION TEST");print(" CANONICAL MARKET REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD103))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_103_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-102 canonical market records consumed read-only")\n    print("[PASS] Deterministic immutable canonical registry certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-103 CERTIFIED")\n'
UPSTREAM_MODULE='umd_102_canonical_market_record'
UPSTREAM_VERIFIER='verify_umd_102_canonical_market_record_assembly'
EXPORTED_NAMES=('UMD_103_REVISION', 'CanonicalMarketRegistry', 'CanonicalMarketRegistryBuilder', 'build_umd_103_certification_manifest', 'verify_umd_103_canonical_market_registry')

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        m=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        v=getattr(m,UPSTREAM_VERIFIER,None)
        if v is None or v() is not True:
            raise RuntimeError(f"Certified upstream verification failed: {UPSTREAM_MODULE}.{UPSTREAM_VERIFIER}")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def write_exact(path, text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker="# UMD-103 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {n},\n" for n in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None); importlib.invalidate_caches()
        m=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(m,n)]
        if missing: raise RuntimeError("Missing symbols: "+", ".join(missing))
        verifier=getattr(m,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True: raise RuntimeError("Verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72); print(" UMD-103 INSTALLER"); print(" CANONICAL MARKET REGISTRY"); print("="*72)
    print(f"[BOOT] Revision: {REVISION}"); print(f"[ROOT] {ROOT}")
    verify_upstream(); print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        verify_current()
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-103 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-103',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-103 INSTALLATION COMPLETE")
if __name__=="__main__": main()
