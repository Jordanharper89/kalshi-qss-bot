from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_137_OBSERVATION_CONTRADICTION_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_137_observation_contradiction.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_137_observation_contradiction.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_136_observation_equivalence import ObservationEquivalenceGroup,verify_umd_136_observation_equivalence_resolution\n\nUMD_137_BUILD_ID="UMD-137"\nUMD_137_REVISION="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1"\nUMD_137_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nCONTRADICTION_TYPES=("negates","supersedes","mutually-exclusive","temporal-conflict")\nSYMMETRIC_CONTRADICTIONS=("mutually-exclusive",)\n\n@dataclass(frozen=True,slots=True)\nclass ObservationContradiction:\n    source_observation_id:str\n    target_observation_id:str\n    contradiction_type:str\n    basis_key:str\n\n    def __post_init__(self):\n        if not self.source_observation_id or not self.target_observation_id:\n            raise ValueError("contradiction endpoints must be non-empty")\n        if self.source_observation_id==self.target_observation_id:\n            raise ValueError("contradiction endpoints must differ")\n        if self.contradiction_type not in CONTRADICTION_TYPES:\n            raise ValueError("unsupported contradiction type")\n        if not isinstance(self.basis_key,str) or not self.basis_key.strip():\n            raise ValueError("basis_key must be non-empty")\n\n    @property\n    def contradiction_hash(self)->str:\n        return deterministic_sha256({\n            "source_observation_id":self.source_observation_id,\n            "target_observation_id":self.target_observation_id,\n            "contradiction_type":self.contradiction_type,\n            "basis_key":self.basis_key,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationContradictionSet:\n    observation_ids:Tuple[str,...]\n    contradictions:Tuple[ObservationContradiction,...]\n    equivalence_group_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"observation_ids",tuple(self.observation_ids))\n        object.__setattr__(self,"contradictions",tuple(self.contradictions))\n        object.__setattr__(self,"equivalence_group_hashes",tuple(self.equivalence_group_hashes))\n        if self.observation_ids!=tuple(sorted(set(self.observation_ids))):\n            raise ValueError("observation_ids must be unique and sorted")\n        expected=tuple(sorted(\n            self.contradictions,\n            key=lambda c:(c.source_observation_id,c.target_observation_id,c.contradiction_type,c.basis_key)\n        ))\n        if self.contradictions!=expected:\n            raise ValueError("contradictions must be deterministically sorted")\n        known=set(self.observation_ids)\n        for c in self.contradictions:\n            if c.source_observation_id not in known or c.target_observation_id not in known:\n                raise ValueError("contradiction references unknown observation")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_137_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-137")\n        if not set(self.equivalence_group_hashes).issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include equivalence group hashes")\n\n    def contradictions_for(self,observation_id:str)->Tuple[ObservationContradiction,...]:\n        return tuple(c for c in self.contradictions if observation_id in (c.source_observation_id,c.target_observation_id))\n\n    @property\n    def contradiction_set_hash(self)->str:\n        return deterministic_sha256({\n            "observation_ids":self.observation_ids,\n            "contradiction_hashes":tuple(c.contradiction_hash for c in self.contradictions),\n            "equivalence_group_hashes":self.equivalence_group_hashes,\n            "lineage":self.lineage,\n        })\n\nclass ObservationContradictionBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        equivalence_groups:Iterable[ObservationEquivalenceGroup],\n        specs:Iterable[tuple[str,str,str,str]],\n        *,\n        lineage:ImmutableLineage,\n    )->ObservationContradictionSet:\n        groups=tuple(equivalence_groups)\n        if any(not isinstance(g,ObservationEquivalenceGroup) for g in groups):\n            raise TypeError("equivalence_groups must contain ObservationEquivalenceGroup")\n\n        observation_ids=tuple(sorted({\n            obs for group in groups for obs in group.member_observation_ids\n        }))\n        known=set(observation_ids)\n        contradictions=[]\n        seen=set()\n\n        for source,target,kind,basis in specs:\n            if source not in known or target not in known:\n                raise ValueError("contradiction references unknown observation")\n            if kind in SYMMETRIC_CONTRADICTIONS and target<source:\n                source,target=target,source\n            key=(source,target,kind,basis)\n            if key in seen:\n                continue\n            seen.add(key)\n            contradictions.append(ObservationContradiction(source,target,kind,basis))\n\n        contradictions.sort(key=lambda c:(c.source_observation_id,c.target_observation_id,c.contradiction_type,c.basis_key))\n        return ObservationContradictionSet(\n            observation_ids,\n            tuple(contradictions),\n            tuple(sorted(g.group_hash for g in groups)),\n            lineage,\n        )\n\ndef build_umd_137_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_137_BUILD_ID,"revision":UMD_137_REVISION,\n        "schema_version":UMD_137_SCHEMA_VERSION,"upstream_builds":("UMD-136",),\n        "mode":"deterministic_read_only_explicit_observation_contradiction_model",\n        "contradiction_types":CONTRADICTION_TYPES,\n        "contradiction_semantics":"explicit_structural_relationships_only_no_inference",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_137_observation_contradiction_model()->bool:\n    if verify_umd_136_observation_equivalence_resolution() is not True:\n        return False\n    m=build_umd_137_certification_manifest()\n    return m["build_id"]=="UMD-137" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup\nfrom qseries_v2.universal_market_discovery.umd_137_observation_contradiction import *\n\nFIXED=datetime(2026,8,10,3,10,tzinfo=timezone.utc)\n\ndef group(signature,ids,hashes):\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=hashes,\n        source_refs=("fixture://137/136",),created_at=FIXED\n    )\n    return ObservationEquivalenceGroup(signature,tuple(ids)[0],tuple(ids),tuple(hashes),l)\n\ndef groups():\n    return (\n        group("a"*64,("obs-a",),("1"*64,)),\n        group("b"*64,("obs-b",),("2"*64,)),\n        group("c"*64,("obs-c",),("3"*64,)),\n    )\n\ndef lineage(gs):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-137",revision=UMD_137_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(g.group_hash for g in gs),\n        source_refs=("fixture://137",),created_at=FIXED\n    )\n\nclass TestUMD137(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_137_observation_contradiction_model())\n\n    def test_negation(self):\n        gs=groups()\n        s=ObservationContradictionBuilder().build(\n            gs,(("obs-a","obs-b","negates","claim:inflation-direction"),),\n            lineage=lineage(gs)\n        )\n        self.assertEqual(len(s.contradictions),1)\n        self.assertEqual(s.contradictions[0].contradiction_type,"negates")\n\n    def test_symmetric_canonicalization(self):\n        gs=groups(); l=lineage(gs)\n        a=ObservationContradictionBuilder().build(\n            gs,(("obs-b","obs-a","mutually-exclusive","event:result"),),lineage=l\n        )\n        b=ObservationContradictionBuilder().build(\n            gs,(("obs-a","obs-b","mutually-exclusive","event:result"),),lineage=l\n        )\n        self.assertEqual(a.contradiction_set_hash,b.contradiction_set_hash)\n\n    def test_duplicate_collapsed(self):\n        gs=groups()\n        spec=("obs-a","obs-b","supersedes","source:update")\n        s=ObservationContradictionBuilder().build(gs,(spec,spec),lineage=lineage(gs))\n        self.assertEqual(len(s.contradictions),1)\n\n    def test_query(self):\n        gs=groups()\n        s=ObservationContradictionBuilder().build(\n            gs,(("obs-a","obs-c","temporal-conflict","time:event"),),lineage=lineage(gs)\n        )\n        self.assertEqual(len(s.contradictions_for("obs-c")),1)\n\n    def test_unknown_observation_rejected(self):\n        gs=groups()\n        with self.assertRaises(ValueError):\n            ObservationContradictionBuilder().build(\n                gs,(("obs-a","missing","negates","claim:x"),),lineage=lineage(gs)\n            )\n\n    def test_self_contradiction_rejected(self):\n        gs=groups()\n        with self.assertRaises(ValueError):\n            ObservationContradictionBuilder().build(\n                gs,(("obs-a","obs-a","negates","claim:x"),),lineage=lineage(gs)\n            )\n\n    def test_side_effects(self):\n        m=build_umd_137_certification_manifest()\n        self.assertEqual(m["contradiction_semantics"],"explicit_structural_relationships_only_no_inference")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-137 CERTIFICATION TEST");print(" OBSERVATION CONTRADICTION MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD137))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_137_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Explicit negation, supersession, exclusivity, and temporal-conflict relationships certified")\n    print("[PASS] No contradiction inference or probabilistic reasoning introduced")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-137 CERTIFIED")\n'
UPSTREAM_MODULE='umd_136_observation_equivalence'
UPSTREAM_VERIFIER='verify_umd_136_observation_equivalence_resolution'
EXPORTED_NAMES=('UMD_137_REVISION', 'CONTRADICTION_TYPES', 'ObservationContradiction', 'ObservationContradictionSet', 'ObservationContradictionBuilder', 'build_umd_137_certification_manifest', 'verify_umd_137_observation_contradiction_model')

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
    marker="# UMD-137 exports"
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
            raise RuntimeError("UMD-137 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-137 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-137 INSTALLER")
    print(" OBSERVATION CONTRADICTION MODEL")
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
        print("[ROLLBACK] UMD-137 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-137',
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
    print("[DONE] UMD-137 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
