from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_114_DEPENDENCY_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_114_dependency_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_114_dependency_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_112_market_dependency import MarketDependencyProfile\nfrom .umd_113_market_constraints import MarketConstraintGraph, verify_umd_113_market_constraint_graph\n\nUMD_114_BUILD_ID="UMD-114"\nUMD_114_REVISION="UMD_114_DEPENDENCY_REGISTRY_V1"\nUMD_114_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({\n        key:tuple(value)\n        for key,value in sorted(source.items())\n    })\n\n@dataclass(frozen=True,slots=True)\nclass DependencyRegistry:\n    profiles:Tuple[MarketDependencyProfile,...]\n    constraint_graph_hash:str\n    dependency_index:Mapping[str,Tuple[str,...]]\n    role_index:Mapping[str,Tuple[str,...]]\n    constraint_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"profiles",tuple(self.profiles))\n        object.__setattr__(self,"dependency_index",_freeze_index(self.dependency_index))\n        object.__setattr__(self,"role_index",_freeze_index(self.role_index))\n        object.__setattr__(self,"constraint_index",_freeze_index(self.constraint_index))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_114_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-114")\n        required={p.profile_hash for p in self.profiles}|{self.constraint_graph_hash}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include dependency profiles and constraint graph hash")\n\n    def markets_for_dependency(self,kind:str,key:str)->Tuple[str,...]:\n        return self.dependency_index.get(kind+"="+key,())\n\n    def markets_for_role(self,role:str)->Tuple[str,...]:\n        return self.role_index.get(role,())\n\n    def markets_for_constraint(self,constraint_type:str)->Tuple[str,...]:\n        return self.constraint_index.get(constraint_type,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "profile_hashes":tuple(p.profile_hash for p in self.profiles),\n            "constraint_graph_hash":self.constraint_graph_hash,\n            "dependency_index":self.dependency_index,\n            "role_index":self.role_index,\n            "constraint_index":self.constraint_index,\n            "lineage":self.lineage,\n        })\n\nclass DependencyRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        profiles:Iterable[MarketDependencyProfile],\n        constraint_graph:MarketConstraintGraph,\n        *,\n        lineage:ImmutableLineage,\n    )->DependencyRegistry:\n        ps=tuple(sorted(profiles,key=lambda p:p.canonical_market_id))\n        if any(not isinstance(p,MarketDependencyProfile) for p in ps):\n            raise TypeError("profiles must contain MarketDependencyProfile")\n        if not isinstance(constraint_graph,MarketConstraintGraph):\n            raise TypeError("constraint_graph must be MarketConstraintGraph")\n\n        dependency={}\n        role={}\n        constraint={}\n\n        for p in ps:\n            for d in p.dependencies:\n                dependency.setdefault(d.kind+"="+d.key,[]).append(p.canonical_market_id)\n                role.setdefault(d.role,[]).append(p.canonical_market_id)\n\n        for c in constraint_graph.constraints:\n            bucket=constraint.setdefault(c.constraint_type,[])\n            bucket.extend((c.source_market_id,c.target_market_id))\n\n        for index in (dependency,role,constraint):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        return DependencyRegistry(\n            ps,\n            constraint_graph.graph_hash,\n            dependency,\n            role,\n            constraint,\n            lineage,\n        )\n\ndef build_umd_114_certification_manifest():\n    data={\n        "subsystem_id":"UMD",\n        "build_id":UMD_114_BUILD_ID,\n        "revision":UMD_114_REVISION,\n        "schema_version":UMD_114_SCHEMA_VERSION,\n        "upstream_builds":("UMD-112","UMD-113"),\n        "mode":"deterministic_read_only_dependency_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,\n        "persistence_enabled":False,\n        "mutation_enabled":False,\n        "publication_enabled":False,\n        "execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_114_dependency_registry()->bool:\n    if verify_umd_113_market_constraint_graph() is not True:\n        return False\n    m=build_umd_114_certification_manifest()\n    return m["build_id"]=="UMD-114" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver\nfrom qseries_v2.universal_market_discovery.umd_112_market_dependency import UMD_112_REVISION,MarketDependencyBuilder\nfrom qseries_v2.universal_market_discovery.umd_113_market_constraints import UMD_113_REVISION,MarketConstraintGraphBuilder\nfrom qseries_v2.universal_market_discovery.umd_114_dependency_registry import *\n\nFIXED=datetime(2026,8,9,18,20,tzinfo=timezone.utc)\n\ndef semantic_profile(cid,ih,asset,threshold):\n    l102=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://114/102",),created_at=FIXED\n    )\n    record=CanonicalMarketRecord(\n        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),\n        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102\n    )\n    l109=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,\n        schema_version="1.0.0",parent_hashes=(record.record_hash,),\n        source_refs=("fixture://114/109",),created_at=FIXED\n    )\n    return MarketSemanticProfiler().build(\n        record,\n        (("asset",asset),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),\n        lineage=l109,\n    )\n\ndef family_lineage(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://114/110",),created_at=FIXED\n    )\n\ndef dependency_profile(profile,metric):\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,\n        schema_version="1.0.0",parent_hashes=(profile.profile_hash,),\n        source_refs=("fixture://114/112",),created_at=FIXED\n    )\n    return MarketDependencyBuilder().build(\n        profile,\n        (("asset","Bitcoin","required"),("metric",metric,"required")),\n        lineage=l,\n    )\n\ndef constraint_graph(ps,fs):\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(f.family_hash for f in fs),\n        source_refs=("fixture://114/113",),created_at=FIXED\n    )\n    return MarketConstraintGraphBuilder().build(\n        ps,fs,\n        (("umd:market:b","umd:market:a","threshold_monotonic","higher-threshold-implies-lower-threshold"),),\n        lineage=l,\n    )\n\ndef registry_lineage(dps,graph):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-114",revision=UMD_114_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(d.profile_hash for d in dps)+(graph.graph_hash,),\n        source_refs=("fixture://114",),created_at=FIXED\n    )\n\nclass TestUMD114(unittest.TestCase):\n    def setUp(self):\n        self.a=semantic_profile("umd:market:a","a"*64,"Bitcoin","100000")\n        self.b=semantic_profile("umd:market:b","b"*64,"Bitcoin","150000")\n        self.ps=(self.a,self.b)\n        self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)\n        self.da=dependency_profile(self.a,"BTC Spot Price")\n        self.db=dependency_profile(self.b,"BTC Spot Price")\n        self.dps=(self.da,self.db)\n        self.graph=constraint_graph(self.ps,self.fs)\n        self.registry=DependencyRegistryBuilder().build(\n            self.dps,self.graph,lineage=registry_lineage(self.dps,self.graph)\n        )\n\n    def test_foundation(self):\n        self.assertTrue(verify_umd_114_dependency_registry())\n\n    def test_dependency_query(self):\n        self.assertEqual(\n            self.registry.markets_for_dependency("metric","btc-spot-price"),\n            ("umd:market:a","umd:market:b"),\n        )\n\n    def test_asset_dependency_query(self):\n        self.assertEqual(\n            self.registry.markets_for_dependency("asset","bitcoin"),\n            ("umd:market:a","umd:market:b"),\n        )\n\n    def test_role_query(self):\n        self.assertEqual(\n            self.registry.markets_for_role("required"),\n            ("umd:market:a","umd:market:b"),\n        )\n\n    def test_constraint_query(self):\n        self.assertEqual(\n            self.registry.markets_for_constraint("threshold_monotonic"),\n            ("umd:market:a","umd:market:b"),\n        )\n\n    def test_unknown_dependency(self):\n        self.assertEqual(\n            self.registry.markets_for_dependency("metric","eth-spot-price"),\n            (),\n        )\n\n    def test_deterministic(self):\n        x=DependencyRegistryBuilder().build(\n            tuple(reversed(self.dps)),\n            self.graph,\n            lineage=registry_lineage(self.dps,self.graph),\n        )\n        self.assertEqual(self.registry.registry_hash,x.registry_hash)\n\n    def test_immutable_index(self):\n        with self.assertRaises(TypeError):\n            self.registry.dependency_index["metric=btc-spot-price"]=()\n\n    def test_bad_graph(self):\n        with self.assertRaises(TypeError):\n            DependencyRegistryBuilder().build(\n                self.dps,\n                object(),\n                lineage=registry_lineage(self.dps,self.graph),\n            )\n\n    def test_lineage_required(self):\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-114",revision=UMD_114_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),\n            source_refs=("fixture://114/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            DependencyRegistryBuilder().build(self.dps,self.graph,lineage=bad)\n\n    def test_side_effects(self):\n        m=build_umd_114_certification_manifest()\n        self.assertFalse(any(\n            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n        ))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-114 CERTIFICATION TEST");print(" DEPENDENCY REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD114))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    m=build_umd_114_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Dependency-to-market and constraint-to-market queries certified")\n    print("[PASS] UMD-112 and UMD-113 consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-114 CERTIFIED")\n'
UPSTREAM_MODULE='umd_113_market_constraints'
UPSTREAM_VERIFIER='verify_umd_113_market_constraint_graph'
EXPORTED_NAMES=('UMD_114_REVISION', 'DependencyRegistry', 'DependencyRegistryBuilder', 'build_umd_114_certification_manifest', 'verify_umd_114_dependency_registry')

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
    marker="# UMD-114 exports"
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
            raise RuntimeError("UMD-114 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-114 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-114 INSTALLER")
    print(" DEPENDENCY REGISTRY")
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
        print("[ROLLBACK] UMD-114 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-114',
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
    print("[DONE] UMD-114 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
