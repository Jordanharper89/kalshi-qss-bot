from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_140_OBSERVATION_CLUSTER_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_140_observation_cluster.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_140_observation_cluster.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_139_observation_merge import ObservationMerge,verify_umd_139_observation_merge_resolution\n\nUMD_140_BUILD_ID="UMD-140"\nUMD_140_REVISION="UMD_140_OBSERVATION_CLUSTER_MODEL_V1"\nUMD_140_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ObservationCluster:\n    cluster_id:str\n    canonical_observation_ids:Tuple[str,...]\n    member_observation_ids:Tuple[str,...]\n    contradiction_links:Tuple[Tuple[str,str],...]\n    merge_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"canonical_observation_ids",tuple(self.canonical_observation_ids))\n        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))\n        object.__setattr__(self,"contradiction_links",tuple(self.contradiction_links))\n        object.__setattr__(self,"merge_hashes",tuple(self.merge_hashes))\n        for name in ("canonical_observation_ids","member_observation_ids","merge_hashes"):\n            value=getattr(self,name)\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n        if not self.cluster_id:\n            raise ValueError("cluster_id must be non-empty")\n        if self.contradiction_links!=tuple(sorted(set(self.contradiction_links))):\n            raise ValueError("contradiction_links must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_140_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-140")\n        if not set(self.merge_hashes).issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every merge hash")\n\n    @property\n    def cluster_hash(self)->str:\n        return deterministic_sha256({\n            "cluster_id":self.cluster_id,\n            "canonical_observation_ids":self.canonical_observation_ids,\n            "member_observation_ids":self.member_observation_ids,\n            "contradiction_links":self.contradiction_links,\n            "merge_hashes":self.merge_hashes,\n            "lineage":self.lineage,\n        })\n\nclass ObservationClusterBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        cluster_id:str,\n        merges:Iterable[ObservationMerge],\n        *,\n        lineage:ImmutableLineage,\n    )->ObservationCluster:\n        values=tuple(merges)\n        if any(not isinstance(m,ObservationMerge) for m in values):\n            raise TypeError("merges must contain ObservationMerge")\n        canonical=tuple(sorted(m.canonical_observation_id for m in values))\n        members=tuple(sorted({x for m in values for x in m.member_observation_ids}))\n        known=set(members)\n        links=set()\n        for merge in values:\n            for peer in merge.contradiction_peer_ids:\n                if peer in known:\n                    links.add(tuple(sorted((merge.canonical_observation_id,peer))))\n        hashes=tuple(sorted(m.merge_hash for m in values))\n        return ObservationCluster(cluster_id,canonical,members,tuple(sorted(links)),hashes,lineage)\n\ndef build_umd_140_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_140_BUILD_ID,"revision":UMD_140_REVISION,\n        "schema_version":UMD_140_SCHEMA_VERSION,"upstream_builds":("UMD-139",),\n        "mode":"deterministic_read_only_observation_cluster_model",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_140_observation_cluster_model()->bool:\n    if verify_umd_139_observation_merge_resolution() is not True:\n        return False\n    m=build_umd_140_certification_manifest()\n    return m["build_id"]=="UMD-140" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge\nfrom qseries_v2.universal_market_discovery.umd_140_observation_cluster import *\n\nFIXED=datetime(2026,8,10,4,10,tzinfo=timezone.utc)\n\ndef merge(canonical,members,peers,seed):\n    g=seed*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://140/139",),created_at=FIXED)\n    return ObservationMerge(\n        canonical,tuple(members),tuple(x for x in members if x!=canonical),\n        tuple(peers),g,l\n    )\n\ndef lineage(ms):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision=UMD_140_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),\n        source_refs=("fixture://140",),created_at=FIXED)\n\nclass TestUMD140(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_140_observation_cluster_model())\n    def test_cluster_build(self):\n        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")\n        c=merge("obs-c",("obs-c",),("obs-a",),"b")\n        x=ObservationClusterBuilder().build("cluster-1",(c,a),lineage=lineage((a,c)))\n        self.assertEqual(x.canonical_observation_ids,("obs-a","obs-c"))\n        self.assertEqual(x.member_observation_ids,("obs-a","obs-b","obs-c"))\n    def test_contradiction_link(self):\n        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")\n        c=merge("obs-c",("obs-c",),("obs-a",),"b")\n        x=ObservationClusterBuilder().build("cluster-1",(a,c),lineage=lineage((a,c)))\n        self.assertEqual(x.contradiction_links,(("obs-a","obs-c"),))\n    def test_external_peer_excluded(self):\n        a=merge("obs-a",("obs-a",),("outside",),"a")\n        x=ObservationClusterBuilder().build("cluster-1",(a,),lineage=lineage((a,)))\n        self.assertEqual(x.contradiction_links,())\n    def test_deterministic(self):\n        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")\n        c=merge("obs-c",("obs-c",),("obs-a",),"b")\n        x=ObservationClusterBuilder().build("cluster-1",(a,c),lineage=lineage((a,c)))\n        y=ObservationClusterBuilder().build("cluster-1",(c,a),lineage=lineage((a,c)))\n        self.assertEqual(x.cluster_hash,y.cluster_hash)\n    def test_bad_merge(self):\n        with self.assertRaises(TypeError):\n            ObservationClusterBuilder().build("cluster-1",(object(),),lineage=ImmutableLineage(\n                subsystem_id="UMD",build_id="UMD-140",revision=UMD_140_REVISION,\n                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://140/bad",),created_at=FIXED\n            ))\n    def test_side_effects(self):\n        m=build_umd_140_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-140 CERTIFICATION TEST");print(" OBSERVATION CLUSTER MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD140))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_140_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical observation clusters and internal contradiction links certified")\n    print("[PASS] External contradiction peers remain outside cluster membership")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-140 CERTIFIED")\n'
UPSTREAM_MODULE='umd_139_observation_merge'
UPSTREAM_VERIFIER='verify_umd_139_observation_merge_resolution'
EXPORTED_NAMES=('UMD_140_REVISION', 'ObservationCluster', 'ObservationClusterBuilder', 'build_umd_140_certification_manifest', 'verify_umd_140_observation_cluster_model')

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
    marker="# UMD-140 exports"
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
            raise RuntimeError("UMD-140 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-140 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-140 INSTALLER")
    print(" OBSERVATION CLUSTER MODEL")
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
        print("[ROLLBACK] UMD-140 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-140',
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
    print("[DONE] UMD-140 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
