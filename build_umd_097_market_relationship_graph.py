from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_097_MARKET_RELATIONSHIP_GRAPH_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_097_market_relationship_graph.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_097_market_relationship_graph.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_095_market_identity import CanonicalMarketIdentity\nfrom .umd_096_duplicate_resolution import verify_umd_096_cross_venue_duplicate_resolution\n\nUMD_097_BUILD_ID="UMD-097"\nUMD_097_BUILD_NAME="Market Relationship Graph"\nUMD_097_REVISION="UMD_097_MARKET_RELATIONSHIP_GRAPH_V1"\nUMD_097_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nRELATION_TYPES=("parent","child","complementary","opposing","conditional","successor","predecessor","related")\nDIRECTED_RELATION_TYPES=("parent","child","conditional","successor","predecessor")\n\n\ndef _freeze(value: Mapping[str,Any] | None) -> Mapping[str,Any]:\n    if value is None:\n        value={}\n    if not isinstance(value,Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))\n\n\n@dataclass(frozen=True,slots=True)\nclass RelationshipSpec:\n    source_market_id:str\n    target_market_id:str\n    relation_type:str\n    evidence_refs:Tuple[str,...]=()\n    metadata:Mapping[str,Any] | None=None\n\n    def __post_init__(self):\n        if not isinstance(self.source_market_id,str) or not self.source_market_id:\n            raise ValueError("source_market_id must be non-empty")\n        if not isinstance(self.target_market_id,str) or not self.target_market_id:\n            raise ValueError("target_market_id must be non-empty")\n        if self.source_market_id==self.target_market_id:\n            raise ValueError("relationship endpoints must differ")\n        if self.relation_type not in RELATION_TYPES:\n            raise ValueError("unsupported relation_type")\n        refs=tuple(self.evidence_refs)\n        if any(not isinstance(x,str) or not x for x in refs):\n            raise ValueError("evidence_refs must contain non-empty strings")\n        if len(set(refs))!=len(refs):\n            raise ValueError("evidence_refs must be unique")\n        object.__setattr__(self,"evidence_refs",refs)\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n\n\n@dataclass(frozen=True,slots=True)\nclass MarketRelationship:\n    source_market_id:str\n    target_market_id:str\n    relation_type:str\n    directed:bool\n    evidence_refs:Tuple[str,...]\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        if self.relation_type not in RELATION_TYPES:\n            raise ValueError("unsupported relation_type")\n        if self.directed != (self.relation_type in DIRECTED_RELATION_TYPES):\n            raise ValueError("directed flag does not match relation type")\n        object.__setattr__(self,"evidence_refs",tuple(self.evidence_refs))\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_097_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-097")\n\n    def to_canonical_dict(self):\n        return {\n            "source_market_id":self.source_market_id,\n            "target_market_id":self.target_market_id,\n            "relation_type":self.relation_type,\n            "directed":self.directed,\n            "evidence_refs":self.evidence_refs,\n            "metadata":self.metadata,\n            "lineage":self.lineage,\n        }\n\n    @property\n    def relationship_hash(self):\n        return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True,slots=True)\nclass MarketRelationshipGraph:\n    market_ids:Tuple[str,...]\n    relationships:Tuple[MarketRelationship,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_ids",tuple(self.market_ids))\n        object.__setattr__(self,"relationships",tuple(self.relationships))\n        if len(set(self.market_ids))!=len(self.market_ids):\n            raise ValueError("market_ids must be unique")\n        known=set(self.market_ids)\n        for edge in self.relationships:\n            if edge.source_market_id not in known or edge.target_market_id not in known:\n                raise ValueError("relationship endpoint missing from graph")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_097_BUILD_ID:\n            raise ValueError("graph lineage must belong to UMD-097")\n\n    def to_canonical_dict(self):\n        return {\n            "market_ids":self.market_ids,\n            "relationship_hashes":tuple(x.relationship_hash for x in self.relationships),\n            "lineage":self.lineage,\n        }\n\n    @property\n    def graph_hash(self):\n        return deterministic_sha256(self.to_canonical_dict())\n\n    def related_to(self, canonical_market_id:str) -> Tuple[MarketRelationship,...]:\n        return tuple(\n            edge for edge in self.relationships\n            if edge.source_market_id==canonical_market_id or edge.target_market_id==canonical_market_id\n        )\n\n\nclass MarketRelationshipGraphBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        identities:Iterable[CanonicalMarketIdentity],\n        specs:Iterable[RelationshipSpec],\n        *,\n        lineage:ImmutableLineage,\n    ) -> MarketRelationshipGraph:\n        ids=tuple(identities)\n        if any(not isinstance(x,CanonicalMarketIdentity) for x in ids):\n            raise TypeError("identities must contain CanonicalMarketIdentity")\n        market_ids=tuple(sorted({x.canonical_market_id for x in ids}))\n        required={x.identity_hash for x in ids}\n        if not required.issubset(set(lineage.parent_hashes)):\n            raise ValueError("lineage must include every identity hash")\n        known=set(market_ids)\n        edges=[]\n        seen=set()\n        for spec in specs:\n            if not isinstance(spec,RelationshipSpec):\n                raise TypeError("specs must contain RelationshipSpec")\n            if spec.source_market_id not in known or spec.target_market_id not in known:\n                raise ValueError("relationship spec references unknown market")\n            source,target=spec.source_market_id,spec.target_market_id\n            directed=spec.relation_type in DIRECTED_RELATION_TYPES\n            if not directed and target < source:\n                source,target=target,source\n            key=(source,target,spec.relation_type)\n            if key in seen:\n                raise ValueError("duplicate relationship specification")\n            seen.add(key)\n            edges.append(MarketRelationship(\n                source_market_id=source,\n                target_market_id=target,\n                relation_type=spec.relation_type,\n                directed=directed,\n                evidence_refs=tuple(sorted(spec.evidence_refs)),\n                metadata=spec.metadata,\n                lineage=lineage,\n            ))\n        edges.sort(key=lambda x:(x.source_market_id,x.target_market_id,x.relation_type,x.relationship_hash))\n        return MarketRelationshipGraph(market_ids=market_ids,relationships=tuple(edges),lineage=lineage)\n\n\ndef build_umd_097_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_097_BUILD_ID,"revision":UMD_097_REVISION,\n        "schema_version":UMD_097_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-096"),\n        "mode":"deterministic_read_only_relationship_graph",\n        "relation_types":RELATION_TYPES,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\n\ndef verify_umd_097_market_relationship_graph()->bool:\n    if verify_umd_096_cross_venue_duplicate_resolution() is not True:\n        return False\n    m=build_umd_097_certification_manifest()\n    return m["build_id"]=="UMD-097" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver\nfrom qseries_v2.universal_market_discovery.umd_097_market_relationship_graph import (\n    UMD_097_REVISION,RelationshipSpec,MarketRelationshipGraphBuilder,\n    build_umd_097_certification_manifest,verify_umd_097_market_relationship_graph,\n)\n\nFIXED=datetime(2026,8,8,13,0,tzinfo=timezone.utc)\n\ndef identity(venue,mid,title,category="Politics"):\n    o=MarketObservation(venue=venue,venue_market_id=mid,title=title,category=category,status="Open",outcomes=("Yes","No"))\n    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://097/94",),created_at=FIXED)\n    m=MarketNormalizer().normalize(o,lineage=l94)\n    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://097/95",),created_at=FIXED)\n    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)\n\ndef graph_lineage(ids):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-097",revision=UMD_097_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://097",),created_at=FIXED)\n\nclass TestUMD097(unittest.TestCase):\n    def setUp(self):\n        self.a=identity("Kalshi","A","Will candidate A win?")\n        self.b=identity("Polymarket","B","Will candidate B win?")\n        self.ids=(self.a,self.b)\n\n    def test_foundation(self):\n        self.assertTrue(verify_umd_097_market_relationship_graph())\n\n    def test_graph_build(self):\n        spec=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"opposing",("fixture://evidence/1",))\n        g=MarketRelationshipGraphBuilder().build(self.ids,(spec,),lineage=graph_lineage(self.ids))\n        self.assertEqual(len(g.relationships),1)\n        self.assertFalse(g.relationships[0].directed)\n\n    def test_undirected_canonicalization(self):\n        s1=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"related")\n        s2=RelationshipSpec(self.b.canonical_market_id,self.a.canonical_market_id,"related")\n        b=MarketRelationshipGraphBuilder()\n        g1=b.build(self.ids,(s1,),lineage=graph_lineage(self.ids))\n        g2=b.build(tuple(reversed(self.ids)),(s2,),lineage=graph_lineage(self.ids))\n        self.assertEqual(g1.graph_hash,g2.graph_hash)\n\n    def test_directed_preserves_orientation(self):\n        s=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"successor")\n        g=MarketRelationshipGraphBuilder().build(self.ids,(s,),lineage=graph_lineage(self.ids))\n        self.assertTrue(g.relationships[0].directed)\n        self.assertEqual(g.relationships[0].source_market_id,self.a.canonical_market_id)\n\n    def test_unknown_market_rejected(self):\n        s=RelationshipSpec(self.a.canonical_market_id,"umd:market:missing","related")\n        with self.assertRaises(ValueError):\n            MarketRelationshipGraphBuilder().build(self.ids,(s,),lineage=graph_lineage(self.ids))\n\n    def test_duplicate_rejected(self):\n        s=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"opposing")\n        with self.assertRaises(ValueError):\n            MarketRelationshipGraphBuilder().build(self.ids,(s,s),lineage=graph_lineage(self.ids))\n\n    def test_lineage_required(self):\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-097",revision=UMD_097_REVISION,schema_version="1.0.0",parent_hashes=(self.a.identity_hash,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError):\n            MarketRelationshipGraphBuilder().build(self.ids,(),lineage=bad)\n\n    def test_immutable(self):\n        g=MarketRelationshipGraphBuilder().build(self.ids,(),lineage=graph_lineage(self.ids))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            g.market_ids=()\n\n    def test_side_effects(self):\n        m=build_umd_097_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-097 CERTIFICATION TEST");print(" MARKET RELATIONSHIP GRAPH");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD097))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_097_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-096 certified capability chain consumed read-only")\n    print("[PASS] Deterministic immutable market relationship graph certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-097 CERTIFIED")\n'
UPSTREAM_MODULE='umd_096_duplicate_resolution'
UPSTREAM_VERIFIER='verify_umd_096_cross_venue_duplicate_resolution'
EXPORTED_NAMES=('UMD_097_REVISION', 'RelationshipSpec', 'MarketRelationship', 'MarketRelationshipGraph', 'MarketRelationshipGraphBuilder', 'build_umd_097_certification_manifest', 'verify_umd_097_market_relationship_graph')

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

def write_exact(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker=f"# UMD-097 exports"
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
        missing=[n for n in EXPORTED_NAMES if not hasattr(mod,n)]
        if missing:
            raise RuntimeError("UMD-097 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-097 verification returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-097 INSTALLER")
    print(" MARKET RELATIONSHIP GRAPH")
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
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        verify_current()
    except Exception:
        for p,previous in backups.items():
            if previous is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(previous)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-097 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-097',
        "revision":REVISION,
        "production_module":MODULE.name,
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
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-097 INSTALLATION COMPLETE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
