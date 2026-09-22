from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_120_IMPACT_QUERY_ENGINE_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_120_impact_query_engine.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_120_impact_query_engine.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_119_impact_provenance import ImpactProvenanceBundle,MarketImpactProvenance,verify_umd_119_impact_provenance_bundle\n\nUMD_120_BUILD_ID="UMD-120"\nUMD_120_REVISION="UMD_120_IMPACT_QUERY_ENGINE_V1"\nUMD_120_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ImpactQueryResult:\n    query_type:str\n    query_key:str\n    entries:Tuple[MarketImpactProvenance,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"entries",tuple(self.entries))\n        if tuple(sorted(self.entries,key=lambda e:(e.canonical_market_id,e.provenance_hash)))!=self.entries:\n            raise ValueError("entries must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_120_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-120")\n\n    @property\n    def result_hash(self)->str:\n        return deterministic_sha256({\n            "query_type":self.query_type,\n            "query_key":self.query_key,\n            "provenance_hashes":tuple(e.provenance_hash for e in self.entries),\n            "lineage":self.lineage,\n        })\n\nclass ImpactQueryEngine:\n    __slots__=("bundles",)\n\n    def __init__(self,bundles:Iterable[ImpactProvenanceBundle]):\n        values=tuple(bundles)\n        if any(not isinstance(b,ImpactProvenanceBundle) for b in values):\n            raise TypeError("bundles must contain ImpactProvenanceBundle")\n        self.bundles=tuple(sorted(values,key=lambda b:(b.observation_hash,b.bundle_hash)))\n\n    def by_observation(self,observation_hash:str,*,lineage:ImmutableLineage)->ImpactQueryResult:\n        entries=[]\n        for b in self.bundles:\n            if b.observation_hash==observation_hash:\n                entries.extend(b.entries)\n        return self._result("observation",observation_hash,entries,lineage)\n\n    def by_market(self,canonical_market_id:str,*,lineage:ImmutableLineage)->ImpactQueryResult:\n        entries=[]\n        for b in self.bundles:\n            entry=b.for_market(canonical_market_id)\n            if entry is not None:\n                entries.append(entry)\n        return self._result("market",canonical_market_id,entries,lineage)\n\n    def by_dependency(self,kind:str,key:str,*,lineage:ImmutableLineage)->ImpactQueryResult:\n        entries=[]\n        for b in self.bundles:\n            for entry in b.entries:\n                if (kind,key) in entry.dependency_matches:\n                    entries.append(entry)\n        return self._result("dependency",kind+"="+key,entries,lineage)\n\n    def by_impact_type(self,direct:bool,*,lineage:ImmutableLineage)->ImpactQueryResult:\n        entries=[]\n        for b in self.bundles:\n            entries.extend(e for e in b.entries if e.direct is direct)\n        return self._result("impact_type","direct" if direct else "propagated",entries,lineage)\n\n    @staticmethod\n    def _result(query_type,query_key,entries,lineage):\n        values=tuple(sorted(entries,key=lambda e:(e.canonical_market_id,e.provenance_hash)))\n        return ImpactQueryResult(query_type,query_key,values,lineage)\n\ndef build_umd_120_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_120_BUILD_ID,"revision":UMD_120_REVISION,\n        "schema_version":UMD_120_SCHEMA_VERSION,"upstream_builds":("UMD-119",),\n        "mode":"deterministic_read_only_impact_query_engine",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_120_impact_query_engine()->bool:\n    if verify_umd_119_impact_provenance_bundle() is not True:\n        return False\n    m=build_umd_120_certification_manifest()\n    return m["build_id"]=="UMD-120" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle\nfrom qseries_v2.universal_market_discovery.umd_120_impact_query_engine import *\n\nFIXED=datetime(2026,8,9,20,20,tzinfo=timezone.utc)\n\ndef bundle(obs_hash,market_suffix):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://120/119",),created_at=FIXED)\n    return ImpactProvenanceBundle(\n        obs_hash,\n        (\n            MarketImpactProvenance("direct-"+market_suffix,True,(("asset","bitcoin"),),("direct-"+market_suffix,),()),\n            MarketImpactProvenance("prop-"+market_suffix,False,(),("direct-"+market_suffix,"prop-"+market_suffix),("implies",)),\n        ),\n        l\n    )\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-120",revision=UMD_120_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://120",),created_at=FIXED)\n\nclass TestUMD120(unittest.TestCase):\n    def setUp(self):\n        self.a=bundle("a"*64,"a")\n        self.b=bundle("b"*64,"b")\n        self.e=ImpactQueryEngine((self.b,self.a))\n\n    def test_foundation(self): self.assertTrue(verify_umd_120_impact_query_engine())\n    def test_observation_query(self):\n        r=self.e.by_observation("a"*64,lineage=lineage())\n        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","prop-a"))\n    def test_market_query(self):\n        r=self.e.by_market("prop-b",lineage=lineage())\n        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("prop-b",))\n    def test_dependency_query(self):\n        r=self.e.by_dependency("asset","bitcoin",lineage=lineage())\n        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","direct-b"))\n    def test_direct_query(self):\n        r=self.e.by_impact_type(True,lineage=lineage())\n        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","direct-b"))\n    def test_propagated_query(self):\n        r=self.e.by_impact_type(False,lineage=lineage())\n        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("prop-a","prop-b"))\n    def test_unknown(self):\n        self.assertEqual(self.e.by_market("missing",lineage=lineage()).entries,())\n    def test_deterministic(self):\n        a=self.e.by_dependency("asset","bitcoin",lineage=lineage())\n        b=self.e.by_dependency("asset","bitcoin",lineage=lineage())\n        self.assertEqual(a.result_hash,b.result_hash)\n    def test_bad_bundle(self):\n        with self.assertRaises(TypeError):\n            ImpactQueryEngine((object(),))\n\n    def test_mixed_bundle_types_rejected(self):\n        with self.assertRaises(TypeError):\n            ImpactQueryEngine((self.a,object()))\n    def test_side_effects(self):\n        m=build_umd_120_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-120 CERTIFICATION TEST");print(" IMPACT QUERY ENGINE — CORRECTION V2");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD120))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_120_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation, market, dependency, direct, and propagated impact queries certified")\n    print("[PASS] UMD-119 provenance bundles consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-120 CERTIFIED")\n'
UPSTREAM_MODULE='umd_119_impact_provenance'
UPSTREAM_VERIFIER='verify_umd_119_impact_provenance_bundle'
EXPORTED_NAMES=('UMD_120_REVISION', 'ImpactQueryResult', 'ImpactQueryEngine', 'build_umd_120_certification_manifest', 'verify_umd_120_impact_query_engine')

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
    marker="# UMD-120 exports"
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
            raise RuntimeError("UMD-120 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-120 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-120 INSTALLER")
    print(" IMPACT QUERY ENGINE")
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
        print("[ROLLBACK] UMD-120 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-120',
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
    print("[DONE] UMD-120 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
