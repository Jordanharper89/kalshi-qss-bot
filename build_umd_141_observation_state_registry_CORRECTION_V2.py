from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_141_OBSERVATION_STATE_REGISTRY_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_141_observation_state_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_141_observation_state_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_139_observation_merge import ObservationMerge\nfrom .umd_140_observation_cluster import ObservationCluster,verify_umd_140_observation_cluster_model\n\nUMD_141_BUILD_ID="UMD-141"\nUMD_141_REVISION="UMD_141_OBSERVATION_STATE_REGISTRY_V1"\nUMD_141_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationStateRegistry:\n    merges:Tuple[ObservationMerge,...]\n    clusters:Tuple[ObservationCluster,...]\n    canonical_index:Mapping[str,Tuple[str,...]]\n    cluster_index:Mapping[str,Tuple[str,...]]\n    contradiction_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"merges",tuple(self.merges))\n        object.__setattr__(self,"clusters",tuple(self.clusters))\n        for name in ("canonical_index","cluster_index","contradiction_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.merges!=tuple(sorted(self.merges,key=lambda m:(m.canonical_observation_id,m.merge_hash))):\n            raise ValueError("merges must be deterministically sorted")\n        if self.clusters!=tuple(sorted(self.clusters,key=lambda c:(c.cluster_id,c.cluster_hash))):\n            raise ValueError("clusters must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_141_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-141")\n        required={m.merge_hash for m in self.merges}|{c.cluster_hash for c in self.clusters}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every merge and cluster hash")\n\n    def canonical_for(self,observation_id:str)->str|None:\n        values=self.canonical_index.get(observation_id,())\n        return values[0] if values else None\n\n    def clusters_for(self,observation_id:str)->Tuple[str,...]:\n        return self.cluster_index.get(observation_id,())\n\n    def contradictions_for(self,canonical_observation_id:str)->Tuple[str,...]:\n        return self.contradiction_index.get(canonical_observation_id,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "merge_hashes":tuple(m.merge_hash for m in self.merges),\n            "cluster_hashes":tuple(c.cluster_hash for c in self.clusters),\n            "canonical_index":self.canonical_index,\n            "cluster_index":self.cluster_index,\n            "contradiction_index":self.contradiction_index,\n            "lineage":self.lineage,\n        })\n\nclass ObservationStateRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        merges:Iterable[ObservationMerge],\n        clusters:Iterable[ObservationCluster],\n        *,\n        lineage_factory,\n    )->ObservationStateRegistry:\n        ms=tuple(merges)\n        cs=tuple(clusters)\n        if any(not isinstance(m,ObservationMerge) for m in ms):\n            raise TypeError("merges must contain ObservationMerge")\n        if any(not isinstance(c,ObservationCluster) for c in cs):\n            raise TypeError("clusters must contain ObservationCluster")\n\n        ms=tuple(sorted(ms,key=lambda m:(m.canonical_observation_id,m.merge_hash)))\n        cs=tuple(sorted(cs,key=lambda c:(c.cluster_id,c.cluster_hash)))\n\n        canonical={}\n        cluster={}\n        contradiction={}\n\n        for merge in ms:\n            for obs in merge.member_observation_ids:\n                existing=canonical.get(obs)\n                value=(merge.canonical_observation_id,)\n                if existing is not None and existing!=value:\n                    raise ValueError("observation belongs to more than one canonical merge")\n                canonical[obs]=value\n            contradiction[merge.canonical_observation_id]=merge.contradiction_peer_ids\n\n        for c in cs:\n            for obs in c.member_observation_ids:\n                cluster.setdefault(obs,[]).append(c.cluster_id)\n\n        for key,values in cluster.items():\n            cluster[key]=tuple(sorted(set(values)))\n\n        parents=tuple(m.merge_hash for m in ms)+tuple(c.cluster_hash for c in cs)\n        lineage=lineage_factory(parents)\n        return ObservationStateRegistry(ms,cs,canonical,cluster,contradiction,lineage)\n\ndef build_umd_141_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_141_BUILD_ID,"revision":UMD_141_REVISION,\n        "schema_version":UMD_141_SCHEMA_VERSION,"upstream_builds":("UMD-139","UMD-140"),\n        "mode":"deterministic_read_only_observation_state_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_141_observation_state_registry()->bool:\n    if verify_umd_140_observation_cluster_model() is not True:\n        return False\n    m=build_umd_141_certification_manifest()\n    return m["build_id"]=="UMD-141" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge\nfrom qseries_v2.universal_market_discovery.umd_140_observation_cluster import ObservationCluster\nfrom qseries_v2.universal_market_discovery.umd_141_observation_state_registry import *\n\nFIXED=datetime(2026,8,10,4,20,tzinfo=timezone.utc)\n\ndef merge(canonical,members,peers,seed):\n    g=seed*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://141/139",),created_at=FIXED)\n    return ObservationMerge(canonical,tuple(members),tuple(x for x in members if x!=canonical),tuple(peers),g,l)\n\ndef cluster(cid,ms):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision="UMD_140_OBSERVATION_CLUSTER_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),\n        source_refs=("fixture://141/140",),created_at=FIXED)\n    return ObservationCluster(\n        cid,\n        tuple(sorted(m.canonical_observation_id for m in ms)),\n        tuple(sorted({x for m in ms for x in m.member_observation_ids})),\n        (),\n        tuple(sorted(m.merge_hash for m in ms)),\n        l,\n    )\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-141",revision=UMD_141_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://141",),created_at=FIXED)\n\nclass TestUMD141(unittest.TestCase):\n    def setUp(self):\n        self.a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")\n        self.c=merge("obs-c",("obs-c",),("obs-a",),"b")\n        self.cluster=cluster("cluster-1",(self.a,self.c))\n        self.r=ObservationStateRegistryBuilder().build((self.c,self.a),(self.cluster,),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_141_observation_state_registry())\n    def test_canonical_query(self):\n        self.assertEqual(self.r.canonical_for("obs-b"),"obs-a")\n        self.assertEqual(self.r.canonical_for("obs-c"),"obs-c")\n    def test_cluster_query(self):\n        self.assertEqual(self.r.clusters_for("obs-b"),("cluster-1",))\n    def test_contradiction_query(self):\n        self.assertEqual(self.r.contradictions_for("obs-a"),("obs-c",))\n    def test_unknown(self):\n        self.assertIsNone(self.r.canonical_for("missing"))\n        self.assertEqual(self.r.clusters_for("missing"),())\n    def test_deterministic(self):\n        x=ObservationStateRegistryBuilder().build((self.a,self.c),(self.cluster,),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_overlap_rejected(self):\n        # Valid UMD-139 merge whose canonical observation is the first sorted member.\n        # It intentionally overlaps self.a on obs-b so UMD-141 must reject ownership conflict.\n        other=merge("obs-b",("obs-b","obs-z"),(),"c")\n        with self.assertRaises(ValueError):\n            ObservationStateRegistryBuilder().build((self.a,other),(),lineage_factory=lf)\n    def test_overlap_fixture_is_valid_umd139(self):\n        other=merge("obs-b",("obs-b","obs-z"),(),"c")\n        self.assertEqual(other.canonical_observation_id,"obs-b")\n        self.assertEqual(other.member_observation_ids,("obs-b","obs-z"))\n\n    def test_bad_cluster(self):\n        with self.assertRaises(TypeError):\n            ObservationStateRegistryBuilder().build((self.a,),(object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_141_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-141 CERTIFICATION TEST");print(" OBSERVATION STATE REGISTRY — CORRECTION V2");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD141))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_141_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical observation state and cluster membership queries certified")\n    print("[PASS] Contradiction preservation and conflicting merge ownership rejection certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-141 CERTIFIED")\n'
UPSTREAM_MODULE='umd_140_observation_cluster'
UPSTREAM_VERIFIER='verify_umd_140_observation_cluster_model'
EXPORTED_NAMES=('UMD_141_REVISION', 'ObservationStateRegistry', 'ObservationStateRegistryBuilder', 'build_umd_141_certification_manifest', 'verify_umd_141_observation_state_registry')

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
    marker="# UMD-141 exports"
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
            raise RuntimeError("UMD-141 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-141 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-141 INSTALLER")
    print(" OBSERVATION STATE REGISTRY")
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
        print("[ROLLBACK] UMD-141 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-141',
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
    print("[DONE] UMD-141 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
