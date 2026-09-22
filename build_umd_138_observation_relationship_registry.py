from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_138_OBSERVATION_RELATIONSHIP_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_138_observation_relationship_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_138_observation_relationship_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_136_observation_equivalence import ObservationEquivalenceGroup\nfrom .umd_137_observation_contradiction import ObservationContradictionSet,verify_umd_137_observation_contradiction_model\n\nUMD_138_BUILD_ID="UMD-138"\nUMD_138_REVISION="UMD_138_OBSERVATION_RELATIONSHIP_REGISTRY_V1"\nUMD_138_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationRelationshipRegistry:\n    equivalence_groups:Tuple[ObservationEquivalenceGroup,...]\n    contradiction_sets:Tuple[ObservationContradictionSet,...]\n    equivalent_index:Mapping[str,Tuple[str,...]]\n    contradiction_index:Mapping[str,Tuple[str,...]]\n    contradiction_type_index:Mapping[str,Tuple[str,...]]\n    canonical_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"equivalence_groups",tuple(self.equivalence_groups))\n        object.__setattr__(self,"contradiction_sets",tuple(self.contradiction_sets))\n        for name in ("equivalent_index","contradiction_index","contradiction_type_index","canonical_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.equivalence_groups!=tuple(sorted(\n            self.equivalence_groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)\n        )):\n            raise ValueError("equivalence groups must be deterministically sorted")\n        if self.contradiction_sets!=tuple(sorted(\n            self.contradiction_sets,key=lambda s:s.contradiction_set_hash\n        )):\n            raise ValueError("contradiction sets must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_138_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-138")\n        required={g.group_hash for g in self.equivalence_groups}|{s.contradiction_set_hash for s in self.contradiction_sets}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every relationship artifact hash")\n\n    def equivalents_of(self,observation_id:str)->Tuple[str,...]:\n        return self.equivalent_index.get(observation_id,())\n\n    def contradictions_of(self,observation_id:str)->Tuple[str,...]:\n        return self.contradiction_index.get(observation_id,())\n\n    def observations_for_contradiction_type(self,kind:str)->Tuple[str,...]:\n        return self.contradiction_type_index.get(kind,())\n\n    def canonical_for(self,observation_id:str)->str|None:\n        values=self.canonical_index.get(observation_id,())\n        return values[0] if values else None\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "equivalence_group_hashes":tuple(g.group_hash for g in self.equivalence_groups),\n            "contradiction_set_hashes":tuple(s.contradiction_set_hash for s in self.contradiction_sets),\n            "equivalent_index":self.equivalent_index,\n            "contradiction_index":self.contradiction_index,\n            "contradiction_type_index":self.contradiction_type_index,\n            "canonical_index":self.canonical_index,\n            "lineage":self.lineage,\n        })\n\nclass ObservationRelationshipRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        equivalence_groups:Iterable[ObservationEquivalenceGroup],\n        contradiction_sets:Iterable[ObservationContradictionSet],\n        *,\n        lineage_factory,\n    )->ObservationRelationshipRegistry:\n        groups=tuple(equivalence_groups)\n        sets=tuple(contradiction_sets)\n\n        if any(not isinstance(g,ObservationEquivalenceGroup) for g in groups):\n            raise TypeError("equivalence_groups must contain ObservationEquivalenceGroup")\n        if any(not isinstance(s,ObservationContradictionSet) for s in sets):\n            raise TypeError("contradiction_sets must contain ObservationContradictionSet")\n\n        groups=tuple(sorted(groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)))\n        sets=tuple(sorted(sets,key=lambda s:s.contradiction_set_hash))\n\n        equivalent={}\n        contradiction={}\n        contradiction_type={}\n        canonical={}\n\n        for group in groups:\n            members=group.member_observation_ids\n            for obs in members:\n                equivalent[obs]=tuple(x for x in members if x!=obs)\n                canonical[obs]=(group.canonical_observation_id,)\n\n        for contradiction_set in sets:\n            for edge in contradiction_set.contradictions:\n                contradiction.setdefault(edge.source_observation_id,[]).append(edge.target_observation_id)\n                contradiction.setdefault(edge.target_observation_id,[]).append(edge.source_observation_id)\n                contradiction_type.setdefault(edge.contradiction_type,[]).extend(\n                    (edge.source_observation_id,edge.target_observation_id)\n                )\n\n        for index in (contradiction,contradiction_type):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        parents=tuple(g.group_hash for g in groups)+tuple(s.contradiction_set_hash for s in sets)\n        lineage=lineage_factory(parents)\n        return ObservationRelationshipRegistry(\n            groups,sets,equivalent,contradiction,contradiction_type,canonical,lineage\n        )\n\ndef build_umd_138_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_138_BUILD_ID,"revision":UMD_138_REVISION,\n        "schema_version":UMD_138_SCHEMA_VERSION,"upstream_builds":("UMD-136","UMD-137"),\n        "mode":"deterministic_read_only_observation_relationship_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_138_observation_relationship_registry()->bool:\n    if verify_umd_137_observation_contradiction_model() is not True:\n        return False\n    m=build_umd_138_certification_manifest()\n    return m["build_id"]=="UMD-138" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup\nfrom qseries_v2.universal_market_discovery.umd_137_observation_contradiction import ObservationContradiction,ObservationContradictionSet\nfrom qseries_v2.universal_market_discovery.umd_138_observation_relationship_registry import *\n\nFIXED=datetime(2026,8,10,3,20,tzinfo=timezone.utc)\n\ndef group(signature,ids,hashes):\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://138/136",),created_at=FIXED\n    )\n    return ObservationEquivalenceGroup(signature,ids[0],ids,hashes,l)\n\ndef artifacts():\n    g1=group("a"*64,("obs-a","obs-b"),("1"*64,"2"*64))\n    g2=group("b"*64,("obs-c",),("3"*64,))\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-137",revision="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1",\n        schema_version="1.0.0",parent_hashes=(g1.group_hash,g2.group_hash),\n        source_refs=("fixture://138/137",),created_at=FIXED\n    )\n    s=ObservationContradictionSet(\n        ("obs-a","obs-b","obs-c"),\n        (\n            ObservationContradiction("obs-a","obs-c","negates","claim:x"),\n            ObservationContradiction("obs-b","obs-c","supersedes","source:update"),\n        ),\n        tuple(sorted((g1.group_hash,g2.group_hash))),\n        l,\n    )\n    return (g1,g2),(s,)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-138",revision=UMD_138_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://138",),created_at=FIXED\n    )\n\nclass TestUMD138(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_138_observation_relationship_registry())\n\n    def test_equivalence_query(self):\n        gs,ss=artifacts()\n        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)\n        self.assertEqual(r.equivalents_of("obs-a"),("obs-b",))\n        self.assertEqual(r.canonical_for("obs-b"),"obs-a")\n\n    def test_contradiction_query(self):\n        gs,ss=artifacts()\n        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)\n        self.assertEqual(r.contradictions_of("obs-c"),("obs-a","obs-b"))\n\n    def test_contradiction_type_query(self):\n        gs,ss=artifacts()\n        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)\n        self.assertEqual(r.observations_for_contradiction_type("negates"),("obs-a","obs-c"))\n\n    def test_unknown(self):\n        gs,ss=artifacts()\n        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)\n        self.assertEqual(r.equivalents_of("missing"),())\n        self.assertIsNone(r.canonical_for("missing"))\n\n    def test_deterministic(self):\n        gs,ss=artifacts()\n        a=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)\n        b=ObservationRelationshipRegistryBuilder().build(tuple(reversed(gs)),tuple(reversed(ss)),lineage_factory=lf)\n        self.assertEqual(a.registry_hash,b.registry_hash)\n\n    def test_empty(self):\n        r=ObservationRelationshipRegistryBuilder().build((),(),lineage_factory=lf)\n        self.assertEqual(r.equivalence_groups,())\n        self.assertEqual(r.contradiction_sets,())\n\n    def test_bad_group(self):\n        _,ss=artifacts()\n        with self.assertRaises(TypeError):\n            ObservationRelationshipRegistryBuilder().build((object(),),ss,lineage_factory=lf)\n\n    def test_side_effects(self):\n        m=build_umd_138_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-138 CERTIFICATION TEST");print(" OBSERVATION RELATIONSHIP REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD138))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_138_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation equivalence and contradiction registry queries certified")\n    print("[PASS] Canonical observation resolution and contradiction-type queries certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-138 CERTIFIED")\n'
UPSTREAM_MODULE='umd_137_observation_contradiction'
UPSTREAM_VERIFIER='verify_umd_137_observation_contradiction_model'
EXPORTED_NAMES=('UMD_138_REVISION', 'ObservationRelationshipRegistry', 'ObservationRelationshipRegistryBuilder', 'build_umd_138_certification_manifest', 'verify_umd_138_observation_relationship_registry')

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
    marker="# UMD-138 exports"
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
            raise RuntimeError("UMD-138 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-138 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-138 INSTALLER")
    print(" OBSERVATION RELATIONSHIP REGISTRY")
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
        print("[ROLLBACK] UMD-138 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-138',
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
    print("[DONE] UMD-138 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
