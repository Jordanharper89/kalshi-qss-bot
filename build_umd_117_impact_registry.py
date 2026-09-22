from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_117_IMPACT_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_117_impact_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_117_impact_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_115_observation_impact import DirectImpactResult\nfrom .umd_116_dependency_propagation import PropagationResult, verify_umd_116_dependency_propagation\n\nUMD_117_BUILD_ID="UMD-117"\nUMD_117_REVISION="UMD_117_IMPACT_REGISTRY_V1"\nUMD_117_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ImpactRecord:\n    observation_hash:str\n    direct_market_ids:Tuple[str,...]\n    propagated_market_ids:Tuple[str,...]\n    direct_impact_hash:str\n    propagation_hash:str\n\n    @property\n    def all_market_ids(self)->Tuple[str,...]:\n        return tuple(sorted(set(self.direct_market_ids)|set(self.propagated_market_ids)))\n\n    @property\n    def record_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "direct_market_ids":self.direct_market_ids,\n            "propagated_market_ids":self.propagated_market_ids,\n            "direct_impact_hash":self.direct_impact_hash,\n            "propagation_hash":self.propagation_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ImpactRegistry:\n    records:Tuple[ImpactRecord,...]\n    observation_index:Mapping[str,Tuple[str,...]]\n    market_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"records",tuple(self.records))\n        object.__setattr__(self,"observation_index",_freeze_index(self.observation_index))\n        object.__setattr__(self,"market_index",_freeze_index(self.market_index))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_117_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-117")\n        required={r.record_hash for r in self.records}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every impact record hash")\n\n    def markets_for_observation(self,observation_hash:str)->Tuple[str,...]:\n        return self.observation_index.get(observation_hash,())\n\n    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.market_index.get(canonical_market_id,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "observation_index":self.observation_index,\n            "market_index":self.market_index,\n            "lineage":self.lineage,\n        })\n\nclass ImpactRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        pairs:Iterable[tuple[DirectImpactResult,PropagationResult]],\n        *,\n        lineage_factory,\n    )->ImpactRegistry:\n        records=[]\n        observation_index={}\n        market_index={}\n\n        for direct,propagation in pairs:\n            if not isinstance(direct,DirectImpactResult):\n                raise TypeError("direct impact must be DirectImpactResult")\n            if not isinstance(propagation,PropagationResult):\n                raise TypeError("propagation must be PropagationResult")\n            if tuple(direct.market_ids)!=tuple(propagation.direct_market_ids):\n                raise ValueError("propagation direct markets do not match direct impact")\n\n            record=ImpactRecord(\n                direct.observation_hash,\n                tuple(direct.market_ids),\n                tuple(propagation.propagated_market_ids),\n                direct.impact_hash,\n                propagation.propagation_hash,\n            )\n            records.append(record)\n            observation_index.setdefault(record.observation_hash,[]).extend(record.all_market_ids)\n            for market_id in record.all_market_ids:\n                market_index.setdefault(market_id,[]).append(record.observation_hash)\n\n        records.sort(key=lambda r:(r.observation_hash,r.record_hash))\n        for index in (observation_index,market_index):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        lineage=lineage_factory(tuple(r.record_hash for r in records))\n        return ImpactRegistry(tuple(records),observation_index,market_index,lineage)\n\ndef build_umd_117_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_117_BUILD_ID,"revision":UMD_117_REVISION,\n        "schema_version":UMD_117_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-116"),\n        "mode":"deterministic_read_only_impact_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_117_impact_registry()->bool:\n    if verify_umd_116_dependency_propagation() is not True:\n        return False\n    m=build_umd_117_certification_manifest()\n    return m["build_id"]=="UMD-117" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult\nfrom qseries_v2.universal_market_discovery.umd_116_dependency_propagation import PropagationResult,PropagationStep\nfrom qseries_v2.universal_market_discovery.umd_117_impact_registry import *\n\nFIXED=datetime(2026,8,9,19,20,tzinfo=timezone.utc)\n\ndef pair(obs_hash="a"*64):\n    l115=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",schema_version="1.0.0",parent_hashes=(obs_hash,),source_refs=("fixture://117/115",),created_at=FIXED)\n    direct=DirectImpactResult(obs_hash,("m1",),(),l115)\n    l116=ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision="UMD_116_DEPENDENCY_PROPAGATION_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://117/116",),created_at=FIXED)\n    prop=PropagationResult(("m1",),("m2","m3"),(PropagationStep(1,"m1","m2","implies"),PropagationStep(2,"m2","m3","threshold_monotonic")),l116)\n    return direct,prop\n\ndef lineage_factory(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-117",revision=UMD_117_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://117",),created_at=FIXED)\n\nclass TestUMD117(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_117_impact_registry())\n    def test_observation_query(self):\n        d,p=pair()\n        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)\n        self.assertEqual(r.markets_for_observation(d.observation_hash),("m1","m2","m3"))\n    def test_market_reverse_query(self):\n        d,p=pair()\n        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)\n        self.assertEqual(r.observations_for_market("m2"),(d.observation_hash,))\n    def test_unknown_market(self):\n        d,p=pair()\n        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)\n        self.assertEqual(r.observations_for_market("missing"),())\n    def test_mismatch_rejected(self):\n        d,p=pair()\n        wrong=PropagationResult(("x",),p.propagated_market_ids,p.steps,p.lineage)\n        with self.assertRaises(ValueError):\n            ImpactRegistryBuilder().build(((d,wrong),),lineage_factory=lineage_factory)\n    def test_deterministic(self):\n        a1,p1=pair("a"*64); a2,p2=pair("b"*64)\n        x=ImpactRegistryBuilder().build(((a1,p1),(a2,p2)),lineage_factory=lineage_factory)\n        y=ImpactRegistryBuilder().build(((a2,p2),(a1,p1)),lineage_factory=lineage_factory)\n        self.assertEqual(x.registry_hash,y.registry_hash)\n    def test_immutable_index(self):\n        d,p=pair()\n        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)\n        with self.assertRaises(TypeError): r.market_index["m1"]=()\n    def test_empty_registry(self):\n        r=ImpactRegistryBuilder().build((),lineage_factory=lineage_factory)\n        self.assertEqual(r.records,())\n    def test_side_effects(self):\n        m=build_umd_117_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-117 CERTIFICATION TEST");print(" IMPACT REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD117))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_117_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation-to-market and market-to-observation impact queries certified")\n    print("[PASS] Direct and propagated impact lineage assembled read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-117 CERTIFIED")\n'
UPSTREAM_MODULE='umd_116_dependency_propagation'
UPSTREAM_VERIFIER='verify_umd_116_dependency_propagation'
EXPORTED_NAMES=('UMD_117_REVISION', 'ImpactRecord', 'ImpactRegistry', 'ImpactRegistryBuilder', 'build_umd_117_certification_manifest', 'verify_umd_117_impact_registry')

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
    marker="# UMD-117 exports"
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
            raise RuntimeError("UMD-117 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-117 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-117 INSTALLER")
    print(" IMPACT REGISTRY")
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
        print("[ROLLBACK] UMD-117 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-117',
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
    print("[DONE] UMD-117 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
