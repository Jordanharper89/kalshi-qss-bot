from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path
REVISION='UMD_109_MARKET_SEMANTIC_PROFILE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_109_market_semantic_profile.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_109_market_semantic_profile.py'
MODULE_SOURCE='from __future__ import annotations\nimport re\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_102_canonical_market_record import CanonicalMarketRecord\nfrom .umd_108_registry_search_engine import verify_umd_108_registry_search_engine\nUMD_109_BUILD_ID="UMD-109"; UMD_109_REVISION="UMD_109_MARKET_SEMANTIC_PROFILE_V1"; UMD_109_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nSEMANTIC_KINDS=("entity","asset","event","metric","operator","threshold","unit","geography","time_window","settlement_source","market_type")\n_KEY_RE=re.compile(r"[^a-z0-9]+")\ndef semantic_key(value:str)->str:\n    if not isinstance(value,str): raise TypeError("semantic value must be a string")\n    value=_KEY_RE.sub("-",value.strip().casefold()).strip("-")\n    if not value: raise ValueError("semantic value must contain letters or digits")\n    return value\n@dataclass(frozen=True,slots=True)\nclass SemanticFact:\n    kind:str; value:str; key:str\n    def __post_init__(self):\n        if self.kind not in SEMANTIC_KINDS: raise ValueError("unsupported semantic fact kind")\n        if self.key!=semantic_key(self.value): raise ValueError("semantic fact key does not match value")\n    @property\n    def fact_hash(self): return deterministic_sha256({"kind":self.kind,"key":self.key})\n@dataclass(frozen=True,slots=True)\nclass MarketSemanticProfile:\n    canonical_market_id:str; record_hash:str; facts:Tuple[SemanticFact,...]; lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"facts",tuple(self.facts))\n        if tuple(sorted(self.facts,key=lambda f:(f.kind,f.key)))!=self.facts: raise ValueError("facts must be deterministically sorted")\n        pairs=[(f.kind,f.key) for f in self.facts]\n        if len(pairs)!=len(set(pairs)): raise ValueError("duplicate semantic facts")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_109_BUILD_ID: raise ValueError("lineage must belong to UMD-109")\n        if self.record_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include canonical record hash")\n    def values(self,kind:str)->Tuple[str,...]: return tuple(f.key for f in self.facts if f.kind==kind)\n    @property\n    def profile_hash(self):\n        return deterministic_sha256({"canonical_market_id":self.canonical_market_id,"record_hash":self.record_hash,\n            "facts":tuple({"kind":f.kind,"key":f.key} for f in self.facts),"lineage":self.lineage})\nclass MarketSemanticProfiler:\n    __slots__=()\n    def build(self,record:CanonicalMarketRecord,facts:Iterable[tuple[str,str]],*,lineage:ImmutableLineage)->MarketSemanticProfile:\n        if not isinstance(record,CanonicalMarketRecord): raise TypeError("record must be CanonicalMarketRecord")\n        built=[]; seen=set()\n        for kind,value in facts:\n            key=semantic_key(value); pair=(kind,key)\n            if pair in seen: continue\n            seen.add(pair); built.append(SemanticFact(kind,value,key))\n        built.sort(key=lambda f:(f.kind,f.key))\n        return MarketSemanticProfile(record.canonical_market_id,record.record_hash,tuple(built),lineage)\ndef build_umd_109_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_109_BUILD_ID,"revision":UMD_109_REVISION,"schema_version":UMD_109_SCHEMA_VERSION,\n       "upstream_builds":("UMD-102","UMD-108"),"mode":"deterministic_read_only_market_semantics","semantic_kinds":SEMANTIC_KINDS,\n       "prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_109_market_semantic_profile()->bool:\n    if verify_umd_108_registry_search_engine() is not True:return False\n    m=build_umd_109_certification_manifest()\n    return m["build_id"]=="UMD-109" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='from __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import *\nFIXED=datetime(2026,8,9,17,0,tzinfo=timezone.utc)\ndef record():\n    ih="a"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://109/102",),created_at=FIXED)\n    return CanonicalMarketRecord("umd:market:btc100k",ih,(VenueMarketBinding("kalshi","K-BTC100K",ih),),"btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,("btc-100k",),(),"",{},l)\ndef lineage(r):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://109",),created_at=FIXED)\nclass TestUMD109(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_109_market_semantic_profile())\n    def test_profile_build(self):\n        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("metric","Price"),("operator","Above"),("threshold","100000"),("unit","USD")),lineage=lineage(r))\n        self.assertEqual(p.values("asset"),("bitcoin",)); self.assertEqual(p.values("threshold"),("100000",))\n    def test_deduplication(self):\n        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("asset","BITCOIN")),lineage=lineage(r)); self.assertEqual(len(p.facts),1)\n    def test_deterministic_order(self):\n        r=record(); l=lineage(r)\n        a=MarketSemanticProfiler().build(r,(("unit","USD"),("asset","Bitcoin")),lineage=l)\n        b=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),("unit","USD")),lineage=l)\n        self.assertEqual(a.profile_hash,b.profile_hash)\n    def test_invalid_kind(self):\n        r=record()\n        with self.assertRaises(ValueError): MarketSemanticProfiler().build(r,(("unknown","x"),),lineage=lineage(r))\n    def test_lineage_required(self):\n        r=record(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://109/bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): MarketSemanticProfiler().build(r,(("asset","Bitcoin"),),lineage=bad)\n    def test_immutable(self):\n        r=record(); p=MarketSemanticProfiler().build(r,(("asset","Bitcoin"),),lineage=lineage(r))\n        with self.assertRaises((FrozenInstanceError,AttributeError)): p.facts=()\n    def test_side_effects(self):\n        m=build_umd_109_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-109 CERTIFICATION TEST");print(" MARKET SEMANTIC PROFILE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD109))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_109_certification_manifest(); print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Structured market semantic facts certified"); print("[PASS] UMD-108 capability chain consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-109 CERTIFIED")\n'
UPSTREAM_MODULE='umd_108_registry_search_engine'
UPSTREAM_VERIFIER='verify_umd_108_registry_search_engine'
EXPORTED_NAMES=('UMD_109_REVISION', 'SEMANTIC_KINDS', 'SemanticFact', 'MarketSemanticProfile', 'MarketSemanticProfiler', 'semantic_key', 'build_umd_109_certification_manifest', 'verify_umd_109_market_semantic_profile')
def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        m=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        v=getattr(m,UPSTREAM_VERIFIER,None)
        if v is None or v() is not True: raise RuntimeError("Certified upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker="# UMD-109 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {n},\n" for n in EXPORTED_NAMES)+")\n"
    if marker not in current: write_exact(INIT,current.rstrip()+"\n\n"+block)
def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None); importlib.invalidate_caches()
        m=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(m,n)]
        if missing: raise RuntimeError("Missing symbols: "+", ".join(missing))
        v=getattr(m,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if v() is not True: raise RuntimeError("Verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    print("="*72); print(" UMD-109 INSTALLER"); print(" MARKET SEMANTIC PROFILE"); print("="*72)
    print(f"[BOOT] Revision: {REVISION}"); print(f"[ROOT] {ROOT}")
    verify_upstream(); print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        verify_current()
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-109 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-109',"revision":REVISION,"module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-109 INSTALLATION COMPLETE")
if __name__=="__main__": main()
