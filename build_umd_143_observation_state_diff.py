from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_143_OBSERVATION_STATE_DIFF_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_143_observation_state_diff.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_143_observation_state_diff.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_142_observation_state_snapshot import ObservationStateSnapshot,verify_umd_142_observation_state_snapshot\n\nUMD_143_BUILD_ID="UMD-143"\nUMD_143_REVISION="UMD_143_OBSERVATION_STATE_DIFF_V1"\nUMD_143_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ObservationStateDiff:\n    before_snapshot_hash:str\n    after_snapshot_hash:str\n    added_canonical_ids:Tuple[str,...]\n    removed_canonical_ids:Tuple[str,...]\n    added_cluster_ids:Tuple[str,...]\n    removed_cluster_ids:Tuple[str,...]\n    added_contradictions:Tuple[Tuple[str,str],...]\n    removed_contradictions:Tuple[Tuple[str,str],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in (\n            "added_canonical_ids","removed_canonical_ids","added_cluster_ids","removed_cluster_ids",\n            "added_contradictions","removed_contradictions"\n        ):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if set(self.added_canonical_ids)&set(self.removed_canonical_ids):\n            raise ValueError("canonical id cannot be both added and removed")\n        if set(self.added_cluster_ids)&set(self.removed_cluster_ids):\n            raise ValueError("cluster id cannot be both added and removed")\n        if set(self.added_contradictions)&set(self.removed_contradictions):\n            raise ValueError("contradiction cannot be both added and removed")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_143_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-143")\n        required={self.before_snapshot_hash,self.after_snapshot_hash}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include both snapshot hashes")\n\n    @property\n    def empty(self)->bool:\n        return not any((\n            self.added_canonical_ids,self.removed_canonical_ids,\n            self.added_cluster_ids,self.removed_cluster_ids,\n            self.added_contradictions,self.removed_contradictions,\n        ))\n\n    @property\n    def diff_hash(self)->str:\n        return deterministic_sha256({\n            "before_snapshot_hash":self.before_snapshot_hash,\n            "after_snapshot_hash":self.after_snapshot_hash,\n            "added_canonical_ids":self.added_canonical_ids,\n            "removed_canonical_ids":self.removed_canonical_ids,\n            "added_cluster_ids":self.added_cluster_ids,\n            "removed_cluster_ids":self.removed_cluster_ids,\n            "added_contradictions":self.added_contradictions,\n            "removed_contradictions":self.removed_contradictions,\n            "lineage":self.lineage,\n        })\n\nclass ObservationStateDiffer:\n    __slots__=()\n\n    def diff(\n        self,\n        before:ObservationStateSnapshot,\n        after:ObservationStateSnapshot,\n        *,\n        lineage:ImmutableLineage,\n    )->ObservationStateDiff:\n        if not isinstance(before,ObservationStateSnapshot) or not isinstance(after,ObservationStateSnapshot):\n            raise TypeError("before and after must be ObservationStateSnapshot")\n        if after.as_of<before.as_of:\n            raise ValueError("after snapshot must not precede before snapshot")\n\n        before_obs=set(before.canonical_observation_ids)\n        after_obs=set(after.canonical_observation_ids)\n        before_clusters=set(before.cluster_ids)\n        after_clusters=set(after.cluster_ids)\n        before_contra=set(before.contradiction_pairs)\n        after_contra=set(after.contradiction_pairs)\n\n        return ObservationStateDiff(\n            before.snapshot_hash,\n            after.snapshot_hash,\n            tuple(sorted(after_obs-before_obs)),\n            tuple(sorted(before_obs-after_obs)),\n            tuple(sorted(after_clusters-before_clusters)),\n            tuple(sorted(before_clusters-after_clusters)),\n            tuple(sorted(after_contra-before_contra)),\n            tuple(sorted(before_contra-after_contra)),\n            lineage,\n        )\n\ndef build_umd_143_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_143_BUILD_ID,"revision":UMD_143_REVISION,\n        "schema_version":UMD_143_SCHEMA_VERSION,"upstream_builds":("UMD-142",),\n        "mode":"deterministic_read_only_observation_state_diff",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_143_observation_state_diff()->bool:\n    if verify_umd_142_observation_state_snapshot() is not True:\n        return False\n    m=build_umd_143_certification_manifest()\n    return m["build_id"]=="UMD-143" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone,timedelta\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_142_observation_state_snapshot import ObservationStateSnapshot\nfrom qseries_v2.universal_market_discovery.umd_143_observation_state_diff import *\n\nBASE=datetime(2026,8,10,6,0,tzinfo=timezone.utc)\n\ndef snap(seed,when,obs,clusters,contra):\n    registry_hash=seed*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision="UMD_142_OBSERVATION_STATE_SNAPSHOT_V1",\n        schema_version="1.0.0",parent_hashes=(registry_hash,),source_refs=("fixture://143/142",),created_at=when)\n    return ObservationStateSnapshot(when,registry_hash,tuple(obs),tuple(clusters),tuple(contra),l)\n\ndef lineage(a,b):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-143",revision=UMD_143_REVISION,\n        schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),\n        source_refs=("fixture://143",),created_at=b.as_of)\n\nclass TestUMD143(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_143_observation_state_diff())\n    def test_additions(self):\n        a=snap("a",BASE,("obs-a",),("c1",),())\n        b=snap("b",BASE+timedelta(minutes=1),("obs-a","obs-b"),("c1","c2"),(("obs-a","obs-b"),))\n        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertEqual(d.added_canonical_ids,("obs-b",))\n        self.assertEqual(d.added_cluster_ids,("c2",))\n        self.assertEqual(d.added_contradictions,(("obs-a","obs-b"),))\n    def test_removals(self):\n        a=snap("a",BASE,("obs-a","obs-b"),("c1","c2"),(("obs-a","obs-b"),))\n        b=snap("b",BASE+timedelta(minutes=1),("obs-a",),("c1",),())\n        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertEqual(d.removed_canonical_ids,("obs-b",))\n        self.assertEqual(d.removed_cluster_ids,("c2",))\n        self.assertEqual(d.removed_contradictions,(("obs-a","obs-b"),))\n    def test_empty_diff(self):\n        a=snap("a",BASE,("obs-a",),("c1",),())\n        b=snap("b",BASE+timedelta(minutes=1),("obs-a",),("c1",),())\n        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))\n        self.assertTrue(d.empty)\n    def test_reverse_time_rejected(self):\n        a=snap("a",BASE,("obs-a",),(),())\n        b=snap("b",BASE-timedelta(minutes=1),("obs-a",),(),())\n        with self.assertRaises(ValueError):\n            ObservationStateDiffer().diff(a,b,lineage=lineage(b,a))\n    def test_bad_snapshot(self):\n        a=snap("a",BASE,("obs-a",),(),())\n        with self.assertRaises(TypeError):\n            ObservationStateDiffer().diff(a,object(),lineage=ImmutableLineage(\n                subsystem_id="UMD",build_id="UMD-143",revision=UMD_143_REVISION,\n                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://143/bad",),created_at=BASE))\n    def test_deterministic(self):\n        a=snap("a",BASE,("obs-a",),(),())\n        b=snap("b",BASE+timedelta(minutes=1),("obs-a","obs-b"),(),())\n        l=lineage(a,b)\n        x=ObservationStateDiffer().diff(a,b,lineage=l)\n        y=ObservationStateDiffer().diff(a,b,lineage=l)\n        self.assertEqual(x.diff_hash,y.diff_hash)\n    def test_side_effects(self):\n        m=build_umd_143_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-143 CERTIFICATION TEST");print(" OBSERVATION STATE DIFF");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD143))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_143_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Added and removed observation-state structure certified")\n    print("[PASS] Canonical observations, clusters, and contradiction changes diffed deterministically")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-143 CERTIFIED")\n'
UPSTREAM_MODULE='umd_142_observation_state_snapshot'
UPSTREAM_VERIFIER='verify_umd_142_observation_state_snapshot'
EXPORTED_NAMES=('UMD_143_REVISION', 'ObservationStateDiff', 'ObservationStateDiffer', 'build_umd_143_certification_manifest', 'verify_umd_143_observation_state_diff')

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
    marker="# UMD-143 exports"
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
            raise RuntimeError("UMD-143 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-143 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-143 INSTALLER")
    print(" OBSERVATION STATE DIFF")
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
        print("[ROLLBACK] UMD-143 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-143',
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
    print("[DONE] UMD-143 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
