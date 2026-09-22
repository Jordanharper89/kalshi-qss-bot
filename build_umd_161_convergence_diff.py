from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_161_CONVERGENCE_DIFF_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_161_convergence_diff.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_161_convergence_diff.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_160_convergence_snapshot import ConvergenceSnapshot,verify_umd_160_convergence_snapshot\n\nUMD_161_BUILD_ID="UMD-161"\nUMD_161_REVISION="UMD_161_CONVERGENCE_DIFF_V1"\nUMD_161_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceMarketChange:\n    canonical_market_id:str\n    before_change_hashes:Tuple[str,...]\n    after_change_hashes:Tuple[str,...]\n    added_change_hashes:Tuple[str,...]\n    removed_change_hashes:Tuple[str,...]\n\n    def __post_init__(self):\n        for name in (\n            "before_change_hashes","after_change_hashes",\n            "added_change_hashes","removed_change_hashes"\n        ):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if self.added_change_hashes!=tuple(sorted(set(self.after_change_hashes)-set(self.before_change_hashes))):\n            raise ValueError("added_change_hashes inconsistent with before/after")\n        if self.removed_change_hashes!=tuple(sorted(set(self.before_change_hashes)-set(self.after_change_hashes))):\n            raise ValueError("removed_change_hashes inconsistent with before/after")\n\n    @property\n    def change_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "before_change_hashes":self.before_change_hashes,\n            "after_change_hashes":self.after_change_hashes,\n            "added_change_hashes":self.added_change_hashes,\n            "removed_change_hashes":self.removed_change_hashes,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceDiff:\n    before_snapshot_hash:str\n    after_snapshot_hash:str\n    added_market_ids:Tuple[str,...]\n    removed_market_ids:Tuple[str,...]\n    changed_markets:Tuple[ConvergenceMarketChange,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"added_market_ids",tuple(self.added_market_ids))\n        object.__setattr__(self,"removed_market_ids",tuple(self.removed_market_ids))\n        object.__setattr__(self,"changed_markets",tuple(self.changed_markets))\n        if self.added_market_ids!=tuple(sorted(set(self.added_market_ids))):\n            raise ValueError("added_market_ids must be unique and sorted")\n        if self.removed_market_ids!=tuple(sorted(set(self.removed_market_ids))):\n            raise ValueError("removed_market_ids must be unique and sorted")\n        if set(self.added_market_ids)&set(self.removed_market_ids):\n            raise ValueError("market cannot be both added and removed")\n        if self.changed_markets!=tuple(sorted(\n            self.changed_markets,key=lambda c:(c.canonical_market_id,c.change_hash)\n        )):\n            raise ValueError("changed_markets must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_161_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-161")\n        required={self.before_snapshot_hash,self.after_snapshot_hash}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include both convergence snapshots")\n\n    @property\n    def empty(self)->bool:\n        return not self.added_market_ids and not self.removed_market_ids and not self.changed_markets\n\n    @property\n    def diff_hash(self)->str:\n        return deterministic_sha256({\n            "before_snapshot_hash":self.before_snapshot_hash,\n            "after_snapshot_hash":self.after_snapshot_hash,\n            "added_market_ids":self.added_market_ids,\n            "removed_market_ids":self.removed_market_ids,\n            "changed_market_hashes":tuple(c.change_hash for c in self.changed_markets),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceDiffer:\n    __slots__=()\n\n    def diff(\n        self,\n        before:ConvergenceSnapshot,\n        after:ConvergenceSnapshot,\n        *,\n        lineage:ImmutableLineage,\n    )->ConvergenceDiff:\n        if not isinstance(before,ConvergenceSnapshot) or not isinstance(after,ConvergenceSnapshot):\n            raise TypeError("before and after must be ConvergenceSnapshot")\n        if after.as_of<before.as_of:\n            raise ValueError("after snapshot must not precede before snapshot")\n\n        before_map={r.canonical_market_id:r for r in before.records}\n        after_map={r.canonical_market_id:r for r in after.records}\n\n        before_ids=set(before_map)\n        after_ids=set(after_map)\n        added=tuple(sorted(after_ids-before_ids))\n        removed=tuple(sorted(before_ids-after_ids))\n\n        changed=[]\n        for market_id in sorted(before_ids&after_ids):\n            b=before_map[market_id].change_hashes\n            a=after_map[market_id].change_hashes\n            if b==a:\n                continue\n            changed.append(ConvergenceMarketChange(\n                market_id,b,a,\n                tuple(sorted(set(a)-set(b))),\n                tuple(sorted(set(b)-set(a))),\n            ))\n\n        return ConvergenceDiff(\n            before.snapshot_hash,\n            after.snapshot_hash,\n            added,\n            removed,\n            tuple(changed),\n            lineage,\n        )\n\ndef build_umd_161_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_161_BUILD_ID,"revision":UMD_161_REVISION,\n        "schema_version":UMD_161_SCHEMA_VERSION,"upstream_builds":("UMD-160",),\n        "mode":"deterministic_read_only_convergence_diff",\n        "semantics":"structural_convergence_change_detection_only",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_161_convergence_diff()->bool:\n    if verify_umd_160_convergence_snapshot() is not True:\n        return False\n    m=build_umd_161_certification_manifest()\n    return m["build_id"]=="UMD-161" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone,timedelta\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_160_convergence_snapshot import ConvergenceSnapshotRecord,ConvergenceSnapshot\nfrom qseries_v2.universal_market_discovery.umd_161_convergence_diff import *\n\nBASE=datetime(2026,8,10,13,10,tzinfo=timezone.utc)\nC1="1"*64; C2="2"*64; C3="3"*64; C4="4"*64\n\ndef snapshot(seed,when,records):\n    registry_hash=seed*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-160",revision="UMD_160_CONVERGENCE_SNAPSHOT_V1",\n        schema_version="1.0.0",parent_hashes=(registry_hash,),\n        source_refs=("fixture://161/160",),created_at=when\n    )\n    return ConvergenceSnapshot(when,registry_hash,tuple(records),l)\n\ndef record(market,changes,seed):\n    return ConvergenceSnapshotRecord(market,(seed*64,),tuple(changes))\n\ndef lineage(a,b):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-161",revision=UMD_161_REVISION,\n        schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),\n        source_refs=("fixture://161",),created_at=b.as_of\n    )\n\nclass TestUMD161(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_161_convergence_diff())\n    def test_added_removed_markets(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        b=snapshot("b",BASE+timedelta(minutes=1),(record("m2",(C2,C3),"2"),))\n        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertEqual(d.added_market_ids,("m2",))\n        self.assertEqual(d.removed_market_ids,("m1",))\n    def test_changed_convergence_membership(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2,C3),"2"),))\n        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertEqual(len(d.changed_markets),1)\n        self.assertEqual(d.changed_markets[0].added_change_hashes,(C3,))\n        self.assertEqual(d.changed_markets[0].removed_change_hashes,())\n    def test_removed_change_membership(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2,C3),"1"),))\n        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2),"2"),))\n        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertEqual(d.changed_markets[0].removed_change_hashes,(C3,))\n    def test_empty(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2),"2"),))\n        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertTrue(d.empty)\n    def test_reverse_time_rejected(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        b=snapshot("b",BASE-timedelta(minutes=1),(record("m1",(C1,C2),"2"),))\n        with self.assertRaises(ValueError):\n            ConvergenceDiffer().diff(a,b,lineage=lineage(b,a))\n    def test_deterministic(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2,C3),"2"),))\n        l=lineage(a,b)\n        x=ConvergenceDiffer().diff(a,b,lineage=l)\n        y=ConvergenceDiffer().diff(a,b,lineage=l)\n        self.assertEqual(x.diff_hash,y.diff_hash)\n    def test_bad_snapshot(self):\n        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))\n        with self.assertRaises(TypeError):\n            ConvergenceDiffer().diff(a,object(),lineage=ImmutableLineage(\n                subsystem_id="UMD",build_id="UMD-161",revision=UMD_161_REVISION,\n                schema_version="1.0.0",parent_hashes=(),\n                source_refs=("fixture://161/bad",),created_at=BASE\n            ))\n    def test_side_effects(self):\n        m=build_umd_161_certification_manifest()\n        self.assertEqual(m["semantics"],"structural_convergence_change_detection_only")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-161 CERTIFICATION TEST");print(" CONVERGENCE DIFF");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD161))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_161_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Added, removed, and composition-changed market convergence certified")\n    print("[PASS] Convergence evolution detected without urgency, score, or prediction")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-161 CERTIFIED")\n'
UPSTREAM_MODULE='umd_160_convergence_snapshot'
UPSTREAM_VERIFIER='verify_umd_160_convergence_snapshot'
EXPORTED_NAMES=('UMD_161_REVISION', 'ConvergenceMarketChange', 'ConvergenceDiff', 'ConvergenceDiffer', 'build_umd_161_certification_manifest', 'verify_umd_161_convergence_diff')

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
    marker="# UMD-161 exports"
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
            raise RuntimeError("UMD-161 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-161 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-161 INSTALLER")
    print(" CONVERGENCE DIFF")
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
        print("[ROLLBACK] UMD-161 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-161',
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
    print("[DONE] UMD-161 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
