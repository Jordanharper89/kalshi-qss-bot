from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_157_CHANGE_CO_OCCURRENCE_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_157_change_co_occurrence_model.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_157_change_co_occurrence_model.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom itertools import combinations\nfrom types import MappingProxyType\nfrom typing import Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_156_change_market_context_registry import ChangeMarketContextRegistry,verify_umd_156_change_market_context_registry\n\nUMD_157_BUILD_ID="UMD-157"\nUMD_157_REVISION="UMD_157_CHANGE_CO_OCCURRENCE_MODEL_V1"\nUMD_157_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\nRELATION_ORDER=("impacted","boundary","family-neighbor","topology-neighbor")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeCoOccurrence:\n    canonical_market_id:str\n    change_hashes:Tuple[str,...]\n    change_pairs:Tuple[Tuple[str,str],...]\n    relation_types:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"change_hashes",tuple(self.change_hashes))\n        object.__setattr__(self,"change_pairs",tuple(self.change_pairs))\n        object.__setattr__(self,"relation_types",tuple(self.relation_types))\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        if self.change_hashes!=tuple(sorted(set(self.change_hashes))):\n            raise ValueError("change_hashes must be unique and sorted")\n        if len(self.change_hashes)<2:\n            raise ValueError("co-occurrence requires at least two distinct changes")\n        expected_pairs=tuple(combinations(self.change_hashes,2))\n        if self.change_pairs!=expected_pairs:\n            raise ValueError("change_pairs must equal deterministic pair combinations")\n        expected_relations=tuple(r for r in RELATION_ORDER if r in set(self.relation_types))\n        if self.relation_types!=expected_relations:\n            raise ValueError("relation_types must be unique and canonically ordered")\n\n    @property\n    def occurrence_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "change_hashes":self.change_hashes,\n            "change_pairs":self.change_pairs,\n            "relation_types":self.relation_types,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeCoOccurrenceModel:\n    occurrences:Tuple[ChangeCoOccurrence,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    change_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"occurrences",tuple(self.occurrences))\n        object.__setattr__(self,"market_index",_freeze(self.market_index))\n        object.__setattr__(self,"change_index",_freeze(self.change_index))\n        if self.occurrences!=tuple(sorted(\n            self.occurrences,key=lambda o:(o.canonical_market_id,o.occurrence_hash)\n        )):\n            raise ValueError("occurrences must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_157_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-157")\n        required={o.occurrence_hash for o in self.occurrences}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every occurrence hash")\n\n    def changes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def markets_for_change(self,change_hash:str)->Tuple[str,...]:\n        return self.change_index.get(change_hash,())\n\n    @property\n    def model_hash(self)->str:\n        return deterministic_sha256({\n            "occurrence_hashes":tuple(o.occurrence_hash for o in self.occurrences),\n            "market_index":self.market_index,\n            "change_index":self.change_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeCoOccurrenceBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        context_registry:ChangeMarketContextRegistry,\n        *,\n        lineage_factory,\n    )->ChangeCoOccurrenceModel:\n        if not isinstance(context_registry,ChangeMarketContextRegistry):\n            raise TypeError("context_registry must be ChangeMarketContextRegistry")\n\n        occurrences=[]\n        market_index={}\n        change_index={}\n\n        for market_id,changes in sorted(context_registry.market_index.items()):\n            change_hashes=tuple(sorted(set(changes)))\n            if len(change_hashes)<2:\n                continue\n\n            relations=[]\n            if market_id in context_registry.impacted_index:\n                relations.append("impacted")\n            if market_id in context_registry.boundary_index:\n                relations.append("boundary")\n            if market_id in context_registry.family_neighbor_index:\n                relations.append("family-neighbor")\n            if market_id in context_registry.topology_neighbor_index:\n                relations.append("topology-neighbor")\n\n            occurrence=ChangeCoOccurrence(\n                market_id,\n                change_hashes,\n                tuple(combinations(change_hashes,2)),\n                tuple(relations),\n            )\n            occurrences.append(occurrence)\n            market_index[market_id]=change_hashes\n            for change_hash in change_hashes:\n                change_index.setdefault(change_hash,[]).append(market_id)\n\n        occurrences.sort(key=lambda o:(o.canonical_market_id,o.occurrence_hash))\n        for key,values in change_index.items():\n            change_index[key]=tuple(sorted(set(values)))\n\n        # The model\'s direct parents are the immutable co-occurrence artifacts.\n        lineage=lineage_factory(tuple(o.occurrence_hash for o in occurrences))\n        return ChangeCoOccurrenceModel(\n            tuple(occurrences),market_index,change_index,lineage\n        )\n\ndef build_umd_157_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_157_BUILD_ID,"revision":UMD_157_REVISION,\n        "schema_version":UMD_157_SCHEMA_VERSION,"upstream_builds":("UMD-156",),\n        "mode":"deterministic_read_only_change_co_occurrence_model",\n        "semantics":"shared_structural_context_only_no_importance_or_probability",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_157_change_co_occurrence_model()->bool:\n    if verify_umd_156_change_market_context_registry() is not True:\n        return False\n    m=build_umd_157_certification_manifest()\n    return m["build_id"]=="UMD-157" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood\nfrom qseries_v2.universal_market_discovery.umd_156_change_market_context_registry import ChangeMarketContextRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_157_change_co_occurrence_model import *\n\nFIXED=datetime(2026,8,10,12,0,tzinfo=timezone.utc)\n\ndef neighborhood(change,impacted=(),boundary=(),family=(),topology=()):\n    all_ids=tuple(sorted(set(impacted+boundary+family+topology)))\n    relation={\n        "impacted":tuple(impacted),\n        "boundary":tuple(boundary),\n        "family-neighbor":tuple(family),\n        "topology-neighbor":tuple(topology),\n    }\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-155",revision="UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_V1",\n        schema_version="1.0.0",parent_hashes=(change,),\n        source_refs=("fixture://157/155",),created_at=FIXED\n    )\n    return ChangeStructuralNeighborhood(\n        change,tuple(impacted),tuple(boundary),tuple(family),tuple(topology),\n        all_ids,relation,l\n    )\n\ndef context_registry():\n    c1="1"*64; c2="2"*64; c3="3"*64\n    n1=neighborhood(c1,impacted=("m1",),topology=("m2",))\n    n2=neighborhood(c2,boundary=("m1",),topology=("m2",))\n    n3=neighborhood(c3,impacted=("m3",))\n    def lf(parents):\n        return ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-156",revision="UMD_156_CHANGE_MARKET_CONTEXT_REGISTRY_V1",\n            schema_version="1.0.0",parent_hashes=parents,\n            source_refs=("fixture://157/156",),created_at=FIXED\n        )\n    return ChangeMarketContextRegistryBuilder().build((n1,n2,n3),lineage_factory=lf),c1,c2,c3\n\ndef lf157(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-157",revision=UMD_157_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://157",),created_at=FIXED\n    )\n\nclass TestUMD157(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_157_change_co_occurrence_model())\n    def test_co_occurrence(self):\n        r,c1,c2,_=context_registry()\n        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        self.assertEqual(model.changes_for_market("m1"),(c1,c2))\n        self.assertEqual(model.changes_for_market("m2"),(c1,c2))\n        self.assertEqual(model.changes_for_market("m3"),())\n    def test_pair_generation(self):\n        r,c1,c2,_=context_registry()\n        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        o=next(x for x in model.occurrences if x.canonical_market_id=="m1")\n        self.assertEqual(o.change_pairs,((c1,c2),))\n    def test_relation_union(self):\n        r,_,_,_=context_registry()\n        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        o=next(x for x in model.occurrences if x.canonical_market_id=="m1")\n        self.assertEqual(o.relation_types,("impacted","boundary"))\n    def test_change_reverse_query(self):\n        r,c1,_,_=context_registry()\n        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        self.assertEqual(model.markets_for_change(c1),("m1","m2"))\n    def test_single_change_excluded(self):\n        r,_,_,c3=context_registry()\n        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        self.assertEqual(model.markets_for_change(c3),())\n    def test_deterministic(self):\n        r,_,_,_=context_registry()\n        a=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        b=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)\n        self.assertEqual(a.model_hash,b.model_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ChangeCoOccurrenceBuilder().build(object(),lineage_factory=lf157)\n    def test_side_effects(self):\n        m=build_umd_157_certification_manifest()\n        self.assertEqual(m["semantics"],"shared_structural_context_only_no_importance_or_probability")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-157 CERTIFICATION TEST");print(" CHANGE CO-OCCURRENCE MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD157))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_157_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Multiple certified changes sharing canonical market context identified deterministically")\n    print("[PASS] Co-occurrence remains structural and introduces no importance or probability score")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-157 CERTIFIED")\n'
UPSTREAM_MODULE='umd_156_change_market_context_registry'
UPSTREAM_VERIFIER='verify_umd_156_change_market_context_registry'
EXPORTED_NAMES=('UMD_157_REVISION', 'RELATION_ORDER', 'ChangeCoOccurrence', 'ChangeCoOccurrenceModel', 'ChangeCoOccurrenceBuilder', 'build_umd_157_certification_manifest', 'verify_umd_157_change_co_occurrence_model')

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
    marker="# UMD-157 exports"
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
            raise RuntimeError("UMD-157 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-157 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-157 INSTALLER")
    print(" CHANGE CO OCCURRENCE MODEL")
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
        print("[ROLLBACK] UMD-157 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-157',
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
    print("[DONE] UMD-157 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
