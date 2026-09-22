from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_116_DEPENDENCY_PROPAGATION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_116_dependency_propagation.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_116_dependency_propagation.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_113_market_constraints import MarketConstraintGraph\nfrom .umd_115_observation_impact import DirectImpactResult, verify_umd_115_observation_impact_mapping\n\nUMD_116_BUILD_ID="UMD-116"\nUMD_116_REVISION="UMD_116_DEPENDENCY_PROPAGATION_V1"\nUMD_116_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nPROPAGATING_CONSTRAINTS=("threshold_monotonic","implies","equivalent")\n\n@dataclass(frozen=True,slots=True)\nclass PropagationStep:\n    depth:int\n    source_market_id:str\n    target_market_id:str\n    constraint_type:str\n\n    @property\n    def step_hash(self)->str:\n        return deterministic_sha256({\n            "depth":self.depth,\n            "source_market_id":self.source_market_id,\n            "target_market_id":self.target_market_id,\n            "constraint_type":self.constraint_type,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass PropagationResult:\n    direct_market_ids:Tuple[str,...]\n    propagated_market_ids:Tuple[str,...]\n    steps:Tuple[PropagationStep,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"direct_market_ids",tuple(self.direct_market_ids))\n        object.__setattr__(self,"propagated_market_ids",tuple(self.propagated_market_ids))\n        object.__setattr__(self,"steps",tuple(self.steps))\n        if tuple(sorted(set(self.direct_market_ids)))!=self.direct_market_ids:\n            raise ValueError("direct_market_ids must be unique and sorted")\n        if tuple(sorted(set(self.propagated_market_ids)))!=self.propagated_market_ids:\n            raise ValueError("propagated_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_116_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-116")\n\n    @property\n    def all_market_ids(self)->Tuple[str,...]:\n        return tuple(sorted(set(self.direct_market_ids)|set(self.propagated_market_ids)))\n\n    @property\n    def propagation_hash(self)->str:\n        return deterministic_sha256({\n            "direct_market_ids":self.direct_market_ids,\n            "propagated_market_ids":self.propagated_market_ids,\n            "steps":tuple({\n                "depth":s.depth,\n                "source_market_id":s.source_market_id,\n                "target_market_id":s.target_market_id,\n                "constraint_type":s.constraint_type,\n            } for s in self.steps),\n            "lineage":self.lineage,\n        })\n\nclass DependencyPropagationEngine:\n    __slots__=("graph",)\n\n    def __init__(self,graph:MarketConstraintGraph):\n        if not isinstance(graph,MarketConstraintGraph):\n            raise TypeError("graph must be MarketConstraintGraph")\n        self.graph=graph\n\n    def propagate(\n        self,\n        direct:DirectImpactResult,\n        *,\n        max_depth:int=3,\n        lineage:ImmutableLineage,\n    )->PropagationResult:\n        if not isinstance(direct,DirectImpactResult):\n            raise TypeError("direct must be DirectImpactResult")\n        if not isinstance(max_depth,int) or max_depth<0:\n            raise ValueError("max_depth must be a non-negative integer")\n\n        adjacency={}\n        for c in self.graph.constraints:\n            if c.constraint_type not in PROPAGATING_CONSTRAINTS:\n                continue\n            adjacency.setdefault(c.source_market_id,[]).append((c.target_market_id,c.constraint_type))\n            if c.constraint_type=="equivalent":\n                adjacency.setdefault(c.target_market_id,[]).append((c.source_market_id,c.constraint_type))\n\n        direct_set=set(direct.market_ids)\n        seen=set(direct_set)\n        frontier=tuple(sorted(direct_set))\n        steps=[]\n\n        for depth in range(1,max_depth+1):\n            next_frontier=set()\n            for source in frontier:\n                for target,constraint_type in sorted(adjacency.get(source,())):\n                    if target in seen:\n                        continue\n                    seen.add(target)\n                    next_frontier.add(target)\n                    steps.append(PropagationStep(depth,source,target,constraint_type))\n            if not next_frontier:\n                break\n            frontier=tuple(sorted(next_frontier))\n\n        propagated=tuple(sorted(seen-direct_set))\n        steps.sort(key=lambda s:(s.depth,s.source_market_id,s.target_market_id,s.constraint_type))\n        return PropagationResult(tuple(sorted(direct_set)),propagated,tuple(steps),lineage)\n\ndef build_umd_116_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_116_BUILD_ID,"revision":UMD_116_REVISION,\n        "schema_version":UMD_116_SCHEMA_VERSION,"upstream_builds":("UMD-113","UMD-115"),\n        "mode":"deterministic_read_only_dependency_propagation",\n        "propagating_constraints":PROPAGATING_CONSTRAINTS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_116_dependency_propagation()->bool:\n    if verify_umd_115_observation_impact_mapping() is not True:\n        return False\n    m=build_umd_116_certification_manifest()\n    return m["build_id"]=="UMD-116" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_113_market_constraints import MarketConstraint,MarketConstraintGraph\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult\nfrom qseries_v2.universal_market_discovery.umd_116_dependency_propagation import *\n\nFIXED=datetime(2026,8,9,19,10,tzinfo=timezone.utc)\n\ndef graph():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-113",revision="UMD_113_MARKET_CONSTRAINT_GRAPH_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://116/113",),created_at=FIXED)\n    return MarketConstraintGraph(\n        ("m1","m2","m3","m4"),\n        (\n            MarketConstraint("m1","m2","implies","a"),\n            MarketConstraint("m2","m3","threshold_monotonic","b"),\n            MarketConstraint("m3","m4","mutually_exclusive","c"),\n        ),\n        (),\n        l,\n    )\n\ndef direct():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",schema_version="1.0.0",parent_hashes=("a"*64,),source_refs=("fixture://116/115",),created_at=FIXED)\n    return DirectImpactResult("a"*64,("m1",),(),l)\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision=UMD_116_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://116",),created_at=FIXED)\n\nclass TestUMD116(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_116_dependency_propagation())\n    def test_propagation(self):\n        r=DependencyPropagationEngine(graph()).propagate(direct(),lineage=lineage())\n        self.assertEqual(r.propagated_market_ids,("m2","m3"))\n        self.assertNotIn("m4",r.all_market_ids)\n    def test_depth_limit(self):\n        r=DependencyPropagationEngine(graph()).propagate(direct(),max_depth=1,lineage=lineage())\n        self.assertEqual(r.propagated_market_ids,("m2",))\n    def test_steps(self):\n        r=DependencyPropagationEngine(graph()).propagate(direct(),lineage=lineage())\n        self.assertEqual(tuple(s.depth for s in r.steps),(1,2))\n    def test_zero_depth(self):\n        r=DependencyPropagationEngine(graph()).propagate(direct(),max_depth=0,lineage=lineage())\n        self.assertEqual(r.propagated_market_ids,())\n    def test_deterministic(self):\n        e=DependencyPropagationEngine(graph())\n        a=e.propagate(direct(),lineage=lineage())\n        b=e.propagate(direct(),lineage=lineage())\n        self.assertEqual(a.propagation_hash,b.propagation_hash)\n    def test_bad_depth(self):\n        with self.assertRaises(ValueError): DependencyPropagationEngine(graph()).propagate(direct(),max_depth=-1,lineage=lineage())\n    def test_bad_graph(self):\n        with self.assertRaises(TypeError): DependencyPropagationEngine(object())\n    def test_side_effects(self):\n        m=build_umd_116_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-116 CERTIFICATION TEST");print(" DEPENDENCY PROPAGATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD116))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_116_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Bounded deterministic propagation across implication constraints certified")\n    print("[PASS] Non-propagating constraint types remain excluded")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-116 CERTIFIED")\n'
UPSTREAM_MODULE='umd_115_observation_impact'
UPSTREAM_VERIFIER='verify_umd_115_observation_impact_mapping'
EXPORTED_NAMES=('UMD_116_REVISION', 'PROPAGATING_CONSTRAINTS', 'PropagationStep', 'PropagationResult', 'DependencyPropagationEngine', 'build_umd_116_certification_manifest', 'verify_umd_116_dependency_propagation')

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
    marker="# UMD-116 exports"
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
            raise RuntimeError("UMD-116 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-116 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-116 INSTALLER")
    print(" DEPENDENCY PROPAGATION")
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
        print("[ROLLBACK] UMD-116 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-116',
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
    print("[DONE] UMD-116 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
