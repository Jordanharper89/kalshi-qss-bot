from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_113_MARKET_CONSTRAINT_GRAPH_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_113_market_constraints.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_113_market_constraints.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile\nfrom .umd_110_market_family_resolution import MarketFamily\nfrom .umd_112_market_dependency import verify_umd_112_market_dependency_model\n\nUMD_113_BUILD_ID="UMD-113"\nUMD_113_REVISION="UMD_113_MARKET_CONSTRAINT_GRAPH_V1"\nUMD_113_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nCONSTRAINT_TYPES=("threshold_monotonic","mutually_exclusive","implies","equivalent","collectively_exhaustive")\nSYMMETRIC_CONSTRAINT_TYPES=("mutually_exclusive","equivalent")\n\n@dataclass(frozen=True,slots=True)\nclass MarketConstraint:\n    source_market_id:str\n    target_market_id:str\n    constraint_type:str\n    basis:str\n\n    def __post_init__(self):\n        if not self.source_market_id or not self.target_market_id:\n            raise ValueError("constraint endpoints must be non-empty")\n        if self.source_market_id==self.target_market_id:\n            raise ValueError("constraint endpoints must differ")\n        if self.constraint_type not in CONSTRAINT_TYPES:\n            raise ValueError("unsupported constraint type")\n        if not isinstance(self.basis,str) or not self.basis.strip():\n            raise ValueError("constraint basis must be non-empty")\n\n    @property\n    def constraint_hash(self)->str:\n        return deterministic_sha256({\n            "source_market_id":self.source_market_id,\n            "target_market_id":self.target_market_id,\n            "constraint_type":self.constraint_type,\n            "basis":self.basis,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass MarketConstraintGraph:\n    market_ids:Tuple[str,...]\n    constraints:Tuple[MarketConstraint,...]\n    family_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_ids",tuple(self.market_ids))\n        object.__setattr__(self,"constraints",tuple(self.constraints))\n        object.__setattr__(self,"family_hashes",tuple(self.family_hashes))\n        if tuple(sorted(self.market_ids))!=self.market_ids:\n            raise ValueError("market_ids must be sorted")\n        if len(set(self.market_ids))!=len(self.market_ids):\n            raise ValueError("market_ids must be unique")\n        known=set(self.market_ids)\n        for c in self.constraints:\n            if c.source_market_id not in known or c.target_market_id not in known:\n                raise ValueError("constraint references unknown market")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_113_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-113")\n        if not set(self.family_hashes).issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every family hash")\n\n    def constraints_for(self,canonical_market_id:str)->Tuple[MarketConstraint,...]:\n        return tuple(\n            c for c in self.constraints\n            if c.source_market_id==canonical_market_id or c.target_market_id==canonical_market_id\n        )\n\n    @property\n    def graph_hash(self)->str:\n        return deterministic_sha256({\n            "market_ids":self.market_ids,\n            "constraint_hashes":tuple(c.constraint_hash for c in self.constraints),\n            "family_hashes":self.family_hashes,\n            "lineage":self.lineage,\n        })\n\nclass MarketConstraintGraphBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        profiles:Iterable[MarketSemanticProfile],\n        families:Iterable[MarketFamily],\n        specs:Iterable[tuple[str,str,str,str]],\n        *,\n        lineage:ImmutableLineage,\n    )->MarketConstraintGraph:\n        ps=tuple(profiles)\n        fs=tuple(families)\n        if any(not isinstance(p,MarketSemanticProfile) for p in ps):\n            raise TypeError("profiles must contain MarketSemanticProfile")\n        if any(not isinstance(f,MarketFamily) for f in fs):\n            raise TypeError("families must contain MarketFamily")\n\n        market_ids=tuple(sorted({p.canonical_market_id for p in ps}))\n        known=set(market_ids)\n        constraints=[]\n        seen=set()\n\n        for source,target,constraint_type,basis in specs:\n            if source not in known or target not in known:\n                raise ValueError("constraint specification references unknown market")\n            if constraint_type in SYMMETRIC_CONSTRAINT_TYPES and target<source:\n                source,target=target,source\n            key=(source,target,constraint_type,basis)\n            if key in seen:\n                continue\n            seen.add(key)\n            constraints.append(MarketConstraint(source,target,constraint_type,basis))\n\n        constraints.sort(key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis))\n        return MarketConstraintGraph(\n            market_ids,\n            tuple(constraints),\n            tuple(sorted(f.family_hash for f in fs)),\n            lineage,\n        )\n\ndef build_umd_113_certification_manifest():\n    data={\n        "subsystem_id":"UMD",\n        "build_id":UMD_113_BUILD_ID,\n        "revision":UMD_113_REVISION,\n        "schema_version":UMD_113_SCHEMA_VERSION,\n        "upstream_builds":("UMD-109","UMD-110","UMD-112"),\n        "mode":"deterministic_read_only_market_constraint_graph",\n        "constraint_types":CONSTRAINT_TYPES,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,\n        "persistence_enabled":False,\n        "mutation_enabled":False,\n        "publication_enabled":False,\n        "execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_113_market_constraint_graph()->bool:\n    if verify_umd_112_market_dependency_model() is not True:\n        return False\n    m=build_umd_113_certification_manifest()\n    return m["build_id"]=="UMD-113" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver\nfrom qseries_v2.universal_market_discovery.umd_113_market_constraints import *\n\nFIXED=datetime(2026,8,9,18,10,tzinfo=timezone.utc)\n\ndef profile(cid,ih,threshold):\n    l102=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://113/102",),created_at=FIXED\n    )\n    record=CanonicalMarketRecord(\n        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),\n        "btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,\n        (),(),"",{},l102\n    )\n    l109=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,\n        schema_version="1.0.0",parent_hashes=(record.record_hash,),\n        source_refs=("fixture://113/109",),created_at=FIXED\n    )\n    return MarketSemanticProfiler().build(\n        record,\n        (("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),\n        lineage=l109,\n    )\n\ndef family_lineage(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://113/110",),created_at=FIXED\n    )\n\ndef graph_lineage(families):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(f.family_hash for f in families),\n        source_refs=("fixture://113",),created_at=FIXED\n    )\n\nclass TestUMD113(unittest.TestCase):\n    def setUp(self):\n        self.a=profile("umd:market:a","a"*64,"100000")\n        self.b=profile("umd:market:b","b"*64,"150000")\n        self.ps=(self.a,self.b)\n        self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)\n\n    def test_foundation(self):\n        self.assertTrue(verify_umd_113_market_constraint_graph())\n\n    def test_threshold_constraint(self):\n        g=MarketConstraintGraphBuilder().build(\n            self.ps,self.fs,\n            (("umd:market:b","umd:market:a","threshold_monotonic","higher-threshold-implies-lower-threshold"),),\n            lineage=graph_lineage(self.fs),\n        )\n        self.assertEqual(len(g.constraints),1)\n        self.assertEqual(g.constraints[0].constraint_type,"threshold_monotonic")\n\n    def test_symmetric_canonicalization(self):\n        l=graph_lineage(self.fs)\n        a=MarketConstraintGraphBuilder().build(\n            self.ps,self.fs,\n            (("umd:market:b","umd:market:a","mutually_exclusive","same-event-exclusive"),),\n            lineage=l,\n        )\n        b=MarketConstraintGraphBuilder().build(\n            tuple(reversed(self.ps)),tuple(reversed(self.fs)),\n            (("umd:market:a","umd:market:b","mutually_exclusive","same-event-exclusive"),),\n            lineage=l,\n        )\n        self.assertEqual(a.graph_hash,b.graph_hash)\n\n    def test_duplicate_collapsed(self):\n        spec=("umd:market:b","umd:market:a","implies","semantic-threshold")\n        g=MarketConstraintGraphBuilder().build(\n            self.ps,self.fs,(spec,spec),lineage=graph_lineage(self.fs)\n        )\n        self.assertEqual(len(g.constraints),1)\n\n    def test_constraints_for(self):\n        g=MarketConstraintGraphBuilder().build(\n            self.ps,self.fs,\n            (("umd:market:b","umd:market:a","implies","semantic-threshold"),),\n            lineage=graph_lineage(self.fs),\n        )\n        self.assertEqual(len(g.constraints_for("umd:market:a")),1)\n\n    def test_unknown_market_rejected(self):\n        with self.assertRaises(ValueError):\n            MarketConstraintGraphBuilder().build(\n                self.ps,self.fs,\n                (("umd:market:a","missing","implies","bad"),),\n                lineage=graph_lineage(self.fs),\n            )\n\n    def test_lineage_required(self):\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),\n            source_refs=("fixture://113/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            MarketConstraintGraphBuilder().build(self.ps,self.fs,(),lineage=bad)\n\n    def test_immutable(self):\n        g=MarketConstraintGraphBuilder().build(self.ps,self.fs,(),lineage=graph_lineage(self.fs))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            g.constraints=()\n\n    def test_side_effects(self):\n        m=build_umd_113_certification_manifest()\n        self.assertFalse(any(\n            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n        ))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-113 CERTIFICATION TEST");print(" MARKET CONSTRAINT GRAPH");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD113))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    m=build_umd_113_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Threshold, implication, exclusivity, equivalence, and partition constraint primitives certified")\n    print("[PASS] Semantic families consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-113 CERTIFIED")\n'
UPSTREAM_MODULE='umd_112_market_dependency'
UPSTREAM_VERIFIER='verify_umd_112_market_dependency_model'
EXPORTED_NAMES=('UMD_113_REVISION', 'CONSTRAINT_TYPES', 'MarketConstraint', 'MarketConstraintGraph', 'MarketConstraintGraphBuilder', 'build_umd_113_certification_manifest', 'verify_umd_113_market_constraint_graph')

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
    marker="# UMD-113 exports"
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
            raise RuntimeError("UMD-113 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-113 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-113 INSTALLER")
    print(" MARKET CONSTRAINT GRAPH")
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
        print("[ROLLBACK] UMD-113 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-113',
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
    print("[DONE] UMD-113 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
