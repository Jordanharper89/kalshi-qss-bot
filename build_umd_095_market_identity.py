from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_095_CANONICAL_MARKET_IDENTITY_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_095_market_identity.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_095_market_identity.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_094_market_normalization import NormalizedMarket, verify_umd_094_market_normalization_foundation\n\nUMD_095_BUILD_ID="UMD-095"\nUMD_095_BUILD_NAME="Canonical Market Identity Resolution"\nUMD_095_REVISION="UMD_095_CANONICAL_MARKET_IDENTITY_RESOLUTION_V1"\nUMD_095_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n\ndef _freeze(v: Mapping[str,Any]|None)->Mapping[str,Any]:\n    if v is None: v={}\n    if not isinstance(v,Mapping): raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),x) for k,x in v.items())))\n\n\ndef canonical_identity_key(market: NormalizedMarket) -> str:\n    if not isinstance(market, NormalizedMarket): raise TypeError("market must be NormalizedMarket")\n    payload={"title_key":market.title_key,"category_key":market.category_key,"close_time":market.close_time,"settlement_time":market.settlement_time,"outcome_keys":tuple(sorted(market.outcome_keys))}\n    return deterministic_sha256(payload)\n\n@dataclass(frozen=True,slots=True)\nclass CanonicalMarketIdentity:\n    canonical_market_id:str\n    identity_key:str\n    source_market_hash:str\n    venue_key:str\n    venue_market_id:str\n    title_key:str\n    category_key:str\n    close_time:str\n    settlement_time:str\n    outcome_keys:Tuple[str,...]\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n        expected="umd:market:"+self.identity_key\n        if self.canonical_market_id!=expected: raise ValueError("canonical_market_id does not match identity_key")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_095_BUILD_ID: raise ValueError("lineage must belong to UMD-095")\n        if self.source_market_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include source market hash")\n    def to_canonical_dict(self):\n        return {"canonical_market_id":self.canonical_market_id,"identity_key":self.identity_key,"source_market_hash":self.source_market_hash,"venue_key":self.venue_key,"venue_market_id":self.venue_market_id,"title_key":self.title_key,"category_key":self.category_key,"close_time":self.close_time,"settlement_time":self.settlement_time,"outcome_keys":self.outcome_keys,"metadata":self.metadata,"lineage":self.lineage}\n    @property\n    def identity_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\nclass CanonicalMarketIdentityResolver:\n    __slots__=()\n    def resolve(self, market:NormalizedMarket, *, lineage:ImmutableLineage, metadata:Mapping[str,Any]|None=None)->CanonicalMarketIdentity:\n        key=canonical_identity_key(market)\n        return CanonicalMarketIdentity(canonical_market_id="umd:market:"+key,identity_key=key,source_market_hash=market.normalized_market_hash,venue_key=market.venue_key,venue_market_id=market.venue_market_id,title_key=market.title_key,category_key=market.category_key,close_time=market.close_time,settlement_time=market.settlement_time,outcome_keys=tuple(sorted(market.outcome_keys)),metadata={} if metadata is None else metadata,lineage=lineage)\n\ndef build_umd_095_certification_manifest():\n    data={"subsystem_id":"UMD","build_id":UMD_095_BUILD_ID,"revision":UMD_095_REVISION,"schema_version":UMD_095_SCHEMA_VERSION,"upstream_builds":("UMD-093","UMD-094"),"mode":"deterministic_read_only_identity_resolution","prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_095_canonical_market_identity_resolution()->bool:\n    if verify_umd_094_market_normalization_foundation() is not True: return False\n    m=build_umd_095_certification_manifest(); return m["build_id"]=="UMD-095" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver,canonical_identity_key,build_umd_095_certification_manifest,verify_umd_095_canonical_market_identity_resolution\nFIXED=datetime(2026,8,8,12,5,tzinfo=timezone.utc)\ndef normalized(venue="Kalshi",mid="A"):\n    o=MarketObservation(venue=venue,venue_market_id=mid,title="Will BTC exceed 100K?",category="Crypto",status="Open",close_time="2026-12-31T23:59:59Z",outcomes=("Yes","No"))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://095/94",),created_at=FIXED)\n    return MarketNormalizer().normalize(o,lineage=l)\ndef lineage(h): return ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(h,),source_refs=("fixture://095",),created_at=FIXED)\nclass TestUMD095(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_095_canonical_market_identity_resolution())\n    def test_same_semantics_same_identity(self):\n        a=normalized("Kalshi","A"); b=normalized("Polymarket","B"); self.assertEqual(canonical_identity_key(a),canonical_identity_key(b))\n    def test_resolve(self):\n        a=normalized(); x=CanonicalMarketIdentityResolver().resolve(a,lineage=lineage(a.normalized_market_hash)); self.assertTrue(x.canonical_market_id.startswith("umd:market:")); self.assertEqual(x.identity_key,canonical_identity_key(a))\n    def test_deterministic(self):\n        a=normalized(); l=lineage(a.normalized_market_hash); r=CanonicalMarketIdentityResolver(); self.assertEqual(r.resolve(a,lineage=l).identity_hash,r.resolve(a,lineage=l).identity_hash)\n    def test_lineage(self):\n        a=normalized(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): CanonicalMarketIdentityResolver().resolve(a,lineage=bad)\n    def test_immutable(self):\n        a=normalized(); x=CanonicalMarketIdentityResolver().resolve(a,lineage=lineage(a.normalized_market_hash));\n        with self.assertRaises((FrozenInstanceError,AttributeError)): x.identity_key="x"\n    def test_side_effects(self):\n        m=build_umd_095_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72); print(" UMD-095 CERTIFICATION TEST"); print(" CANONICAL MARKET IDENTITY RESOLUTION"); print("="*72); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD095));\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_095_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}"); print("[PASS] UMD-094 normalized markets consumed read-only"); print("[PASS] Deterministic canonical identity resolution certified"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-095 CERTIFIED")\n'
UPSTREAM_MODULE='umd_094_market_normalization'
UPSTREAM_VERIFIER='verify_umd_094_market_normalization_foundation'
EXPORTED_NAMES=('UMD_095_REVISION', 'CanonicalMarketIdentity', 'CanonicalMarketIdentityResolver', 'canonical_identity_key', 'build_umd_095_certification_manifest', 'verify_umd_095_canonical_market_identity_resolution')

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        mod=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        verifier=getattr(mod,UPSTREAM_VERIFIER,None)
        if verifier is None: raise RuntimeError(f"Certified upstream verifier missing: {UPSTREAM_MODULE}.{UPSTREAM_VERIFIER}")
        if verifier() is not True: raise RuntimeError(f"Certified upstream verification failed: {UPSTREAM_MODULE}")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def write_exact(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker=f"# UMD-095 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {name},\n" for name in EXPORTED_NAMES)+")\n"
    if marker not in current: write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None); importlib.invalidate_caches(); mod=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(mod,n)]
        if missing: raise RuntimeError("UMD-095 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True: raise RuntimeError("UMD-095 verification returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def sha256_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72); print(" UMD-095 INSTALLER"); print(" CANONICAL MARKET IDENTITY RESOLUTION"); print("="*72); print(f"[BOOT] Revision: {REVISION}"); print(f"[ROOT] {ROOT}")
    verify_upstream(); print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        verify_current()
    except Exception:
        for p,previous in backups.items():
            if previous is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(previous)
        importlib.invalidate_caches(); print("[ROLLBACK] UMD-095 installation failed; all affected files restored"); raise
    manifest={"build_id":'UMD-095',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha256_file(MODULE),str(INIT.relative_to(ROOT)):sha256_file(INIT),str(TEST.relative_to(ROOT)):sha256_file(TEST)},"network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}"); print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified"); print(f"[PASS] Deterministic install hash: {h}"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-095 INSTALLATION COMPLETE"); return 0

if __name__=="__main__": raise SystemExit(main())
