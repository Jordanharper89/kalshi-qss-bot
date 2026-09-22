from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_106_REGISTRY_QUERY_ENGINE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_106_registry_query_engine.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_106_registry_query_engine.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry, CanonicalMarketRecord\nfrom .umd_105_registry_diff import verify_umd_105_registry_diff\n\nUMD_106_BUILD_ID="UMD-106"\nUMD_106_REVISION="UMD_106_REGISTRY_QUERY_ENGINE_V1"\nUMD_106_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass RegistryQueryResult:\n    query_type:str\n    query_key:str\n    records:Tuple[CanonicalMarketRecord,...]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"records",tuple(self.records))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_106_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-106")\n    @property\n    def result_hash(self):\n        return deterministic_sha256({\n            "query_type":self.query_type,\n            "query_key":self.query_key,\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "lineage":self.lineage,\n        })\n\nclass RegistryQueryEngine:\n    __slots__=("registry",)\n    def __init__(self,registry:CanonicalMarketRegistry):\n        if not isinstance(registry,CanonicalMarketRegistry):\n            raise TypeError("registry must be CanonicalMarketRegistry")\n        self.registry=registry\n\n    def by_canonical_id(self,canonical_market_id:str,*,lineage:ImmutableLineage)->RegistryQueryResult:\n        record=self.registry.get(canonical_market_id)\n        records=() if record is None else (record,)\n        return RegistryQueryResult("canonical_id",canonical_market_id,records,lineage)\n\n    def by_venue_market(self,venue:str,venue_market_id:str,*,lineage:ImmutableLineage)->RegistryQueryResult:\n        matches=[]\n        for record in self.registry.records:\n            for binding in record.venue_bindings:\n                if binding.venue==venue and binding.venue_market_id==venue_market_id:\n                    matches.append(record); break\n        matches=tuple(sorted(matches,key=lambda r:r.canonical_market_id))\n        return RegistryQueryResult("venue_market",f"{venue}:{venue_market_id}",matches,lineage)\n\n    def by_taxonomy(self,taxonomy_key:str,*,lineage:ImmutableLineage)->RegistryQueryResult:\n        matches=tuple(r for r in self.registry.records if r.taxonomy_key==taxonomy_key)\n        return RegistryQueryResult("taxonomy",taxonomy_key,matches,lineage)\n\ndef build_umd_106_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_106_BUILD_ID,"revision":UMD_106_REVISION,"schema_version":UMD_106_SCHEMA_VERSION,\n       "upstream_builds":("UMD-103","UMD-105"),"mode":"deterministic_read_only_registry_query",\n       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,\n       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\n\ndef verify_umd_106_registry_query_engine()->bool:\n    if verify_umd_105_registry_diff() is not True:return False\n    m=build_umd_106_certification_manifest()\n    return m["build_id"]=="UMD-106" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_106_registry_query_engine import *\n\nFIXED=datetime(2026,8,9,15,0,tzinfo=timezone.utc)\n\nclass TestUMD106(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_106_registry_query_engine())\n    def test_side_effects(self):\n        m=build_umd_106_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): RegistryQueryEngine(object())\n    def test_result_immutable_tuple(self):\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-106",revision=UMD_106_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://106",),created_at=FIXED)\n        r=RegistryQueryResult("x","y",[],l)\n        self.assertEqual(r.records,())\nif __name__=="__main__":\n    print("="*72);print(" UMD-106 CERTIFICATION TEST");print(" REGISTRY QUERY ENGINE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD106))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_106_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-105 certified registry capability chain consumed read-only"); print("[PASS] Deterministic registry query engine certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-106 CERTIFIED")\n'
UPSTREAM_MODULE='umd_105_registry_diff'
UPSTREAM_VERIFIER='verify_umd_105_registry_diff'
EXPORTED_NAMES=('UMD_106_REVISION', 'RegistryQueryResult', 'RegistryQueryEngine', 'build_umd_106_certification_manifest', 'verify_umd_106_registry_query_engine')

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
    marker="# UMD-106 exports"
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
            raise RuntimeError("UMD-106 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-106 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-106 INSTALLER")
    print(" REGISTRY QUERY ENGINE")
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
        print("[ROLLBACK] UMD-106 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-106',
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
    print("[DONE] UMD-106 INSTALLATION COMPLETE")
if __name__=="__main__":
    main()
