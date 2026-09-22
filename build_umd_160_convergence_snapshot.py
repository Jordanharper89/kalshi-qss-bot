from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_160_CONVERGENCE_SNAPSHOT_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_160_convergence_snapshot.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_160_convergence_snapshot.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_159_change_convergence_registry import ChangeConvergenceRegistry,verify_umd_159_change_convergence_registry\n\nUMD_160_BUILD_ID="UMD-160"\nUMD_160_REVISION="UMD_160_CONVERGENCE_SNAPSHOT_V1"\nUMD_160_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _utc(value:datetime)->datetime:\n    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:\n        raise ValueError("as_of must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceSnapshotRecord:\n    canonical_market_id:str\n    convergence_hashes:Tuple[str,...]\n    change_hashes:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"convergence_hashes",tuple(self.convergence_hashes))\n        object.__setattr__(self,"change_hashes",tuple(self.change_hashes))\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        if self.convergence_hashes!=tuple(sorted(set(self.convergence_hashes))):\n            raise ValueError("convergence_hashes must be unique and sorted")\n        if self.change_hashes!=tuple(sorted(set(self.change_hashes))):\n            raise ValueError("change_hashes must be unique and sorted")\n        if not self.convergence_hashes:\n            raise ValueError("snapshot record requires convergence")\n        if len(self.change_hashes)<2:\n            raise ValueError("snapshot convergence requires at least two distinct changes")\n\n    @property\n    def record_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "convergence_hashes":self.convergence_hashes,\n            "change_hashes":self.change_hashes,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceSnapshot:\n    as_of:datetime\n    registry_hash:str\n    records:Tuple[ConvergenceSnapshotRecord,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"as_of",_utc(self.as_of))\n        object.__setattr__(self,"records",tuple(self.records))\n        if self.records!=tuple(sorted(self.records,key=lambda r:(r.canonical_market_id,r.record_hash))):\n            raise ValueError("records must be deterministically sorted")\n        if len({r.canonical_market_id for r in self.records})!=len(self.records):\n            raise ValueError("snapshot markets must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_160_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-160")\n        if self.registry_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include convergence registry hash")\n\n    def record_for_market(self,market_id:str)->ConvergenceSnapshotRecord|None:\n        for record in self.records:\n            if record.canonical_market_id==market_id:\n                return record\n        return None\n\n    @property\n    def snapshot_hash(self)->str:\n        return deterministic_sha256({\n            "as_of":self.as_of,\n            "registry_hash":self.registry_hash,\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceSnapshotBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        registry:ChangeConvergenceRegistry,\n        *,\n        as_of:datetime,\n        lineage:ImmutableLineage,\n    )->ConvergenceSnapshot:\n        if not isinstance(registry,ChangeConvergenceRegistry):\n            raise TypeError("registry must be ChangeConvergenceRegistry")\n\n        changes_by_market={}\n        for change_hash,markets in registry.change_index.items():\n            for market_id in markets:\n                changes_by_market.setdefault(market_id,[]).append(change_hash)\n\n        records=[]\n        for market_id,convergence_hashes in sorted(registry.market_index.items()):\n            changes=tuple(sorted(set(changes_by_market.get(market_id,()))))\n            if len(changes)<2:\n                raise ValueError("convergence registry market lacks two distinct changes")\n            records.append(ConvergenceSnapshotRecord(\n                market_id,\n                tuple(sorted(set(convergence_hashes))),\n                changes,\n            ))\n\n        return ConvergenceSnapshot(\n            as_of,\n            registry.registry_hash,\n            tuple(records),\n            lineage,\n        )\n\ndef build_umd_160_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_160_BUILD_ID,"revision":UMD_160_REVISION,\n        "schema_version":UMD_160_SCHEMA_VERSION,"upstream_builds":("UMD-159",),\n        "mode":"deterministic_read_only_convergence_snapshot",\n        "semantics":"point_in_time_structural_convergence_only",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_160_convergence_snapshot()->bool:\n    if verify_umd_159_change_convergence_registry() is not True:\n        return False\n    m=build_umd_160_certification_manifest()\n    return m["build_id"]=="UMD-160" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import ChangeConvergence,ChangeConvergenceProjection\nfrom qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_160_convergence_snapshot import *\n\nFIXED=datetime(2026,8,10,13,0,tzinfo=timezone.utc)\nC1="1"*64; C2="2"*64; C3="3"*64\n\ndef projection(market,changes,seed):\n    conv=ChangeConvergence(\n        market,tuple(changes),("impacted",),(),(),(),(),seed*64\n    )\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-158",revision="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(conv.convergence_hash,),\n        source_refs=("fixture://160/158",),created_at=FIXED\n    )\n    return ChangeConvergenceProjection((conv,),l)\n\ndef registry():\n    p1=projection("m1",(C1,C2),"a")\n    p2=projection("m2",(C2,C3),"b")\n    def lf(parents):\n        return ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",\n            schema_version="1.0.0",parent_hashes=parents,\n            source_refs=("fixture://160/159",),created_at=FIXED\n        )\n    return ChangeConvergenceRegistryBuilder().build((p1,p2),lineage_factory=lf)\n\ndef lineage(r):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-160",revision=UMD_160_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.registry_hash,),\n        source_refs=("fixture://160",),created_at=FIXED\n    )\n\nclass TestUMD160(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_160_convergence_snapshot())\n    def test_snapshot(self):\n        r=registry()\n        s=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertEqual(tuple(x.canonical_market_id for x in s.records),("m1","m2"))\n        self.assertEqual(s.record_for_market("m1").change_hashes,(C1,C2))\n    def test_unknown_market(self):\n        r=registry()\n        s=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertIsNone(s.record_for_market("missing"))\n    def test_naive_time_rejected(self):\n        r=registry()\n        with self.assertRaises(ValueError):\n            ConvergenceSnapshotBuilder().build(\n                r,as_of=datetime(2026,8,10,13,0),lineage=lineage(r)\n            )\n    def test_deterministic(self):\n        r=registry(); l=lineage(r)\n        a=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        b=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        self.assertEqual(a.snapshot_hash,b.snapshot_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ConvergenceSnapshotBuilder().build(\n                object(),as_of=FIXED,\n                lineage=ImmutableLineage(\n                    subsystem_id="UMD",build_id="UMD-160",revision=UMD_160_REVISION,\n                    schema_version="1.0.0",parent_hashes=(),\n                    source_refs=("fixture://160/bad",),created_at=FIXED\n                )\n            )\n    def test_side_effects(self):\n        m=build_umd_160_certification_manifest()\n        self.assertEqual(m["semantics"],"point_in_time_structural_convergence_only")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-160 CERTIFICATION TEST");print(" CONVERGENCE SNAPSHOT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD160))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_160_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Immutable timezone-aware multi-change convergence snapshots certified")\n    print("[PASS] Market convergence membership and contributing changes captured deterministically")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-160 CERTIFIED")\n'
UPSTREAM_MODULE='umd_159_change_convergence_registry'
UPSTREAM_VERIFIER='verify_umd_159_change_convergence_registry'
EXPORTED_NAMES=('UMD_160_REVISION', 'ConvergenceSnapshotRecord', 'ConvergenceSnapshot', 'ConvergenceSnapshotBuilder', 'build_umd_160_certification_manifest', 'verify_umd_160_convergence_snapshot')

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
    marker="# UMD-160 exports"
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
            raise RuntimeError("UMD-160 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-160 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-160 INSTALLER")
    print(" CONVERGENCE SNAPSHOT")
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
        print("[ROLLBACK] UMD-160 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-160',
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
    print("[DONE] UMD-160 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
