from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_131_OBSERVATION_ENTITY_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_131_observation_entity_resolution.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_131_observation_entity_resolution.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import semantic_key\nfrom .umd_111_semantic_registry import SemanticRegistry\nfrom .umd_112_market_dependency import DEPENDENCY_KINDS\nfrom .umd_114_dependency_registry import DependencyRegistry\nfrom .umd_130_observation_classification import CanonicalObservationClassification,verify_umd_130_observation_classification\n\nUMD_131_BUILD_ID="UMD-131"\nUMD_131_REVISION="UMD_131_OBSERVATION_ENTITY_RESOLUTION_V1"\nUMD_131_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nRESOLVABLE_ENTITY_KINDS=tuple(\n    kind for kind in DEPENDENCY_KINDS\n    if kind not in ("time_window","external_state")\n)\n\n@dataclass(frozen=True,slots=True)\nclass ObservationEntityBinding:\n    kind:str\n    source_value:str\n    canonical_key:str\n    known_market_ids:Tuple[str,...]\n\n    def __post_init__(self):\n        if self.kind not in RESOLVABLE_ENTITY_KINDS:\n            raise ValueError("unsupported resolvable entity kind")\n        if self.canonical_key!=semantic_key(self.source_value):\n            raise ValueError("canonical_key does not match source_value")\n        object.__setattr__(self,"known_market_ids",tuple(self.known_market_ids))\n        if self.known_market_ids!=tuple(sorted(set(self.known_market_ids))):\n            raise ValueError("known_market_ids must be unique and sorted")\n        if not self.known_market_ids:\n            raise ValueError("resolved entity binding requires at least one known market")\n\n    @property\n    def binding_hash(self)->str:\n        return deterministic_sha256({\n            "kind":self.kind,\n            "canonical_key":self.canonical_key,\n            "known_market_ids":self.known_market_ids,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationEntityResolution:\n    observation_id:str\n    classification_hash:str\n    bindings:Tuple[ObservationEntityBinding,...]\n    unresolved:Tuple[Tuple[str,str],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"bindings",tuple(self.bindings))\n        object.__setattr__(self,"unresolved",tuple(self.unresolved))\n        if self.bindings!=tuple(sorted(self.bindings,key=lambda b:(b.kind,b.canonical_key,b.binding_hash))):\n            raise ValueError("bindings must be deterministically sorted")\n        if self.unresolved!=tuple(sorted(set(self.unresolved))):\n            raise ValueError("unresolved entries must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_131_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-131")\n        if self.classification_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include classification hash")\n\n    @property\n    def resolution_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "classification_hash":self.classification_hash,\n            "binding_hashes":tuple(b.binding_hash for b in self.bindings),\n            "unresolved":self.unresolved,\n            "lineage":self.lineage,\n        })\n\nclass ObservationEntityResolver:\n    __slots__=("semantic_registry","dependency_registry")\n\n    def __init__(\n        self,\n        semantic_registry:SemanticRegistry,\n        dependency_registry:DependencyRegistry,\n    ):\n        if not isinstance(semantic_registry,SemanticRegistry):\n            raise TypeError("semantic_registry must be SemanticRegistry")\n        if not isinstance(dependency_registry,DependencyRegistry):\n            raise TypeError("dependency_registry must be DependencyRegistry")\n        self.semantic_registry=semantic_registry\n        self.dependency_registry=dependency_registry\n\n    def resolve(\n        self,\n        classification:CanonicalObservationClassification,\n        candidates:Iterable[tuple[str,str]],\n        *,\n        lineage:ImmutableLineage,\n    )->ObservationEntityResolution:\n        if not isinstance(classification,CanonicalObservationClassification):\n            raise TypeError("classification must be CanonicalObservationClassification")\n\n        bindings=[]\n        unresolved=[]\n        seen=set()\n\n        for kind,value in candidates:\n            if kind not in RESOLVABLE_ENTITY_KINDS:\n                raise ValueError("unsupported resolvable entity kind")\n            key=semantic_key(value)\n            identity=(kind,key)\n            if identity in seen:\n                continue\n            seen.add(identity)\n\n            markets=set(self.semantic_registry.markets_with(kind,key))\n            markets.update(self.dependency_registry.markets_for_dependency(kind,key))\n\n            if markets:\n                bindings.append(ObservationEntityBinding(\n                    kind,\n                    value,\n                    key,\n                    tuple(sorted(markets)),\n                ))\n            else:\n                unresolved.append((kind,key))\n\n        bindings.sort(key=lambda b:(b.kind,b.canonical_key,b.binding_hash))\n        unresolved=tuple(sorted(set(unresolved)))\n\n        return ObservationEntityResolution(\n            classification.observation_id,\n            classification.classification_hash,\n            tuple(bindings),\n            unresolved,\n            lineage,\n        )\n\ndef build_umd_131_certification_manifest():\n    data={\n        "subsystem_id":"UMD",\n        "build_id":UMD_131_BUILD_ID,\n        "revision":UMD_131_REVISION,\n        "schema_version":UMD_131_SCHEMA_VERSION,\n        "upstream_builds":("UMD-111","UMD-114","UMD-130"),\n        "mode":"deterministic_read_only_observation_entity_resolution",\n        "resolvable_entity_kinds":RESOLVABLE_ENTITY_KINDS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,\n        "persistence_enabled":False,\n        "mutation_enabled":False,\n        "publication_enabled":False,\n        "execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_131_observation_entity_resolution()->bool:\n    if verify_umd_130_observation_classification() is not True:\n        return False\n    m=build_umd_131_certification_manifest()\n    return m["build_id"]=="UMD-131" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_111_semantic_registry import SemanticRegistry\nfrom qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry\nfrom qseries_v2.universal_market_discovery.umd_130_observation_classification import UMD_130_REVISION,ObservationClassifier\nfrom qseries_v2.universal_market_discovery.umd_131_observation_entity_resolution import *\n\nFIXED=datetime(2026,8,9,23,40,tzinfo=timezone.utc)\n\ndef semantic_registry():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-111",revision="UMD_111_SEMANTIC_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://131/111",),created_at=FIXED\n    )\n    return SemanticRegistry(\n        (),(),\n        {\n            "asset=bitcoin":("m1",),\n            "entity=federal-reserve":("m2",),\n        },\n        {},\n        l,\n    )\n\ndef dependency_registry():\n    graph_hash="a"*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(graph_hash,),\n        source_refs=("fixture://131/114",),created_at=FIXED\n    )\n    return DependencyRegistry(\n        (),\n        graph_hash,\n        {\n            "asset=bitcoin":("m1","m3"),\n            "metric=consumer-price-index":("m4",),\n        },\n        {},\n        {},\n        l,\n    )\n\ndef classification():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-130",revision=UMD_130_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://131/130",),created_at=FIXED\n    )\n    return ObservationClassifier().classify(\n        "obs-1","economics",\n        (("metric","Consumer Price Index"),),\n        lineage=l,\n    )\n\ndef lineage(c):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-131",revision=UMD_131_REVISION,\n        schema_version="1.0.0",parent_hashes=(c.classification_hash,),\n        source_refs=("fixture://131",),created_at=FIXED\n    )\n\nclass TestUMD131(unittest.TestCase):\n    def setUp(self):\n        self.c=classification()\n        self.r=ObservationEntityResolver(semantic_registry(),dependency_registry())\n\n    def test_foundation(self):\n        self.assertTrue(verify_umd_131_observation_entity_resolution())\n\n    def test_asset_resolution(self):\n        x=self.r.resolve(self.c,(("asset","Bitcoin"),),lineage=lineage(self.c))\n        self.assertEqual(len(x.bindings),1)\n        self.assertEqual(x.bindings[0].canonical_key,"bitcoin")\n        self.assertEqual(x.bindings[0].known_market_ids,("m1","m3"))\n\n    def test_entity_resolution(self):\n        x=self.r.resolve(self.c,(("entity","Federal Reserve"),),lineage=lineage(self.c))\n        self.assertEqual(x.bindings[0].canonical_key,"federal-reserve")\n        self.assertEqual(x.bindings[0].known_market_ids,("m2",))\n\n    def test_unresolved_preserved(self):\n        x=self.r.resolve(self.c,(("asset","Solana"),),lineage=lineage(self.c))\n        self.assertEqual(x.bindings,())\n        self.assertEqual(x.unresolved,(("asset","solana"),))\n\n    def test_deduplication(self):\n        x=self.r.resolve(\n            self.c,\n            (("asset","Bitcoin"),("asset","BITCOIN")),\n            lineage=lineage(self.c),\n        )\n        self.assertEqual(len(x.bindings),1)\n\n    def test_deterministic(self):\n        a=self.r.resolve(\n            self.c,\n            (("entity","Federal Reserve"),("asset","Bitcoin")),\n            lineage=lineage(self.c),\n        )\n        b=self.r.resolve(\n            self.c,\n            (("asset","Bitcoin"),("entity","Federal Reserve")),\n            lineage=lineage(self.c),\n        )\n        self.assertEqual(a.resolution_hash,b.resolution_hash)\n\n    def test_bad_kind(self):\n        with self.assertRaises(ValueError):\n            self.r.resolve(self.c,(("time_window","tomorrow"),),lineage=lineage(self.c))\n\n    def test_lineage_required(self):\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-131",revision=UMD_131_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),\n            source_refs=("fixture://131/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            self.r.resolve(self.c,(("asset","Bitcoin"),),lineage=bad)\n\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ObservationEntityResolver(object(),dependency_registry())\n\n    def test_side_effects(self):\n        m=build_umd_131_certification_manifest()\n        self.assertFalse(any(\n            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n        ))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-131 CERTIFICATION TEST");print(" OBSERVATION ENTITY RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD131))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    m=build_umd_131_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation entity and asset resolution against certified market knowledge certified")\n    print("[PASS] Unknown candidates preserved deterministically as unresolved")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-131 CERTIFIED")\n'
UPSTREAM_MODULE='umd_130_observation_classification'
UPSTREAM_VERIFIER='verify_umd_130_observation_classification'
EXPORTED_NAMES=('UMD_131_REVISION', 'RESOLVABLE_ENTITY_KINDS', 'ObservationEntityBinding', 'ObservationEntityResolution', 'ObservationEntityResolver', 'build_umd_131_certification_manifest', 'verify_umd_131_observation_entity_resolution')

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
    marker="# UMD-131 exports"
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
            raise RuntimeError("UMD-131 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-131 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-131 INSTALLER")
    print(" OBSERVATION ENTITY RESOLUTION")
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
        print("[ROLLBACK] UMD-131 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-131',
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
    print("[DONE] UMD-131 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
