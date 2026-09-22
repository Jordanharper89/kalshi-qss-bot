from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path
REVISION='UMD_110_MARKET_FAMILY_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_110_market_family_resolution.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_110_market_family_resolution.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile,verify_umd_109_market_semantic_profile\nUMD_110_BUILD_ID="UMD-110"; UMD_110_REVISION="UMD_110_MARKET_FAMILY_RESOLUTION_V1"; UMD_110_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nDEFAULT_FAMILY_DIMENSIONS=("asset","event","metric","market_type")\n@dataclass(frozen=True,slots=True)\nclass MarketFamily:\n    family_key:str; dimensions:Tuple[str,...]; member_market_ids:Tuple[str,...]; member_profile_hashes:Tuple[str,...]; lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"dimensions",tuple(self.dimensions)); object.__setattr__(self,"member_market_ids",tuple(self.member_market_ids)); object.__setattr__(self,"member_profile_hashes",tuple(self.member_profile_hashes))\n        if not self.member_market_ids: raise ValueError("market family requires at least one member")\n        if len(self.member_market_ids)!=len(self.member_profile_hashes): raise ValueError("member ids and profile hashes length mismatch")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_110_BUILD_ID: raise ValueError("lineage must belong to UMD-110")\n        if not set(self.member_profile_hashes).issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include every member profile hash")\n    @property\n    def family_hash(self):\n        return deterministic_sha256({"family_key":self.family_key,"dimensions":self.dimensions,"member_market_ids":self.member_market_ids,"member_profile_hashes":self.member_profile_hashes,"lineage":self.lineage})\nclass MarketFamilyResolver:\n    __slots__=("dimensions",)\n    def __init__(self,dimensions:Iterable[str]=DEFAULT_FAMILY_DIMENSIONS):\n        dims=tuple(dimensions)\n        if not dims or len(set(dims))!=len(dims): raise ValueError("dimensions must be non-empty and unique")\n        self.dimensions=dims\n    def family_key(self,profile:MarketSemanticProfile)->str:\n        if not isinstance(profile,MarketSemanticProfile): raise TypeError("profile must be MarketSemanticProfile")\n        return "|".join(dim+"="+(",".join(profile.values(dim)) if profile.values(dim) else "*") for dim in self.dimensions)\n    def resolve(self,profiles:Iterable[MarketSemanticProfile],*,lineage_factory)->Tuple[MarketFamily,...]:\n        vals=tuple(profiles)\n        if any(not isinstance(p,MarketSemanticProfile) for p in vals): raise TypeError("profiles must contain MarketSemanticProfile")\n        buckets={}\n        for p in vals: buckets.setdefault(self.family_key(p),[]).append(p)\n        out=[]\n        for key,members in sorted(buckets.items()):\n            members=tuple(sorted(members,key=lambda p:p.canonical_market_id))\n            lineage=lineage_factory(tuple(p.profile_hash for p in members))\n            out.append(MarketFamily(key,self.dimensions,tuple(p.canonical_market_id for p in members),tuple(p.profile_hash for p in members),lineage))\n        return tuple(out)\ndef build_umd_110_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_110_BUILD_ID,"revision":UMD_110_REVISION,"schema_version":UMD_110_SCHEMA_VERSION,"upstream_builds":("UMD-109",),\n       "mode":"deterministic_read_only_market_family_resolution","default_family_dimensions":DEFAULT_FAMILY_DIMENSIONS,"prohibited_capabilities":PROHIBITED_CAPABILITIES,\n       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_110_market_family_resolution()->bool:\n    if verify_umd_109_market_semantic_profile() is not True:return False\n    m=build_umd_110_certification_manifest()\n    return m["build_id"]=="UMD-110" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='from __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import *\nFIXED=datetime(2026,8,9,17,10,tzinfo=timezone.utc)\ndef profile(cid,ih,facts):\n    l102=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://110/102",),created_at=FIXED)\n    r=CanonicalMarketRecord(cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102)\n    l109=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,schema_version="1.0.0",parent_hashes=(r.record_hash,),source_refs=("fixture://110/109",),created_at=FIXED)\n    return MarketSemanticProfiler().build(r,facts,lineage=l109)\ndef lf(parent_hashes):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,schema_version="1.0.0",parent_hashes=parent_hashes,source_refs=("fixture://110",),created_at=FIXED)\nclass TestUMD110(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_110_market_family_resolution())\n    def test_same_family(self):\n        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold","100000")))\n        b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold","150000")))\n        fam=MarketFamilyResolver().resolve((a,b),lineage_factory=lf); self.assertEqual(len(fam),1); self.assertEqual(fam[0].member_market_ids,("umd:market:a","umd:market:b"))\n    def test_different_family(self):\n        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold")))\n        b=profile("umd:market:b","b"*64,(("asset","Ethereum"),("metric","Price"),("market_type","Price Threshold")))\n        self.assertEqual(len(MarketFamilyResolver().resolve((a,b),lineage_factory=lf)),2)\n    def test_threshold_not_default_dimension(self):\n        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("metric","Price"),("threshold","100000")))\n        b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),("metric","Price"),("threshold","200000")))\n        self.assertEqual(MarketFamilyResolver().family_key(a),MarketFamilyResolver().family_key(b))\n    def test_custom_dimensions(self):\n        p=profile("umd:market:a","a"*64,(("asset","Bitcoin"),("threshold","100000"))); self.assertIn("threshold=100000",MarketFamilyResolver(("asset","threshold")).family_key(p))\n    def test_deterministic(self):\n        a=profile("umd:market:a","a"*64,(("asset","Bitcoin"),)); b=profile("umd:market:b","b"*64,(("asset","Bitcoin"),))\n        x=MarketFamilyResolver().resolve((a,b),lineage_factory=lf); y=MarketFamilyResolver().resolve((b,a),lineage_factory=lf)\n        self.assertEqual(tuple(f.family_hash for f in x),tuple(f.family_hash for f in y))\n    def test_bad_dimensions(self):\n        with self.assertRaises(ValueError): MarketFamilyResolver(())\n    def test_side_effects(self):\n        m=build_umd_110_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-110 CERTIFICATION TEST");print(" MARKET FAMILY RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD110))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_110_certification_manifest(); print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Semantic market-family grouping certified"); print("[PASS] Threshold variants can remain in one family")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-110 CERTIFIED")\n'
UPSTREAM_MODULE='umd_109_market_semantic_profile'
UPSTREAM_VERIFIER='verify_umd_109_market_semantic_profile'
EXPORTED_NAMES=('UMD_110_REVISION', 'DEFAULT_FAMILY_DIMENSIONS', 'MarketFamily', 'MarketFamilyResolver', 'build_umd_110_certification_manifest', 'verify_umd_110_market_family_resolution')
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
    marker="# UMD-110 exports"
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
    print("="*72); print(" UMD-110 INSTALLER"); print(" MARKET FAMILY RESOLUTION"); print("="*72)
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
        print("[ROLLBACK] UMD-110 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-110',"revision":REVISION,"module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-110 INSTALLATION COMPLETE")
if __name__=="__main__": main()
