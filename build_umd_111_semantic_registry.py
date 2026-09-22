from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path
REVISION='UMD_111_SEMANTIC_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_111_semantic_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_111_semantic_registry.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile\nfrom .umd_110_market_family_resolution import MarketFamily,verify_umd_110_market_family_resolution\nUMD_111_BUILD_ID="UMD-111"; UMD_111_REVISION="UMD_111_SEMANTIC_REGISTRY_V1"; UMD_111_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\ndef _freeze_index(source): return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n@dataclass(frozen=True,slots=True)\nclass SemanticRegistry:\n    profiles:Tuple[MarketSemanticProfile,...]; families:Tuple[MarketFamily,...]; fact_index:Mapping[str,Tuple[str,...]]; family_index:Mapping[str,Tuple[str,...]]; lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"profiles",tuple(self.profiles)); object.__setattr__(self,"families",tuple(self.families))\n        object.__setattr__(self,"fact_index",_freeze_index(self.fact_index)); object.__setattr__(self,"family_index",_freeze_index(self.family_index))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_111_BUILD_ID: raise ValueError("lineage must belong to UMD-111")\n        required={p.profile_hash for p in self.profiles}|{f.family_hash for f in self.families}\n        if not required.issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include every profile and family hash")\n    def markets_with(self,kind:str,key:str)->Tuple[str,...]: return self.fact_index.get(kind+"="+key,())\n    def family_members(self,family_key:str)->Tuple[str,...]: return self.family_index.get(family_key,())\n    @property\n    def registry_hash(self):\n        return deterministic_sha256({"profile_hashes":tuple(p.profile_hash for p in self.profiles),"family_hashes":tuple(f.family_hash for f in self.families),\n            "fact_index":self.fact_index,"family_index":self.family_index,"lineage":self.lineage})\nclass SemanticRegistryBuilder:\n    __slots__=()\n    def build(self,profiles:Iterable[MarketSemanticProfile],families:Iterable[MarketFamily],*,lineage:ImmutableLineage)->SemanticRegistry:\n        ps=tuple(sorted(profiles,key=lambda p:p.canonical_market_id)); fs=tuple(sorted(families,key=lambda f:f.family_key))\n        if any(not isinstance(p,MarketSemanticProfile) for p in ps): raise TypeError("profiles must contain MarketSemanticProfile")\n        if any(not isinstance(f,MarketFamily) for f in fs): raise TypeError("families must contain MarketFamily")\n        fact={}\n        for p in ps:\n            for f in p.facts: fact.setdefault(f.kind+"="+f.key,[]).append(p.canonical_market_id)\n        fam={f.family_key:list(f.member_market_ids) for f in fs}\n        for d in (fact,fam):\n            for k,v in d.items(): d[k]=tuple(sorted(set(v)))\n        return SemanticRegistry(ps,fs,fact,fam,lineage)\ndef build_umd_111_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_111_BUILD_ID,"revision":UMD_111_REVISION,"schema_version":UMD_111_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110"),\n       "mode":"deterministic_read_only_semantic_registry","prohibited_capabilities":PROHIBITED_CAPABILITIES,"network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_111_semantic_registry()->bool:\n    if verify_umd_110_market_family_resolution() is not True:return False\n    m=build_umd_111_certification_manifest()\n    return m["build_id"]=="UMD-111" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='from __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver\nfrom qseries_v2.universal_market_discovery.umd_111_semantic_registry import *\nFIXED=datetime(2026,8,9,17,20,tzinfo=timezone.utc)\ndef profile(cid,ih,asset,threshold):\n    l102=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://111/102",),created_at=FIXED)\n    r=CanonicalMarketRecord(cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102)\n    l109=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://111/109",),created_at=FIXED)\n    return MarketSemanticProfiler().build(r,(("asset",asset),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),lineage=l109)\ndef family_lineage(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://111/110",),created_at=FIXED)\ndef registry_lineage(ps,fs):\n    parents=tuple(p.profile_hash for p in ps)+tuple(f.family_hash for f in fs)\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision=UMD_111_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://111",),created_at=FIXED)\nclass TestUMD111(unittest.TestCase):\n    def setUp(self):\n        self.a=profile("umd:market:a","a"*64,"Bitcoin","100000"); self.b=profile("umd:market:b","b"*64,"Bitcoin","150000"); self.c=profile("umd:market:c","c"*64,"Ethereum","10000")\n        self.ps=(self.a,self.b,self.c); self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)\n        self.r=SemanticRegistryBuilder().build(self.ps,self.fs,lineage=registry_lineage(self.ps,self.fs))\n    def test_foundation(self): self.assertTrue(verify_umd_111_semantic_registry())\n    def test_fact_query(self): self.assertEqual(self.r.markets_with("asset","bitcoin"),("umd:market:a","umd:market:b"))\n    def test_threshold_query(self): self.assertEqual(self.r.markets_with("threshold","100000"),("umd:market:a",))\n    def test_family_members(self):\n        btc=[f for f in self.fs if "asset=bitcoin" in f.family_key][0]; self.assertEqual(self.r.family_members(btc.family_key),("umd:market:a","umd:market:b"))\n    def test_unknown_fact(self): self.assertEqual(self.r.markets_with("asset","solana"),())\n    def test_deterministic(self):\n        x=SemanticRegistryBuilder().build(tuple(reversed(self.ps)),tuple(reversed(self.fs)),lineage=registry_lineage(self.ps,self.fs)); self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_immutable_index(self):\n        with self.assertRaises(TypeError): self.r.fact_index["asset=bitcoin"]=()\n    def test_lineage_required(self):\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision=UMD_111_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://111/bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): SemanticRegistryBuilder().build(self.ps,self.fs,lineage=bad)\n    def test_side_effects(self):\n        m=build_umd_111_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-111 CERTIFICATION TEST");print(" SEMANTIC REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD111))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_111_certification_manifest(); print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Semantic fact and market-family registry queries certified"); print("[PASS] UMD-109 and UMD-110 consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-111 CERTIFIED")\n'
UPSTREAM_MODULE='umd_110_market_family_resolution'
UPSTREAM_VERIFIER='verify_umd_110_market_family_resolution'
EXPORTED_NAMES=('UMD_111_REVISION', 'SemanticRegistry', 'SemanticRegistryBuilder', 'build_umd_111_certification_manifest', 'verify_umd_111_semantic_registry')
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
    marker="# UMD-111 exports"
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
    print("="*72); print(" UMD-111 INSTALLER"); print(" SEMANTIC REGISTRY"); print("="*72)
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
        print("[ROLLBACK] UMD-111 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-111',"revision":REVISION,"module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-111 INSTALLATION COMPLETE")
if __name__=="__main__": main()
