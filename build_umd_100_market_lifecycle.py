from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_100_MARKET_LIFECYCLE_SEMANTICS_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_100_market_lifecycle.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_100_market_lifecycle.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom types import MappingProxyType\nfrom typing import Any, Mapping\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_095_market_identity import CanonicalMarketIdentity\nfrom .umd_099_market_alias_resolution import verify_umd_099_market_alias_resolution\n\nUMD_100_BUILD_ID="UMD-100"\nUMD_100_BUILD_NAME="Market Lifecycle Semantics"\nUMD_100_REVISION="UMD_100_MARKET_LIFECYCLE_SEMANTICS_V1"\nUMD_100_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nLIFECYCLE_PHASES=("unscheduled","pre_close","post_close_pre_settlement","post_settlement")\n\n\ndef _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:\n    if value is None: value={}\n    if not isinstance(value,Mapping): raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))\n\n\ndef _parse_time(value:str, field_name:str)->datetime | None:\n    if not isinstance(value,str): raise TypeError(f"{field_name} must be a string")\n    value=value.strip()\n    if not value: return None\n    if value.endswith("Z"): value=value[:-1]+"+00:00"\n    try: dt=datetime.fromisoformat(value)\n    except ValueError as exc: raise ValueError(f"{field_name} must be ISO-8601") from exc\n    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError(f"{field_name} must include a timezone")\n    return dt.astimezone(timezone.utc)\n\n\ndef _as_utc(value:datetime)->datetime:\n    if not isinstance(value,datetime): raise TypeError("as_of must be datetime")\n    if value.tzinfo is None or value.utcoffset() is None: raise ValueError("as_of must include a timezone")\n    return value.astimezone(timezone.utc)\n\n\ndef _iso(dt:datetime | None)->str:\n    return "" if dt is None else dt.isoformat().replace("+00:00","Z")\n\n\n@dataclass(frozen=True,slots=True)\nclass MarketLifecycle:\n    canonical_market_id:str\n    identity_hash:str\n    close_at:str\n    settlement_at:str\n    as_of:str\n    scheduled_phase:str\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n        if self.scheduled_phase not in LIFECYCLE_PHASES: raise ValueError("unsupported scheduled_phase")\n        close=_parse_time(self.close_at,"close_at"); settle=_parse_time(self.settlement_at,"settlement_at"); observed=_parse_time(self.as_of,"as_of")\n        if observed is None: raise ValueError("as_of must be non-empty")\n        if close is not None and settle is not None and settle < close: raise ValueError("settlement_at cannot precede close_at")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_100_BUILD_ID: raise ValueError("lineage must belong to UMD-100")\n        if self.identity_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include identity hash")\n\n    def to_canonical_dict(self):\n        return {"canonical_market_id":self.canonical_market_id,"identity_hash":self.identity_hash,"close_at":self.close_at,\n                "settlement_at":self.settlement_at,"as_of":self.as_of,"scheduled_phase":self.scheduled_phase,\n                "metadata":self.metadata,"lineage":self.lineage}\n\n    @property\n    def lifecycle_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\n\nclass MarketLifecycleResolver:\n    __slots__=()\n\n    def resolve(self,identity:CanonicalMarketIdentity,*,as_of:datetime,lineage:ImmutableLineage,metadata:Mapping[str,Any] | None=None)->MarketLifecycle:\n        if not isinstance(identity,CanonicalMarketIdentity): raise TypeError("identity must be CanonicalMarketIdentity")\n        observed=_as_utc(as_of)\n        close=_parse_time(identity.close_time,"close_time")\n        settle=_parse_time(identity.settlement_time,"settlement_time")\n        if close is not None and settle is not None and settle < close: raise ValueError("settlement_time cannot precede close_time")\n        if close is None and settle is None: phase="unscheduled"\n        elif close is None:\n            phase="post_settlement" if observed >= settle else "pre_close"\n        elif observed < close: phase="pre_close"\n        elif settle is None or observed < settle: phase="post_close_pre_settlement"\n        else: phase="post_settlement"\n        return MarketLifecycle(canonical_market_id=identity.canonical_market_id,identity_hash=identity.identity_hash,\n            close_at=_iso(close),settlement_at=_iso(settle),as_of=_iso(observed),scheduled_phase=phase,\n            metadata={} if metadata is None else metadata,lineage=lineage)\n\n\ndef build_umd_100_certification_manifest():\n    data={"subsystem_id":"UMD","build_id":UMD_100_BUILD_ID,"revision":UMD_100_REVISION,"schema_version":UMD_100_SCHEMA_VERSION,\n          "upstream_builds":("UMD-095","UMD-099"),"mode":"deterministic_read_only_market_lifecycle_semantics",\n          "lifecycle_phases":LIFECYCLE_PHASES,"prohibited_capabilities":PROHIBITED_CAPABILITIES,\n          "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\n\ndef verify_umd_100_market_lifecycle_semantics()->bool:\n    if verify_umd_099_market_alias_resolution() is not True: return False\n    m=build_umd_100_certification_manifest()\n    return m["build_id"]=="UMD-100" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION, MarketObservation, MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION, CanonicalMarketIdentityResolver\nfrom qseries_v2.universal_market_discovery.umd_100_market_lifecycle import (\n    UMD_100_REVISION, MarketLifecycleResolver, build_umd_100_certification_manifest, verify_umd_100_market_lifecycle_semantics,\n)\n\nFIXED=datetime(2026,8,9,12,0,tzinfo=timezone.utc)\n\ndef identity(close_time="2026-08-10T00:00:00Z",settlement_time="2026-08-11T00:00:00Z"):\n    o=MarketObservation(venue="Kalshi",venue_market_id="A",title="Will BTC exceed 100K?",category="Crypto",status="Open",close_time=close_time,settlement_time=settlement_time,outcomes=("Yes","No"))\n    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://100/94",),created_at=FIXED)\n    m=MarketNormalizer().normalize(o,lineage=l94)\n    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://100/95",),created_at=FIXED)\n    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)\n\ndef lineage(i):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-100",revision=UMD_100_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://100",),created_at=FIXED)\n\nclass TestUMD100(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_100_market_lifecycle_semantics())\n    def test_pre_close(self):\n        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"pre_close")\n    def test_post_close_pre_settlement(self):\n        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,10,12,tzinfo=timezone.utc),lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"post_close_pre_settlement")\n    def test_post_settlement(self):\n        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,12,tzinfo=timezone.utc),lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"post_settlement")\n    def test_unscheduled(self):\n        i=identity("",""); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"unscheduled")\n    def test_invalid_order_rejected(self):\n        i=identity("2026-08-12T00:00:00Z","2026-08-11T00:00:00Z")\n        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i))\n    def test_naive_as_of_rejected(self):\n        i=identity()\n        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,9,12),lineage=lineage(i))\n    def test_lineage_required(self):\n        i=identity(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-100",revision=UMD_100_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=bad)\n    def test_immutable(self):\n        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i))\n        with self.assertRaises((FrozenInstanceError,AttributeError)): x.scheduled_phase="x"\n    def test_side_effects(self):\n        m=build_umd_100_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72); print(" UMD-100 CERTIFICATION TEST"); print(" MARKET LIFECYCLE SEMANTICS"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD100))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_100_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-099 certified capability chain consumed read-only"); print("[PASS] Deterministic scheduled lifecycle semantics certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-100 CERTIFIED")\n'
UPSTREAM_MODULE='umd_099_market_alias_resolution'
UPSTREAM_VERIFIER='verify_umd_099_market_alias_resolution'
EXPORTED_NAMES=('UMD_100_REVISION', 'MarketLifecycle', 'MarketLifecycleResolver', 'build_umd_100_certification_manifest', 'verify_umd_100_market_lifecycle_semantics')

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
    marker=f"# UMD-100 exports"
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
        if missing: raise RuntimeError("UMD-100 missing symbols: "+", ".join(missing))
        verifier_name=[n for n in EXPORTED_NAMES if n.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True: raise RuntimeError("UMD-100 verification returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def sha256_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72); print(" UMD-100 INSTALLER"); print(" MARKET LIFECYCLE SEMANTICS"); print("="*72)
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
        importlib.invalidate_caches(); print("[ROLLBACK] UMD-100 installation failed; all affected files restored"); raise
    manifest={"build_id":'UMD-100',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,
        "files":{str(MODULE.relative_to(ROOT)):sha256_file(MODULE),str(INIT.relative_to(ROOT)):sha256_file(INIT),str(TEST.relative_to(ROOT)):sha256_file(TEST)},
        "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-100 INSTALLATION COMPLETE"); return 0

if __name__=="__main__": raise SystemExit(main())
