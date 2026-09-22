from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_142_OBSERVATION_STATE_SNAPSHOT_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_142_observation_state_snapshot.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_142_observation_state_snapshot.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_141_observation_state_registry import ObservationStateRegistry, verify_umd_141_observation_state_registry\n\nUMD_142_BUILD_ID="UMD-142"\nUMD_142_REVISION="UMD_142_OBSERVATION_STATE_SNAPSHOT_V1"\nUMD_142_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _utc(value:datetime)->datetime:\n    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:\n        raise ValueError("as_of must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n@dataclass(frozen=True,slots=True)\nclass ObservationStateSnapshot:\n    as_of:datetime\n    registry_hash:str\n    canonical_observation_ids:Tuple[str,...]\n    cluster_ids:Tuple[str,...]\n    contradiction_pairs:Tuple[Tuple[str,str],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"as_of",_utc(self.as_of))\n        object.__setattr__(self,"canonical_observation_ids",tuple(self.canonical_observation_ids))\n        object.__setattr__(self,"cluster_ids",tuple(self.cluster_ids))\n        object.__setattr__(self,"contradiction_pairs",tuple(self.contradiction_pairs))\n        for name in ("canonical_observation_ids","cluster_ids"):\n            value=getattr(self,name)\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n        if self.contradiction_pairs!=tuple(sorted(set(self.contradiction_pairs))):\n            raise ValueError("contradiction_pairs must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_142_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-142")\n        if self.registry_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include state registry hash")\n\n    @property\n    def snapshot_hash(self)->str:\n        return deterministic_sha256({\n            "as_of":self.as_of,\n            "registry_hash":self.registry_hash,\n            "canonical_observation_ids":self.canonical_observation_ids,\n            "cluster_ids":self.cluster_ids,\n            "contradiction_pairs":self.contradiction_pairs,\n            "lineage":self.lineage,\n        })\n\nclass ObservationStateSnapshotBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        registry:ObservationStateRegistry,\n        *,\n        as_of:datetime,\n        lineage:ImmutableLineage,\n    )->ObservationStateSnapshot:\n        if not isinstance(registry,ObservationStateRegistry):\n            raise TypeError("registry must be ObservationStateRegistry")\n\n        canonical=tuple(sorted({m.canonical_observation_id for m in registry.merges}))\n        clusters=tuple(sorted({c.cluster_id for c in registry.clusters}))\n        pairs=set()\n\n        known_canonical=set(canonical)\n        for merge in registry.merges:\n            for peer in merge.contradiction_peer_ids:\n                left=merge.canonical_observation_id\n                right=registry.canonical_for(peer) or peer\n                if left==right:\n                    continue\n                pair=tuple(sorted((left,right)))\n                pairs.add(pair)\n\n        return ObservationStateSnapshot(\n            as_of,\n            registry.registry_hash,\n            canonical,\n            clusters,\n            tuple(sorted(pairs)),\n            lineage,\n        )\n\ndef build_umd_142_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_142_BUILD_ID,"revision":UMD_142_REVISION,\n        "schema_version":UMD_142_SCHEMA_VERSION,"upstream_builds":("UMD-141",),\n        "mode":"deterministic_read_only_observation_state_snapshot",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_142_observation_state_snapshot()->bool:\n    if verify_umd_141_observation_state_registry() is not True:\n        return False\n    m=build_umd_142_certification_manifest()\n    return m["build_id"]=="UMD-142" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge\nfrom qseries_v2.universal_market_discovery.umd_140_observation_cluster import ObservationCluster\nfrom qseries_v2.universal_market_discovery.umd_141_observation_state_registry import ObservationStateRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_142_observation_state_snapshot import *\n\nFIXED=datetime(2026,8,10,5,0,tzinfo=timezone.utc)\n\ndef merge(canonical,members,peers,seed):\n    g=seed*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://142/139",),created_at=FIXED)\n    return ObservationMerge(canonical,tuple(members),tuple(x for x in members if x!=canonical),tuple(peers),g,l)\n\ndef cluster(cid,ms):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision="UMD_140_OBSERVATION_CLUSTER_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),\n        source_refs=("fixture://142/140",),created_at=FIXED)\n    return ObservationCluster(\n        cid,\n        tuple(sorted(m.canonical_observation_id for m in ms)),\n        tuple(sorted({x for m in ms for x in m.member_observation_ids})),\n        (),\n        tuple(sorted(m.merge_hash for m in ms)),\n        l,\n    )\n\ndef lf141(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-141",revision="UMD_141_OBSERVATION_STATE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://142/141",),created_at=FIXED)\n\ndef registry():\n    a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")\n    c=merge("obs-c",("obs-c",),("obs-a",),"b")\n    cl=cluster("cluster-1",(a,c))\n    return ObservationStateRegistryBuilder().build((a,c),(cl,),lineage_factory=lf141)\n\ndef lineage(r):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.registry_hash,),\n        source_refs=("fixture://142",),created_at=FIXED)\n\nclass TestUMD142(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_142_observation_state_snapshot())\n    def test_snapshot(self):\n        r=registry()\n        s=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))\n        self.assertEqual(s.canonical_observation_ids,("obs-a","obs-c"))\n        self.assertEqual(s.cluster_ids,("cluster-1",))\n        self.assertEqual(s.contradiction_pairs,(("obs-a","obs-c"),))\n    def test_utc_normalization(self):\n        r=registry()\n        local=datetime(2026,8,10,0,0,tzinfo=timezone.utc)\n        s=ObservationStateSnapshotBuilder().build(r,as_of=local,lineage=lineage(r))\n        self.assertEqual(s.as_of,local)\n    def test_naive_time_rejected(self):\n        r=registry()\n        with self.assertRaises(ValueError):\n            ObservationStateSnapshotBuilder().build(r,as_of=datetime(2026,8,10,5,0),lineage=lineage(r))\n    def test_lineage_required(self):\n        r=registry()\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://142/bad",),created_at=FIXED)\n        with self.assertRaises(ValueError):\n            ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=bad)\n    def test_deterministic(self):\n        r=registry(); l=lineage(r)\n        a=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        b=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)\n        self.assertEqual(a.snapshot_hash,b.snapshot_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ObservationStateSnapshotBuilder().build(object(),as_of=FIXED,lineage=ImmutableLineage(\n                subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,\n                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://142/bad",),created_at=FIXED))\n    def test_side_effects(self):\n        m=build_umd_142_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-142 CERTIFICATION TEST");print(" OBSERVATION STATE SNAPSHOT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD142))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_142_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Immutable timezone-aware observation state snapshots certified")\n    print("[PASS] Canonical observations, clusters, and contradiction pairs captured deterministically")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-142 CERTIFIED")\n'
UPSTREAM_MODULE='umd_141_observation_state_registry'
UPSTREAM_VERIFIER='verify_umd_141_observation_state_registry'
EXPORTED_NAMES=('UMD_142_REVISION', 'ObservationStateSnapshot', 'ObservationStateSnapshotBuilder', 'build_umd_142_certification_manifest', 'verify_umd_142_observation_state_snapshot')

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
    marker="# UMD-142 exports"
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
            raise RuntimeError("UMD-142 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-142 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-142 INSTALLER")
    print(" OBSERVATION STATE SNAPSHOT")
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
        print("[ROLLBACK] UMD-142 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-142',
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
    print("[DONE] UMD-142 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
