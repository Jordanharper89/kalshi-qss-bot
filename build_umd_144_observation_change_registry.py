from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_144_OBSERVATION_CHANGE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_144_observation_change_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_144_observation_change_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_143_observation_state_diff import ObservationStateDiff,verify_umd_143_observation_state_diff\n\nUMD_144_BUILD_ID="UMD-144"\nUMD_144_REVISION="UMD_144_OBSERVATION_CHANGE_REGISTRY_V1"\nUMD_144_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\nCHANGE_TYPES=(\n    "canonical-added",\n    "canonical-removed",\n    "cluster-added",\n    "cluster-removed",\n    "contradiction-added",\n    "contradiction-removed",\n)\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationChangeRecord:\n    change_type:str\n    subject_key:str\n    diff_hash:str\n\n    def __post_init__(self):\n        if self.change_type not in CHANGE_TYPES:\n            raise ValueError("unsupported change type")\n        if not isinstance(self.subject_key,str) or not self.subject_key:\n            raise ValueError("subject_key must be non-empty")\n\n    @property\n    def change_hash(self)->str:\n        return deterministic_sha256({\n            "change_type":self.change_type,\n            "subject_key":self.subject_key,\n            "diff_hash":self.diff_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationChangeRegistry:\n    diffs:Tuple[ObservationStateDiff,...]\n    changes:Tuple[ObservationChangeRecord,...]\n    type_index:Mapping[str,Tuple[str,...]]\n    observation_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"diffs",tuple(self.diffs))\n        object.__setattr__(self,"changes",tuple(self.changes))\n        object.__setattr__(self,"type_index",_freeze(self.type_index))\n        object.__setattr__(self,"observation_index",_freeze(self.observation_index))\n        if self.diffs!=tuple(sorted(self.diffs,key=lambda d:d.diff_hash)):\n            raise ValueError("diffs must be deterministically sorted")\n        if self.changes!=tuple(sorted(self.changes,key=lambda c:(c.change_type,c.subject_key,c.diff_hash))):\n            raise ValueError("changes must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_144_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-144")\n        required={d.diff_hash for d in self.diffs}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every diff hash")\n\n    def subjects_for_type(self,change_type:str)->Tuple[str,...]:\n        return self.type_index.get(change_type,())\n\n    def changes_for_observation(self,observation_id:str)->Tuple[str,...]:\n        return self.observation_index.get(observation_id,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "diff_hashes":tuple(d.diff_hash for d in self.diffs),\n            "change_hashes":tuple(c.change_hash for c in self.changes),\n            "type_index":self.type_index,\n            "observation_index":self.observation_index,\n            "lineage":self.lineage,\n        })\n\nclass ObservationChangeRegistryBuilder:\n    __slots__=()\n\n    def build(self,diffs:Iterable[ObservationStateDiff],*,lineage_factory)->ObservationChangeRegistry:\n        values=tuple(diffs)\n        if any(not isinstance(d,ObservationStateDiff) for d in values):\n            raise TypeError("diffs must contain ObservationStateDiff")\n        values=tuple(sorted(values,key=lambda d:d.diff_hash))\n\n        changes=[]\n        type_index={}\n        observation_index={}\n\n        def add(kind,subject,diff_hash,obs_ids=()):\n            record=ObservationChangeRecord(kind,subject,diff_hash)\n            changes.append(record)\n            type_index.setdefault(kind,[]).append(subject)\n            for obs in obs_ids:\n                observation_index.setdefault(obs,[]).append(record.change_hash)\n\n        for diff in values:\n            for obs in diff.added_canonical_ids:\n                add("canonical-added",obs,diff.diff_hash,(obs,))\n            for obs in diff.removed_canonical_ids:\n                add("canonical-removed",obs,diff.diff_hash,(obs,))\n            for cluster in diff.added_cluster_ids:\n                add("cluster-added",cluster,diff.diff_hash)\n            for cluster in diff.removed_cluster_ids:\n                add("cluster-removed",cluster,diff.diff_hash)\n            for left,right in diff.added_contradictions:\n                subject=left+"|"+right\n                add("contradiction-added",subject,diff.diff_hash,(left,right))\n            for left,right in diff.removed_contradictions:\n                subject=left+"|"+right\n                add("contradiction-removed",subject,diff.diff_hash,(left,right))\n\n        changes.sort(key=lambda c:(c.change_type,c.subject_key,c.diff_hash))\n        for index in (type_index,observation_index):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        lineage=lineage_factory(tuple(d.diff_hash for d in values))\n        return ObservationChangeRegistry(values,tuple(changes),type_index,observation_index,lineage)\n\ndef build_umd_144_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_144_BUILD_ID,"revision":UMD_144_REVISION,\n        "schema_version":UMD_144_SCHEMA_VERSION,"upstream_builds":("UMD-143",),\n        "mode":"deterministic_read_only_observation_change_registry",\n        "change_types":CHANGE_TYPES,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_144_observation_change_registry()->bool:\n    if verify_umd_143_observation_state_diff() is not True:\n        return False\n    m=build_umd_144_certification_manifest()\n    return m["build_id"]=="UMD-144" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_143_observation_state_diff import ObservationStateDiff\nfrom qseries_v2.universal_market_discovery.umd_144_observation_change_registry import *\n\nFIXED=datetime(2026,8,10,7,0,tzinfo=timezone.utc)\n\ndef diff(seed,added=(),removed=(),clusters_a=(),clusters_r=(),contra_a=(),contra_r=()):\n    before=seed*64\n    after=chr(ord(seed)+1)*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-143",revision="UMD_143_OBSERVATION_STATE_DIFF_V1",\n        schema_version="1.0.0",parent_hashes=(before,after),source_refs=("fixture://144/143",),created_at=FIXED)\n    return ObservationStateDiff(before,after,tuple(added),tuple(removed),tuple(clusters_a),tuple(clusters_r),tuple(contra_a),tuple(contra_r),l)\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-144",revision=UMD_144_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://144",),created_at=FIXED)\n\nclass TestUMD144(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_144_observation_change_registry())\n    def test_change_types(self):\n        d=diff("a",added=("obs-a",),removed=("obs-b",),clusters_a=("c1",),clusters_r=("c2",),\n               contra_a=(("obs-a","obs-c"),),contra_r=(("obs-b","obs-d"),))\n        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)\n        self.assertEqual(set(c.change_type for c in r.changes),set(CHANGE_TYPES))\n    def test_type_query(self):\n        d=diff("a",added=("obs-a","obs-b"))\n        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)\n        self.assertEqual(r.subjects_for_type("canonical-added"),("obs-a","obs-b"))\n    def test_observation_query(self):\n        d=diff("a",contra_a=(("obs-a","obs-c"),))\n        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)\n        self.assertEqual(len(r.changes_for_observation("obs-a")),1)\n        self.assertEqual(r.changes_for_observation("obs-a"),r.changes_for_observation("obs-c"))\n    def test_unknown(self):\n        r=ObservationChangeRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(r.subjects_for_type("canonical-added"),())\n        self.assertEqual(r.changes_for_observation("missing"),())\n    def test_deterministic(self):\n        a=diff("a",added=("obs-a",))\n        c=diff("c",removed=("obs-b",))\n        x=ObservationChangeRegistryBuilder().build((a,c),lineage_factory=lf)\n        y=ObservationChangeRegistryBuilder().build((c,a),lineage_factory=lf)\n        self.assertEqual(x.registry_hash,y.registry_hash)\n    def test_bad_diff(self):\n        with self.assertRaises(TypeError):\n            ObservationChangeRegistryBuilder().build((object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_144_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-144 CERTIFICATION TEST");print(" OBSERVATION CHANGE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD144))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_144_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation-state changes indexed by deterministic change type")\n    print("[PASS] Canonical observation and contradiction change reverse queries certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-144 CERTIFIED")\n'
UPSTREAM_MODULE='umd_143_observation_state_diff'
UPSTREAM_VERIFIER='verify_umd_143_observation_state_diff'
EXPORTED_NAMES=('UMD_144_REVISION', 'CHANGE_TYPES', 'ObservationChangeRecord', 'ObservationChangeRegistry', 'ObservationChangeRegistryBuilder', 'build_umd_144_certification_manifest', 'verify_umd_144_observation_change_registry')

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
    marker="# UMD-144 exports"
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
            raise RuntimeError("UMD-144 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-144 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-144 INSTALLER")
    print(" OBSERVATION CHANGE REGISTRY")
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
        print("[ROLLBACK] UMD-144 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-144',
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
    print("[DONE] UMD-144 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
