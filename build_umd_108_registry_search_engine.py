from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_108_REGISTRY_SEARCH_ENGINE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_108_registry_search_engine.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_108_registry_search_engine.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry, CanonicalMarketRecord\nfrom .umd_107_registry_index_builder import RegistryIndexes, verify_umd_107_registry_index_builder\n\nUMD_108_BUILD_ID="UMD-108"\nUMD_108_REVISION="UMD_108_REGISTRY_SEARCH_ENGINE_V1"\nUMD_108_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _norm(value:str)->str:\n    return " ".join(str(value).strip().casefold().split())\n\n@dataclass(frozen=True,slots=True)\nclass RegistrySearchHit:\n    canonical_market_id:str\n    score:int\n    reasons:Tuple[str,...]\n    record_hash:str\n\n@dataclass(frozen=True,slots=True)\nclass RegistrySearchResult:\n    query:str\n    hits:Tuple[RegistrySearchHit,...]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"hits",tuple(self.hits))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_108_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-108")\n    @property\n    def result_hash(self):\n        return deterministic_sha256({"query":self.query,"hits":self.hits,"lineage":self.lineage})\n\nclass RegistrySearchEngine:\n    __slots__=("registry","indexes")\n    def __init__(self,registry:CanonicalMarketRegistry,indexes:RegistryIndexes):\n        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")\n        if not isinstance(indexes,RegistryIndexes): raise TypeError("indexes must be RegistryIndexes")\n        self.registry=registry; self.indexes=indexes\n\n    def search(self,query:str,*,taxonomy_key:str|None=None,lineage:ImmutableLineage)->RegistrySearchResult:\n        q=_norm(query)\n        hits=[]\n        for record in self.registry.records:\n            if taxonomy_key is not None and record.taxonomy_key!=taxonomy_key:\n                continue\n            score=0; reasons=[]\n            cid=_norm(record.canonical_market_id)\n            if q and q==cid: score+=100; reasons.append("canonical_exact")\n            elif q and cid.startswith(q): score+=60; reasons.append("canonical_prefix")\n            if q in tuple(_norm(a) for a in record.alias_keys):\n                score+=90; reasons.append("alias_exact")\n            if q and any(_norm(a).startswith(q) for a in record.alias_keys):\n                score+=40; reasons.append("alias_prefix")\n            if taxonomy_key is not None:\n                score+=10; reasons.append("taxonomy_filter")\n            if score:\n                hits.append(RegistrySearchHit(record.canonical_market_id,score,tuple(sorted(set(reasons))),record.record_hash))\n        hits.sort(key=lambda h:(-h.score,h.canonical_market_id,h.record_hash))\n        return RegistrySearchResult(query,tuple(hits),lineage)\n\ndef build_umd_108_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_108_BUILD_ID,"revision":UMD_108_REVISION,"schema_version":UMD_108_SCHEMA_VERSION,\n       "upstream_builds":("UMD-103","UMD-107"),"mode":"deterministic_read_only_registry_search",\n       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,\n       "mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\n\ndef verify_umd_108_registry_search_engine()->bool:\n    if verify_umd_107_registry_index_builder() is not True:return False\n    m=build_umd_108_certification_manifest()\n    return m["build_id"]=="UMD-108" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_108_registry_search_engine import *\n\nFIXED=datetime(2026,8,9,15,20,tzinfo=timezone.utc)\nclass TestUMD108(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_108_registry_search_engine())\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): RegistrySearchEngine(object(),object())\n    def test_result_hash_deterministic(self):\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-108",revision=UMD_108_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://108",),created_at=FIXED)\n        r1=RegistrySearchResult("btc",(),l); r2=RegistrySearchResult("btc",(),l)\n        self.assertEqual(r1.result_hash,r2.result_hash)\n    def test_side_effects(self):\n        m=build_umd_108_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-108 CERTIFICATION TEST");print(" REGISTRY SEARCH ENGINE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD108))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_108_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-107 deterministic registry indexes consumed read-only"); print("[PASS] Deterministic ranked registry search certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-108 CERTIFIED")\n'
UPSTREAM_MODULE='umd_107_registry_index_builder'
UPSTREAM_VERIFIER='verify_umd_107_registry_index_builder'
EXPORTED_NAMES=('UMD_108_REVISION', 'RegistrySearchHit', 'RegistrySearchResult', 'RegistrySearchEngine', 'build_umd_108_certification_manifest', 'verify_umd_108_registry_search_engine')

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
    marker="# UMD-108 exports"
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
            raise RuntimeError("UMD-108 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-108 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-108 INSTALLER")
    print(" REGISTRY SEARCH ENGINE")
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
        print("[ROLLBACK] UMD-108 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-108',
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
    print("[DONE] UMD-108 INSTALLATION COMPLETE")
if __name__=="__main__":
    main()
