from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_115_OBSERVATION_IMPACT_MAPPING_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_115_observation_impact.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_115_observation_impact.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_109_market_semantic_profile import semantic_key\nfrom .umd_114_dependency_registry import DependencyRegistry, verify_umd_114_dependency_registry\n\nUMD_115_BUILD_ID="UMD-115"\nUMD_115_REVISION="UMD_115_OBSERVATION_IMPACT_MAPPING_V1"\nUMD_115_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nOBSERVATION_FIELDS=("entity","asset","event","metric","geography","time_window","settlement_source","external_state")\n\n@dataclass(frozen=True,slots=True)\nclass ObservationDescriptor:\n    observation_id:str\n    facts:Tuple[Tuple[str,str],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        if not isinstance(self.observation_id,str) or not self.observation_id:\n            raise ValueError("observation_id must be non-empty")\n        normalized=[]\n        for kind,key in self.facts:\n            if kind not in OBSERVATION_FIELDS:\n                raise ValueError("unsupported observation fact kind")\n            normalized.append((kind,semantic_key(key)))\n        normalized=tuple(sorted(set(normalized)))\n        object.__setattr__(self,"facts",normalized)\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_115_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-115")\n\n    @property\n    def observation_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "facts":self.facts,\n            "lineage":self.lineage,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass DirectImpactResult:\n    observation_hash:str\n    market_ids:Tuple[str,...]\n    matched_dependencies:Tuple[Tuple[str,str,Tuple[str,...]],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_ids",tuple(self.market_ids))\n        object.__setattr__(self,"matched_dependencies",tuple(self.matched_dependencies))\n        if tuple(sorted(set(self.market_ids)))!=self.market_ids:\n            raise ValueError("market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_115_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-115")\n        if self.observation_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include observation hash")\n\n    @property\n    def impact_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "market_ids":self.market_ids,\n            "matched_dependencies":self.matched_dependencies,\n            "lineage":self.lineage,\n        })\n\nclass ObservationImpactMapper:\n    __slots__=("registry",)\n\n    def __init__(self,registry:DependencyRegistry):\n        if not isinstance(registry,DependencyRegistry):\n            raise TypeError("registry must be DependencyRegistry")\n        self.registry=registry\n\n    def map(self,observation:ObservationDescriptor,*,lineage:ImmutableLineage)->DirectImpactResult:\n        if not isinstance(observation,ObservationDescriptor):\n            raise TypeError("observation must be ObservationDescriptor")\n        markets=set()\n        matched=[]\n        for kind,key in observation.facts:\n            ids=self.registry.markets_for_dependency(kind,key)\n            if ids:\n                markets.update(ids)\n                matched.append((kind,key,ids))\n        return DirectImpactResult(\n            observation.observation_hash,\n            tuple(sorted(markets)),\n            tuple(sorted(matched)),\n            lineage,\n        )\n\ndef build_umd_115_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_115_BUILD_ID,"revision":UMD_115_REVISION,\n        "schema_version":UMD_115_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-114"),\n        "mode":"deterministic_read_only_observation_impact_mapping",\n        "observation_fields":OBSERVATION_FIELDS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_115_observation_impact_mapping()->bool:\n    if verify_umd_114_dependency_registry() is not True:\n        return False\n    m=build_umd_115_certification_manifest()\n    return m["build_id"]=="UMD-115" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import *\n\nFIXED=datetime(2026,8,9,19,0,tzinfo=timezone.utc)\n\ndef registry():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=("a"*64,),\n        source_refs=("fixture://115/114",),created_at=FIXED\n    )\n    r=object.__new__(DependencyRegistry)\n    object.__setattr__(r,"profiles",())\n    object.__setattr__(r,"constraint_graph_hash","a"*64)\n    object.__setattr__(r,"dependency_index",MappingProxyType({\n        "asset=bitcoin":("umd:market:a","umd:market:b"),\n        "metric=btc-spot-price":("umd:market:a","umd:market:b"),\n        "event=fomc-meeting":("umd:market:c",),\n    }))\n    object.__setattr__(r,"role_index",MappingProxyType({}))\n    object.__setattr__(r,"constraint_index",MappingProxyType({}))\n    object.__setattr__(r,"lineage",l)\n    return r\n\ndef observation():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,\n        schema_version="1.0.0",parent_hashes=(),\n        source_refs=("fixture://115/obs",),created_at=FIXED\n    )\n    return ObservationDescriptor("obs-1",(("metric","BTC Spot Price"),("asset","Bitcoin")),l)\n\ndef impact_lineage(o):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,\n        schema_version="1.0.0",parent_hashes=(o.observation_hash,),\n        source_refs=("fixture://115/map",),created_at=FIXED\n    )\n\nclass TestUMD115(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_115_observation_impact_mapping())\n    def test_direct_mapping(self):\n        o=observation()\n        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))\n        self.assertEqual(r.market_ids,("umd:market:a","umd:market:b"))\n    def test_matched_dependencies(self):\n        o=observation()\n        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))\n        self.assertEqual(len(r.matched_dependencies),2)\n    def test_unknown_observation(self):\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://115/x",),created_at=FIXED)\n        o=ObservationDescriptor("obs-x",(("asset","Ethereum"),),l)\n        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))\n        self.assertEqual(r.market_ids,())\n    def test_normalization(self):\n        o=observation()\n        self.assertIn(("metric","btc-spot-price"),o.facts)\n    def test_deterministic(self):\n        o=observation(); l=impact_lineage(o)\n        a=ObservationImpactMapper(registry()).map(o,lineage=l)\n        b=ObservationImpactMapper(registry()).map(o,lineage=l)\n        self.assertEqual(a.impact_hash,b.impact_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): ObservationImpactMapper(object())\n    def test_lineage_required(self):\n        o=observation()\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://115/bad",),created_at=FIXED)\n        with self.assertRaises(ValueError): ObservationImpactMapper(registry()).map(o,lineage=bad)\n    def test_side_effects(self):\n        m=build_umd_115_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-115 CERTIFICATION TEST");print(" OBSERVATION IMPACT MAPPING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD115))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_115_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation facts map deterministically to directly dependent markets")\n    print("[PASS] UMD-114 dependency registry consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-115 CERTIFIED")\n'
UPSTREAM_MODULE='umd_114_dependency_registry'
UPSTREAM_VERIFIER='verify_umd_114_dependency_registry'
EXPORTED_NAMES=('UMD_115_REVISION', 'OBSERVATION_FIELDS', 'ObservationDescriptor', 'DirectImpactResult', 'ObservationImpactMapper', 'build_umd_115_certification_manifest', 'verify_umd_115_observation_impact_mapping')

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
    marker="# UMD-115 exports"
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
            raise RuntimeError("UMD-115 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-115 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-115 INSTALLER")
    print(" OBSERVATION IMPACT MAPPING")
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
        print("[ROLLBACK] UMD-115 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-115',
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
    print("[DONE] UMD-115 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
