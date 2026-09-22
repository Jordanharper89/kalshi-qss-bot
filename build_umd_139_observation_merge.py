from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_139_OBSERVATION_MERGE_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_139_observation_merge.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_139_observation_merge.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_136_observation_equivalence import ObservationEquivalenceGroup\nfrom .umd_138_observation_relationship_registry import ObservationRelationshipRegistry,verify_umd_138_observation_relationship_registry\n\nUMD_139_BUILD_ID="UMD-139"\nUMD_139_REVISION="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1"\nUMD_139_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ObservationMerge:\n    canonical_observation_id:str\n    member_observation_ids:Tuple[str,...]\n    equivalent_member_ids:Tuple[str,...]\n    contradiction_peer_ids:Tuple[str,...]\n    source_group_hash:str\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))\n        object.__setattr__(self,"equivalent_member_ids",tuple(self.equivalent_member_ids))\n        object.__setattr__(self,"contradiction_peer_ids",tuple(self.contradiction_peer_ids))\n        for name in ("member_observation_ids","equivalent_member_ids","contradiction_peer_ids"):\n            value=getattr(self,name)\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n        if not self.member_observation_ids:\n            raise ValueError("merge requires at least one observation")\n        if self.canonical_observation_id!=self.member_observation_ids[0]:\n            raise ValueError("canonical observation must be first sorted member")\n        if set(self.equivalent_member_ids)!=(set(self.member_observation_ids)-{self.canonical_observation_id}):\n            raise ValueError("equivalent_member_ids must be all non-canonical members")\n        if set(self.contradiction_peer_ids)&set(self.member_observation_ids):\n            raise ValueError("contradiction peers cannot be members of same merge")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_139_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-139")\n        if self.source_group_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include source equivalence group hash")\n\n    @property\n    def merge_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_observation_id":self.canonical_observation_id,\n            "member_observation_ids":self.member_observation_ids,\n            "equivalent_member_ids":self.equivalent_member_ids,\n            "contradiction_peer_ids":self.contradiction_peer_ids,\n            "source_group_hash":self.source_group_hash,\n            "lineage":self.lineage,\n        })\n\nclass ObservationMergeResolver:\n    __slots__=("relationships",)\n\n    def __init__(self,relationships:ObservationRelationshipRegistry):\n        if not isinstance(relationships,ObservationRelationshipRegistry):\n            raise TypeError("relationships must be ObservationRelationshipRegistry")\n        self.relationships=relationships\n\n    def resolve(\n        self,\n        groups:Iterable[ObservationEquivalenceGroup],\n        *,\n        lineage_factory,\n    )->Tuple[ObservationMerge,...]:\n        values=tuple(groups)\n        if any(not isinstance(g,ObservationEquivalenceGroup) for g in values):\n            raise TypeError("groups must contain ObservationEquivalenceGroup")\n\n        merges=[]\n        for group in sorted(values,key=lambda g:(g.signature_hash,g.canonical_observation_id)):\n            peers=set()\n            for member in group.member_observation_ids:\n                peers.update(self.relationships.contradictions_of(member))\n            peers.difference_update(group.member_observation_ids)\n\n            lineage=lineage_factory((group.group_hash,))\n            merges.append(ObservationMerge(\n                group.canonical_observation_id,\n                group.member_observation_ids,\n                tuple(x for x in group.member_observation_ids if x!=group.canonical_observation_id),\n                tuple(sorted(peers)),\n                group.group_hash,\n                lineage,\n            ))\n        return tuple(sorted(merges,key=lambda m:(m.canonical_observation_id,m.merge_hash)))\n\ndef build_umd_139_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_139_BUILD_ID,"revision":UMD_139_REVISION,\n        "schema_version":UMD_139_SCHEMA_VERSION,"upstream_builds":("UMD-136","UMD-138"),\n        "mode":"deterministic_read_only_observation_merge_resolution",\n        "merge_semantics":"equivalence_collapse_with_contradiction_preservation",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_139_observation_merge_resolution()->bool:\n    if verify_umd_138_observation_relationship_registry() is not True:\n        return False\n    m=build_umd_139_certification_manifest()\n    return m["build_id"]=="UMD-139" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup\nfrom qseries_v2.universal_market_discovery.umd_137_observation_contradiction import ObservationContradiction,ObservationContradictionSet\nfrom qseries_v2.universal_market_discovery.umd_138_observation_relationship_registry import ObservationRelationshipRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_139_observation_merge import *\n\nFIXED=datetime(2026,8,10,4,0,tzinfo=timezone.utc)\n\ndef group(sig,ids,hashes):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://139/136",),created_at=FIXED)\n    return ObservationEquivalenceGroup(sig,ids[0],ids,hashes,l)\n\ndef artifacts():\n    g1=group("a"*64,("obs-a","obs-b"),("1"*64,"2"*64))\n    g2=group("b"*64,("obs-c",),("3"*64,))\n    l137=ImmutableLineage(subsystem_id="UMD",build_id="UMD-137",revision="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(g1.group_hash,g2.group_hash),source_refs=("fixture://139/137",),created_at=FIXED)\n    s=ObservationContradictionSet(\n        ("obs-a","obs-b","obs-c"),\n        (ObservationContradiction("obs-a","obs-c","negates","claim:x"),),\n        tuple(sorted((g1.group_hash,g2.group_hash))),l137\n    )\n    def lf138(parents):\n        return ImmutableLineage(subsystem_id="UMD",build_id="UMD-138",revision="UMD_138_OBSERVATION_RELATIONSHIP_REGISTRY_V1",\n            schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://139/138",),created_at=FIXED)\n    rel=ObservationRelationshipRegistryBuilder().build((g1,g2),(s,),lineage_factory=lf138)\n    return (g1,g2),rel\n\ndef lf139(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision=UMD_139_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://139",),created_at=FIXED)\n\nclass TestUMD139(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_139_observation_merge_resolution())\n    def test_equivalence_collapsed(self):\n        gs,rel=artifacts()\n        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)\n        m=next(x for x in merges if x.canonical_observation_id=="obs-a")\n        self.assertEqual(m.member_observation_ids,("obs-a","obs-b"))\n        self.assertEqual(m.equivalent_member_ids,("obs-b",))\n    def test_contradiction_preserved(self):\n        gs,rel=artifacts()\n        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)\n        m=next(x for x in merges if x.canonical_observation_id=="obs-a")\n        self.assertEqual(m.contradiction_peer_ids,("obs-c",))\n    def test_singleton_merge(self):\n        gs,rel=artifacts()\n        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)\n        m=next(x for x in merges if x.canonical_observation_id=="obs-c")\n        self.assertEqual(m.member_observation_ids,("obs-c",))\n        self.assertEqual(m.equivalent_member_ids,())\n    def test_deterministic(self):\n        gs,rel=artifacts()\n        a=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)\n        b=ObservationMergeResolver(rel).resolve(tuple(reversed(gs)),lineage_factory=lf139)\n        self.assertEqual(tuple(x.merge_hash for x in a),tuple(x.merge_hash for x in b))\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): ObservationMergeResolver(object())\n    def test_bad_group(self):\n        _,rel=artifacts()\n        with self.assertRaises(TypeError): ObservationMergeResolver(rel).resolve((object(),),lineage_factory=lf139)\n    def test_side_effects(self):\n        m=build_umd_139_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-139 CERTIFICATION TEST");print(" OBSERVATION MERGE RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD139))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_139_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Equivalent observations collapsed to canonical merges")\n    print("[PASS] Contradiction peers preserved outside merge membership")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-139 CERTIFIED")\n'
UPSTREAM_MODULE='umd_138_observation_relationship_registry'
UPSTREAM_VERIFIER='verify_umd_138_observation_relationship_registry'
EXPORTED_NAMES=('UMD_139_REVISION', 'ObservationMerge', 'ObservationMergeResolver', 'build_umd_139_certification_manifest', 'verify_umd_139_observation_merge_resolution')

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
    marker="# UMD-139 exports"
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
            raise RuntimeError("UMD-139 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-139 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-139 INSTALLER")
    print(" OBSERVATION MERGE RESOLUTION")
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
        print("[ROLLBACK] UMD-139 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-139',
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
    print("[DONE] UMD-139 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
