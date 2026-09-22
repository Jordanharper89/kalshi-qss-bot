from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_101_OUTCOME_SCHEMA_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_101_outcome_schema.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_101_outcome_schema.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_095_market_identity import CanonicalMarketIdentity\nfrom .umd_100_market_lifecycle import verify_umd_100_market_lifecycle_semantics\n\nUMD_101_BUILD_ID="UMD-101"\nUMD_101_BUILD_NAME="Outcome Schema Resolution"\nUMD_101_REVISION="UMD_101_OUTCOME_SCHEMA_RESOLUTION_V1"\nUMD_101_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nSCHEMA_TYPES=("unspecified","binary_yes_no","binary_generic","categorical")\n\n\ndef _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:\n    if value is None: value={}\n    if not isinstance(value,Mapping): raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))\n\n\n@dataclass(frozen=True,slots=True)\nclass OutcomeOption:\n    outcome_id:str\n    outcome_key:str\n    ordinal:int\n\n    def __post_init__(self):\n        if not isinstance(self.outcome_key,str) or not self.outcome_key: raise ValueError("outcome_key must be non-empty")\n        if not isinstance(self.ordinal,int) or self.ordinal<0: raise ValueError("ordinal must be non-negative")\n        expected="umd:outcome:"+deterministic_sha256({"outcome_key":self.outcome_key})\n        if self.outcome_id!=expected: raise ValueError("outcome_id does not match outcome_key")\n\n    def to_canonical_dict(self): return {"outcome_id":self.outcome_id,"outcome_key":self.outcome_key,"ordinal":self.ordinal}\n    @property\n    def option_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True,slots=True)\nclass OutcomeSchema:\n    canonical_market_id:str\n    identity_hash:str\n    schema_type:str\n    options:Tuple[OutcomeOption,...]\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"options",tuple(self.options)); object.__setattr__(self,"metadata",_freeze(self.metadata))\n        if self.schema_type not in SCHEMA_TYPES: raise ValueError("unsupported schema_type")\n        if len({x.outcome_key for x in self.options})!=len(self.options): raise ValueError("outcome keys must be unique")\n        if tuple(x.ordinal for x in self.options)!=tuple(range(len(self.options))): raise ValueError("outcome ordinals must be contiguous")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_101_BUILD_ID: raise ValueError("lineage must belong to UMD-101")\n        if self.identity_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include identity hash")\n\n    def to_canonical_dict(self):\n        return {"canonical_market_id":self.canonical_market_id,"identity_hash":self.identity_hash,"schema_type":self.schema_type,\n                "option_hashes":tuple(x.option_hash for x in self.options),"metadata":self.metadata,"lineage":self.lineage}\n    @property\n    def outcome_schema_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\n\nclass OutcomeSchemaResolver:\n    __slots__=()\n    def resolve(self,identity:CanonicalMarketIdentity,*,lineage:ImmutableLineage,metadata:Mapping[str,Any] | None=None)->OutcomeSchema:\n        if not isinstance(identity,CanonicalMarketIdentity): raise TypeError("identity must be CanonicalMarketIdentity")\n        keys=tuple(identity.outcome_keys)\n        if len(set(keys))!=len(keys): raise ValueError("identity outcome keys must be unique")\n        keyset=set(keys)\n        if not keys: schema_type="unspecified"; ordered=()\n        elif keyset=={"yes","no"} and len(keys)==2: schema_type="binary_yes_no"; ordered=("yes","no")\n        elif len(keys)==2: schema_type="binary_generic"; ordered=tuple(sorted(keys))\n        else: schema_type="categorical"; ordered=tuple(sorted(keys))\n        options=tuple(OutcomeOption("umd:outcome:"+deterministic_sha256({"outcome_key":key}),key,n) for n,key in enumerate(ordered))\n        return OutcomeSchema(canonical_market_id=identity.canonical_market_id,identity_hash=identity.identity_hash,schema_type=schema_type,\n            options=options,metadata={} if metadata is None else metadata,lineage=lineage)\n\n\ndef build_umd_101_certification_manifest():\n    data={"subsystem_id":"UMD","build_id":UMD_101_BUILD_ID,"revision":UMD_101_REVISION,"schema_version":UMD_101_SCHEMA_VERSION,\n          "upstream_builds":("UMD-095","UMD-100"),"mode":"deterministic_read_only_outcome_schema_resolution",\n          "schema_types":SCHEMA_TYPES,"prohibited_capabilities":PROHIBITED_CAPABILITIES,\n          "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\n\ndef verify_umd_101_outcome_schema_resolution()->bool:\n    if verify_umd_100_market_lifecycle_semantics() is not True: return False\n    m=build_umd_101_certification_manifest()\n    return m["build_id"]=="UMD-101" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver\nfrom qseries_v2.universal_market_discovery.umd_101_outcome_schema import (\n    UMD_101_REVISION,OutcomeSchemaResolver,build_umd_101_certification_manifest,verify_umd_101_outcome_schema_resolution,\n)\n\nFIXED=datetime(2026,8,9,12,10,tzinfo=timezone.utc)\n\ndef identity(outcomes):\n    o=MarketObservation(venue="Kalshi",venue_market_id="A",title="Example market",category="Other",status="Open",outcomes=tuple(outcomes))\n    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://101/94",),created_at=FIXED)\n    m=MarketNormalizer().normalize(o,lineage=l94)\n    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://101/95",),created_at=FIXED)\n    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)\n\ndef lineage(i): return ImmutableLineage(subsystem_id="UMD",build_id="UMD-101",revision=UMD_101_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://101",),created_at=FIXED)\n\nclass TestUMD101(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_101_outcome_schema_resolution())\n    def test_yes_no(self):\n        i=identity(("Yes","No")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"binary_yes_no"); self.assertEqual(tuple(x.outcome_key for x in s.options),("yes","no"))\n    def test_binary_generic(self):\n        i=identity(("Up","Down")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"binary_generic"); self.assertEqual(tuple(x.outcome_key for x in s.options),("down","up"))\n    def test_categorical(self):\n        i=identity(("A","B","C")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"categorical"); self.assertEqual(len(s.options),3)\n    def test_unspecified(self):\n        i=identity(()); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"unspecified"); self.assertEqual(s.options,())\n    def test_deterministic(self):\n        i=identity(("B","A","C")); l=lineage(i); r=OutcomeSchemaResolver(); self.assertEqual(r.resolve(i,lineage=l).outcome_schema_hash,r.resolve(i,lineage=l).outcome_schema_hash)\n    def test_unique_ids(self):\n        i=identity(("A","B","C")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(len({x.outcome_id for x in s.options}),3)\n    def test_lineage_required(self):\n        i=identity(("Yes","No")); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-101",revision=UMD_101_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): OutcomeSchemaResolver().resolve(i,lineage=bad)\n    def test_immutable(self):\n        i=identity(("Yes","No")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i))\n        with self.assertRaises((FrozenInstanceError,AttributeError)): s.schema_type="x"\n    def test_side_effects(self):\n        m=build_umd_101_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72); print(" UMD-101 CERTIFICATION TEST"); print(" OUTCOME SCHEMA RESOLUTION"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD101))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_101_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-100 lifecycle capability consumed read-only"); print("[PASS] Deterministic canonical outcome schema resolution certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-101 CERTIFIED")\n'
UPSTREAM_MODULE='umd_100_market_lifecycle'
UPSTREAM_VERIFIER='verify_umd_100_market_lifecycle_semantics'
EXPORTED_NAMES=('UMD_101_REVISION', 'OutcomeOption', 'OutcomeSchema', 'OutcomeSchemaResolver', 'build_umd_101_certification_manifest', 'verify_umd_101_outcome_schema_resolution')

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
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def write_exact(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker=f"# UMD-101 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {name},\n" for name in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None); importlib.invalidate_caches()
        mod=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(mod,n)]
        if missing: raise RuntimeError("UMD-101 missing symbols: "+", ".join(missing))
        verifier_name=[n for n in EXPORTED_NAMES if n.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True: raise RuntimeError("UMD-101 verification returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def sha256_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72); print(" UMD-101 INSTALLER"); print(" OUTCOME SCHEMA RESOLUTION"); print("="*72)
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
        for p,previous in backups.items():
            if previous is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(previous)
        importlib.invalidate_caches(); print("[ROLLBACK] UMD-101 installation failed; all affected files restored"); raise
    manifest={"build_id":'UMD-101',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,
        "files":{str(MODULE.relative_to(ROOT)):sha256_file(MODULE),str(INIT.relative_to(ROOT)):sha256_file(INIT),str(TEST.relative_to(ROOT)):sha256_file(TEST)},
        "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-101 INSTALLATION COMPLETE"); return 0

if __name__=="__main__": raise SystemExit(main())
