from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_171_CONVERGENCE_STATE_SNAPSHOT_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_171_convergence_state_snapshot.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_171_convergence_state_snapshot.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_170_convergence_market_registry import ConvergenceMarketRegistry,verify_umd_170_convergence_market_registry\n\nUMD_171_BUILD_ID="UMD-171"\nUMD_171_REVISION="UMD_171_CONVERGENCE_STATE_SNAPSHOT_V1"\nUMD_171_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _utc(value:datetime)->datetime:\n    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:\n        raise ValueError("as_of must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceStateRecord:\n    canonical_market_id:str\n    profile_hash:str\n    change_types:Tuple[str,...]\n    venue_keys:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"change_types",tuple(self.change_types))\n        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))\n        if self.change_types!=tuple(sorted(set(self.change_types))):\n            raise ValueError("change_types must be unique and sorted")\n        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):\n            raise ValueError("venue_keys must be unique and sorted")\n        if not self.canonical_market_id or not self.profile_hash:\n            raise ValueError("state record identifiers must be non-empty")\n\n    @property\n    def record_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "profile_hash":self.profile_hash,\n            "change_types":self.change_types,\n            "venue_keys":self.venue_keys,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceStateSnapshot:\n    as_of:datetime\n    registry_hash:str\n    records:Tuple[ConvergenceStateRecord,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"as_of",_utc(self.as_of))\n        object.__setattr__(self,"records",tuple(self.records))\n        if self.records!=tuple(sorted(self.records,key=lambda r:(r.canonical_market_id,r.record_hash))):\n            raise ValueError("records must be deterministically sorted")\n        if len({r.canonical_market_id for r in self.records})!=len(self.records):\n            raise ValueError("snapshot markets must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_171_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-171")\n        if self.registry_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include convergence market registry hash")\n\n    def record_for_market(self,market_id:str)->ConvergenceStateRecord|None:\n        for record in self.records:\n            if record.canonical_market_id==market_id:\n                return record\n        return None\n\n    @property\n    def snapshot_hash(self)->str:\n        return deterministic_sha256({\n            "as_of":self.as_of,\n            "registry_hash":self.registry_hash,\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceStateSnapshotBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        registry:ConvergenceMarketRegistry,\n        *,\n        as_of:datetime,\n        lineage:ImmutableLineage,\n    )->ConvergenceStateSnapshot:\n        if not isinstance(registry,ConvergenceMarketRegistry):\n            raise TypeError("registry must be ConvergenceMarketRegistry")\n        records=tuple(\n            ConvergenceStateRecord(\n                p.canonical_market_id,p.profile_hash,p.change_types,p.venue_keys\n            )\n            for p in registry.profiles\n        )\n        return ConvergenceStateSnapshot(as_of,registry.registry_hash,records,lineage)\n\ndef build_umd_171_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_171_BUILD_ID,"revision":UMD_171_REVISION,\n        "schema_version":UMD_171_SCHEMA_VERSION,"upstream_builds":("UMD-170",),\n        "mode":"deterministic_read_only_convergence_state_snapshot",\n        "semantics":"enriched_point_in_time_convergence_state_only",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_171_convergence_state_snapshot()->bool:\n    if verify_umd_170_convergence_market_registry() is not True:\n        return False\n    m=build_umd_171_certification_manifest()\n    return m["build_id"]=="UMD-171" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import ConvergenceMarketProfile\nfrom qseries_v2.universal_market_discovery.umd_170_convergence_market_registry import ConvergenceMarketRegistry\nfrom qseries_v2.universal_market_discovery.umd_171_convergence_state_snapshot import *\n\nFIXED=datetime(2026,8,10,16,20,tzinfo=timezone.utc)\n\ndef registry():\n    p1=ConvergenceMarketProfile(\n        "m1",("convergence-added",),("a"*64,),(),("kalshi","polymarket"),\n        ("asset=bitcoin",),("required",),("implies",),("impacted",)\n    )\n    p2=ConvergenceMarketProfile(\n        "m2",("convergence-composition-changed",),(),("b"*64,),("kalshi",),\n        ("metric=cpi",),("supporting",),("threshold_monotonic",),("boundary",)\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-170",revision="UMD_170_CONVERGENCE_MARKET_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash),\n        source_refs=("fixture://171/170",),created_at=FIXED\n    )\n    return ConvergenceMarketRegistry(\n        (p1,p2),\n        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},\n        {"a"*64:("m1",)},{"b"*64:("m2",)},\n        {"kalshi":("m1","m2"),"polymarket":("m1",)},\n        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},\n        {"required":("m1",),"supporting":("m2",)},\n        {"implies":("m1",),"threshold_monotonic":("m2",)},\n        {"impacted":("m1",),"boundary":("m2",)},\n        l\n    )\n\ndef lineage(r):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-171",revision=UMD_171_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.registry_hash,),\n        source_refs=("fixture://171",),created_at=FIXED\n    )\n\nclass TestUMD171(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_171_convergence_state_snapshot())\n    def test_snapshot(self):\n        r=registry()\n        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertEqual(tuple(x.canonical_market_id for x in s.records),("m1","m2"))\n        self.assertEqual(s.record_for_market("m1").venue_keys,("kalshi","polymarket"))\n    def test_profile_hash_preserved(self):\n        r=registry()\n        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertEqual(s.record_for_market("m2").profile_hash,r.get("m2").profile_hash)\n    def test_naive_time_rejected(self):\n        r=registry()\n        with self.assertRaises(ValueError):\n            ConvergenceStateSnapshotBuilder().build(\n                r,as_of=datetime(2026,8,10,16,20),lineage=lineage(r)\n            )\n    def test_unknown(self):\n        r=registry()\n        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertIsNone(s.record_for_market("missing"))\n    def test_deterministic(self):\n        r=registry(); l=lineage(r)\n        a=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        b=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        self.assertEqual(a.snapshot_hash,b.snapshot_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ConvergenceStateSnapshotBuilder().build(\n                object(),as_of=FIXED,\n                lineage=ImmutableLineage(\n                    subsystem_id="UMD",build_id="UMD-171",revision=UMD_171_REVISION,\n                    schema_version="1.0.0",parent_hashes=(),\n                    source_refs=("fixture://171/bad",),created_at=FIXED\n                )\n            )\n    def test_side_effects(self):\n        m=build_umd_171_certification_manifest()\n        self.assertEqual(m["semantics"],"enriched_point_in_time_convergence_state_only")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-171 CERTIFICATION TEST");print(" CONVERGENCE STATE SNAPSHOT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD171))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_171_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Enriched convergence market state captured in immutable timezone-aware snapshots")\n    print("[PASS] Canonical profile identity and exact venue coverage preserved")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-171 CERTIFIED")\n'
UPSTREAM_MODULE='umd_170_convergence_market_registry'
UPSTREAM_VERIFIER='verify_umd_170_convergence_market_registry'
EXPORTED_NAMES=('UMD_171_REVISION', 'ConvergenceStateRecord', 'ConvergenceStateSnapshot', 'ConvergenceStateSnapshotBuilder', 'build_umd_171_certification_manifest', 'verify_umd_171_convergence_state_snapshot')

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
    marker="# UMD-171 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {name},\n" for name in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None)
        importlib.invalidate_caches()
        mod=importlib.import_module(name)
        missing=[name for name in EXPORTED_NAMES if not hasattr(mod,name)]
        if missing:
            raise RuntimeError("UMD-171 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-171 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-171 INSTALLER")
    print(" CONVERGENCE STATE SNAPSHOT")
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
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-171 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-171',
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
    print("[DONE] UMD-171 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
