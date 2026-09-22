from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_136_observation_equivalence.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_136_observation_equivalence.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_135_observation_routing_registry import ObservationRoutingRecord,verify_umd_135_observation_routing_registry\n\nUMD_136_BUILD_ID="UMD-136"\nUMD_136_REVISION="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1"\nUMD_136_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef observation_signature(record:ObservationRoutingRecord)->str:\n    if not isinstance(record,ObservationRoutingRecord):\n        raise TypeError("record must be ObservationRoutingRecord")\n    return deterministic_sha256({\n        "domain":record.domain,\n        "market_ids":record.market_ids,\n        "family_keys":record.family_keys,\n        "venue_keys":record.venue_keys,\n        "unresolved_entities":record.unresolved_entities,\n    })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationEquivalenceGroup:\n    signature_hash:str\n    canonical_observation_id:str\n    member_observation_ids:Tuple[str,...]\n    member_record_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))\n        object.__setattr__(self,"member_record_hashes",tuple(self.member_record_hashes))\n        if self.member_observation_ids!=tuple(sorted(set(self.member_observation_ids))):\n            raise ValueError("member observation ids must be unique and sorted")\n        if not self.member_observation_ids:\n            raise ValueError("equivalence group requires at least one member")\n        if self.canonical_observation_id!=self.member_observation_ids[0]:\n            raise ValueError("canonical observation id must be lexicographically first member")\n        if len(self.member_observation_ids)!=len(self.member_record_hashes):\n            raise ValueError("member ids and record hashes length mismatch")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_136_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-136")\n        if not set(self.member_record_hashes).issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every member record hash")\n\n    @property\n    def equivalent(self)->bool:\n        return len(self.member_observation_ids)>1\n\n    @property\n    def group_hash(self)->str:\n        return deterministic_sha256({\n            "signature_hash":self.signature_hash,\n            "canonical_observation_id":self.canonical_observation_id,\n            "member_observation_ids":self.member_observation_ids,\n            "member_record_hashes":self.member_record_hashes,\n            "lineage":self.lineage,\n        })\n\nclass ObservationEquivalenceResolver:\n    __slots__=()\n\n    def resolve(self,records:Iterable[ObservationRoutingRecord],*,lineage_factory)->Tuple[ObservationEquivalenceGroup,...]:\n        values=tuple(records)\n        if any(not isinstance(r,ObservationRoutingRecord) for r in values):\n            raise TypeError("records must contain ObservationRoutingRecord")\n        if len({r.observation_id for r in values})!=len(values):\n            raise ValueError("observation ids must be unique before equivalence resolution")\n\n        buckets={}\n        for record in values:\n            buckets.setdefault(observation_signature(record),[]).append(record)\n\n        groups=[]\n        for signature,members in sorted(buckets.items()):\n            members=tuple(sorted(members,key=lambda r:r.observation_id))\n            hashes=tuple(r.record_hash for r in members)\n            lineage=lineage_factory(hashes)\n            groups.append(ObservationEquivalenceGroup(\n                signature,\n                members[0].observation_id,\n                tuple(r.observation_id for r in members),\n                hashes,\n                lineage,\n            ))\n        return tuple(sorted(groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)))\n\ndef build_umd_136_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_136_BUILD_ID,"revision":UMD_136_REVISION,\n        "schema_version":UMD_136_SCHEMA_VERSION,"upstream_builds":("UMD-135",),\n        "mode":"deterministic_read_only_observation_equivalence_resolution",\n        "equivalence_semantics":"exact_structural_signature_only_no_fuzzy_reasoning",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_136_observation_equivalence_resolution()->bool:\n    if verify_umd_135_observation_routing_registry() is not True:\n        return False\n    m=build_umd_136_certification_manifest()\n    return m["build_id"]=="UMD-136" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import ObservationRoutingRecord\nfrom qseries_v2.universal_market_discovery.umd_136_observation_equivalence import *\n\nFIXED=datetime(2026,8,10,3,0,tzinfo=timezone.utc)\n\ndef record(obs,market_ids=("m1",),venue_keys=("kalshi",),domain="economics"):\n    return ObservationRoutingRecord(\n        obs,domain,\n        "a"*64,"b"*64,"c"*64,"d"*64,"timeline-1",\n        tuple(market_ids),\n        ("macro=cpi",),\n        tuple(venue_keys),\n        (),\n    )\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-136",revision=UMD_136_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://136",),created_at=FIXED\n    )\n\nclass TestUMD136(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_136_observation_equivalence_resolution())\n\n    def test_equivalent_group(self):\n        a=record("obs-a"); b=record("obs-b")\n        groups=ObservationEquivalenceResolver().resolve((b,a),lineage_factory=lf)\n        self.assertEqual(len(groups),1)\n        self.assertEqual(groups[0].canonical_observation_id,"obs-a")\n        self.assertEqual(groups[0].member_observation_ids,("obs-a","obs-b"))\n        self.assertTrue(groups[0].equivalent)\n\n    def test_distinct_structure_separate(self):\n        a=record("obs-a")\n        b=record("obs-b",market_ids=("m2",))\n        groups=ObservationEquivalenceResolver().resolve((a,b),lineage_factory=lf)\n        self.assertEqual(len(groups),2)\n\n    def test_signature_ignores_observation_id(self):\n        self.assertEqual(observation_signature(record("obs-a")),observation_signature(record("obs-b")))\n\n    def test_deterministic(self):\n        a=record("obs-a"); b=record("obs-b")\n        x=ObservationEquivalenceResolver().resolve((a,b),lineage_factory=lf)\n        y=ObservationEquivalenceResolver().resolve((b,a),lineage_factory=lf)\n        self.assertEqual(tuple(g.group_hash for g in x),tuple(g.group_hash for g in y))\n\n    def test_duplicate_observation_id_rejected(self):\n        with self.assertRaises(ValueError):\n            ObservationEquivalenceResolver().resolve((record("obs-a"),record("obs-a")),lineage_factory=lf)\n\n    def test_bad_record(self):\n        with self.assertRaises(TypeError):\n            ObservationEquivalenceResolver().resolve((object(),),lineage_factory=lf)\n\n    def test_side_effects(self):\n        m=build_umd_136_certification_manifest()\n        self.assertEqual(m["equivalence_semantics"],"exact_structural_signature_only_no_fuzzy_reasoning")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-136 CERTIFICATION TEST");print(" OBSERVATION EQUIVALENCE RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD136))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_136_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Exact structural observation equivalence grouping certified")\n    print("[PASS] No fuzzy similarity, prediction, or semantic guessing introduced")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-136 CERTIFIED")\n'
UPSTREAM_MODULE='umd_135_observation_routing_registry'
UPSTREAM_VERIFIER='verify_umd_135_observation_routing_registry'
EXPORTED_NAMES=('UMD_136_REVISION', 'observation_signature', 'ObservationEquivalenceGroup', 'ObservationEquivalenceResolver', 'build_umd_136_certification_manifest', 'verify_umd_136_observation_equivalence_resolution')

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
    marker="# UMD-136 exports"
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
            raise RuntimeError("UMD-136 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-136 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-136 INSTALLER")
    print(" OBSERVATION EQUIVALENCE RESOLUTION")
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
        print("[ROLLBACK] UMD-136 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-136',
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
    print("[DONE] UMD-136 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
