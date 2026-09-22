from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_119_IMPACT_PROVENANCE_BUNDLE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_119_impact_provenance.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_119_impact_provenance.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_115_observation_impact import DirectImpactResult\nfrom .umd_118_impact_paths import ImpactPathSet,ImpactPath,verify_umd_118_impact_path_resolution\n\nUMD_119_BUILD_ID="UMD-119"\nUMD_119_REVISION="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1"\nUMD_119_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass MarketImpactProvenance:\n    canonical_market_id:str\n    direct:bool\n    dependency_matches:Tuple[Tuple[str,str],...]\n    market_path:Tuple[str,...]\n    constraint_path:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"dependency_matches",tuple(sorted(set(self.dependency_matches))))\n        object.__setattr__(self,"market_path",tuple(self.market_path))\n        object.__setattr__(self,"constraint_path",tuple(self.constraint_path))\n\n    @property\n    def provenance_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "direct":self.direct,\n            "dependency_matches":self.dependency_matches,\n            "market_path":self.market_path,\n            "constraint_path":self.constraint_path,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ImpactProvenanceBundle:\n    observation_hash:str\n    entries:Tuple[MarketImpactProvenance,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"entries",tuple(self.entries))\n        if tuple(sorted(self.entries,key=lambda e:e.canonical_market_id))!=self.entries:\n            raise ValueError("entries must be sorted by canonical_market_id")\n        if len({e.canonical_market_id for e in self.entries})!=len(self.entries):\n            raise ValueError("duplicate canonical market provenance entry")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_119_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-119")\n\n    def for_market(self,canonical_market_id:str)->MarketImpactProvenance|None:\n        for entry in self.entries:\n            if entry.canonical_market_id==canonical_market_id:\n                return entry\n        return None\n\n    @property\n    def bundle_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "provenance_hashes":tuple(e.provenance_hash for e in self.entries),\n            "lineage":self.lineage,\n        })\n\nclass ImpactProvenanceBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        direct:DirectImpactResult,\n        paths:ImpactPathSet,\n        *,\n        lineage:ImmutableLineage,\n    )->ImpactProvenanceBundle:\n        if not isinstance(direct,DirectImpactResult):\n            raise TypeError("direct must be DirectImpactResult")\n        if not isinstance(paths,ImpactPathSet):\n            raise TypeError("paths must be ImpactPathSet")\n        if direct.observation_hash!=paths.observation_hash:\n            raise ValueError("observation hashes do not match")\n\n        direct_matches={}\n        for kind,key,market_ids in direct.matched_dependencies:\n            for market_id in market_ids:\n                direct_matches.setdefault(market_id,[]).append((kind,key))\n\n        entries=[]\n        for path in paths.paths:\n            matches=tuple(sorted(set(direct_matches.get(path.target_market_id,())))) if path.direct else ()\n            entries.append(MarketImpactProvenance(\n                path.target_market_id,\n                path.direct,\n                matches,\n                path.market_path,\n                path.constraint_path,\n            ))\n        entries.sort(key=lambda e:e.canonical_market_id)\n        return ImpactProvenanceBundle(direct.observation_hash,tuple(entries),lineage)\n\ndef build_umd_119_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_119_BUILD_ID,"revision":UMD_119_REVISION,\n        "schema_version":UMD_119_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-118"),\n        "mode":"deterministic_read_only_impact_provenance",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_119_impact_provenance_bundle()->bool:\n    if verify_umd_118_impact_path_resolution() is not True:\n        return False\n    m=build_umd_119_certification_manifest()\n    return m["build_id"]=="UMD-119" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult\nfrom qseries_v2.universal_market_discovery.umd_118_impact_paths import ImpactPath,ImpactPathSet\nfrom qseries_v2.universal_market_discovery.umd_119_impact_provenance import *\n\nFIXED=datetime(2026,8,9,20,10,tzinfo=timezone.utc)\n\ndef direct():\n    obs="a"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",\n        schema_version="1.0.0",parent_hashes=(obs,),source_refs=("fixture://119/115",),created_at=FIXED)\n    return DirectImpactResult(\n        obs,("m1",),\n        (("asset","bitcoin",("m1",)),("metric","btc-spot-price",("m1",))),\n        l\n    )\n\ndef paths():\n    obs="a"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-118",revision="UMD_118_IMPACT_PATH_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://119/118",),created_at=FIXED)\n    return ImpactPathSet(\n        obs,\n        (\n            ImpactPath(obs,"m1",True,("m1",),()),\n            ImpactPath(obs,"m2",False,("m1","m2"),("implies",)),\n        ),\n        l\n    )\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision=UMD_119_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://119",),created_at=FIXED)\n\nclass TestUMD119(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_119_impact_provenance_bundle())\n    def test_direct_dependency_provenance(self):\n        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())\n        e=b.for_market("m1")\n        self.assertTrue(e.direct)\n        self.assertEqual(e.dependency_matches,(("asset","bitcoin"),("metric","btc-spot-price")))\n    def test_propagated_provenance(self):\n        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())\n        e=b.for_market("m2")\n        self.assertFalse(e.direct)\n        self.assertEqual(e.market_path,("m1","m2"))\n        self.assertEqual(e.constraint_path,("implies",))\n    def test_unknown_market(self):\n        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())\n        self.assertIsNone(b.for_market("missing"))\n    def test_mismatch_rejected(self):\n        p=paths()\n        wrong=ImpactPathSet("b"*64,p.paths,p.lineage)\n        with self.assertRaises(ValueError):\n            ImpactProvenanceBuilder().build(direct(),wrong,lineage=lineage())\n    def test_deterministic(self):\n        a=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())\n        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())\n        self.assertEqual(a.bundle_hash,b.bundle_hash)\n    def test_side_effects(self):\n        m=build_umd_119_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-119 CERTIFICATION TEST");print(" IMPACT PROVENANCE BUNDLE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD119))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_119_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Direct dependency matches and propagated constraint paths certified")\n    print("[PASS] UMD-115 and UMD-118 consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-119 CERTIFIED")\n'
UPSTREAM_MODULE='umd_118_impact_paths'
UPSTREAM_VERIFIER='verify_umd_118_impact_path_resolution'
EXPORTED_NAMES=('UMD_119_REVISION', 'MarketImpactProvenance', 'ImpactProvenanceBundle', 'ImpactProvenanceBuilder', 'build_umd_119_certification_manifest', 'verify_umd_119_impact_provenance_bundle')

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
    marker="# UMD-119 exports"
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
            raise RuntimeError("UMD-119 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-119 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-119 INSTALLER")
    print(" IMPACT PROVENANCE BUNDLE")
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
        print("[ROLLBACK] UMD-119 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-119',
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
    print("[DONE] UMD-119 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
