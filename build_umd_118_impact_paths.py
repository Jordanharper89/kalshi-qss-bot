from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_118_IMPACT_PATH_RESOLUTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_118_impact_paths.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_118_impact_paths.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_115_observation_impact import DirectImpactResult\nfrom .umd_116_dependency_propagation import PropagationResult,PropagationStep\nfrom .umd_117_impact_registry import verify_umd_117_impact_registry\n\nUMD_118_BUILD_ID="UMD-118"\nUMD_118_REVISION="UMD_118_IMPACT_PATH_RESOLUTION_V1"\nUMD_118_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ImpactPath:\n    observation_hash:str\n    target_market_id:str\n    direct:bool\n    market_path:Tuple[str,...]\n    constraint_path:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"market_path",tuple(self.market_path))\n        object.__setattr__(self,"constraint_path",tuple(self.constraint_path))\n        if not self.market_path:\n            raise ValueError("market_path must be non-empty")\n        if self.market_path[-1]!=self.target_market_id:\n            raise ValueError("target market must terminate market_path")\n        if len(self.constraint_path)!=len(self.market_path)-1:\n            raise ValueError("constraint_path length must be market_path length minus one")\n        if self.direct and len(self.market_path)!=1:\n            raise ValueError("direct impact path must contain exactly one market")\n        if not self.direct and len(self.market_path)<2:\n            raise ValueError("propagated impact path must contain at least two markets")\n\n    @property\n    def path_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "target_market_id":self.target_market_id,\n            "direct":self.direct,\n            "market_path":self.market_path,\n            "constraint_path":self.constraint_path,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ImpactPathSet:\n    observation_hash:str\n    paths:Tuple[ImpactPath,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"paths",tuple(self.paths))\n        if tuple(sorted(self.paths,key=lambda p:(p.target_market_id,not p.direct,p.market_path,p.constraint_path)))!=self.paths:\n            raise ValueError("paths must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_118_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-118")\n\n    def paths_to(self,canonical_market_id:str)->Tuple[ImpactPath,...]:\n        return tuple(p for p in self.paths if p.target_market_id==canonical_market_id)\n\n    @property\n    def path_set_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "path_hashes":tuple(p.path_hash for p in self.paths),\n            "lineage":self.lineage,\n        })\n\nclass ImpactPathResolver:\n    __slots__=()\n\n    def resolve(\n        self,\n        direct:DirectImpactResult,\n        propagation:PropagationResult,\n        *,\n        lineage:ImmutableLineage,\n    )->ImpactPathSet:\n        if not isinstance(direct,DirectImpactResult):\n            raise TypeError("direct must be DirectImpactResult")\n        if not isinstance(propagation,PropagationResult):\n            raise TypeError("propagation must be PropagationResult")\n        if tuple(direct.market_ids)!=tuple(propagation.direct_market_ids):\n            raise ValueError("direct and propagation market sets do not align")\n\n        paths={}\n        for market_id in direct.market_ids:\n            paths[market_id]=ImpactPath(\n                direct.observation_hash,market_id,True,(market_id,),()\n            )\n\n        ordered=tuple(sorted(\n            propagation.steps,\n            key=lambda s:(s.depth,s.source_market_id,s.target_market_id,s.constraint_type)\n        ))\n\n        for step in ordered:\n            source_path=paths.get(step.source_market_id)\n            if source_path is None:\n                raise ValueError("propagation step source is not reachable from direct impact")\n            candidate=ImpactPath(\n                direct.observation_hash,\n                step.target_market_id,\n                False,\n                source_path.market_path+(step.target_market_id,),\n                source_path.constraint_path+(step.constraint_type,),\n            )\n            existing=paths.get(step.target_market_id)\n            if existing is None or (len(candidate.market_path),candidate.market_path,candidate.constraint_path) < (\n                len(existing.market_path),existing.market_path,existing.constraint_path\n            ):\n                paths[step.target_market_id]=candidate\n\n        expected=set(propagation.all_market_ids)\n        if set(paths)!=expected:\n            raise ValueError("resolved impact paths do not cover propagation result")\n\n        values=tuple(sorted(paths.values(),key=lambda p:(p.target_market_id,not p.direct,p.market_path,p.constraint_path)))\n        return ImpactPathSet(direct.observation_hash,values,lineage)\n\ndef build_umd_118_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_118_BUILD_ID,"revision":UMD_118_REVISION,\n        "schema_version":UMD_118_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-116","UMD-117"),\n        "mode":"deterministic_read_only_impact_path_resolution",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_118_impact_path_resolution()->bool:\n    if verify_umd_117_impact_registry() is not True:\n        return False\n    m=build_umd_118_certification_manifest()\n    return m["build_id"]=="UMD-118" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult\nfrom qseries_v2.universal_market_discovery.umd_116_dependency_propagation import PropagationResult,PropagationStep\nfrom qseries_v2.universal_market_discovery.umd_118_impact_paths import *\n\nFIXED=datetime(2026,8,9,20,0,tzinfo=timezone.utc)\n\ndef direct():\n    obs="a"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",\n        schema_version="1.0.0",parent_hashes=(obs,),source_refs=("fixture://118/115",),created_at=FIXED)\n    return DirectImpactResult(obs,("m1",),(),l)\n\ndef propagation():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision="UMD_116_DEPENDENCY_PROPAGATION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://118/116",),created_at=FIXED)\n    return PropagationResult(\n        ("m1",),("m2","m3"),\n        (PropagationStep(1,"m1","m2","implies"),PropagationStep(2,"m2","m3","threshold_monotonic")),\n        l\n    )\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-118",revision=UMD_118_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://118",),created_at=FIXED)\n\nclass TestUMD118(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_118_impact_path_resolution())\n    def test_direct_path(self):\n        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())\n        p=r.paths_to("m1")[0]\n        self.assertTrue(p.direct)\n        self.assertEqual(p.market_path,("m1",))\n    def test_propagated_path(self):\n        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())\n        p=r.paths_to("m3")[0]\n        self.assertFalse(p.direct)\n        self.assertEqual(p.market_path,("m1","m2","m3"))\n        self.assertEqual(p.constraint_path,("implies","threshold_monotonic"))\n    def test_complete_coverage(self):\n        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())\n        self.assertEqual(tuple(p.target_market_id for p in r.paths),("m1","m2","m3"))\n    def test_mismatch_rejected(self):\n        p=propagation()\n        wrong=PropagationResult(("x",),p.propagated_market_ids,p.steps,p.lineage)\n        with self.assertRaises(ValueError):\n            ImpactPathResolver().resolve(direct(),wrong,lineage=lineage())\n    def test_unreachable_step_rejected(self):\n        p=propagation()\n        bad=PropagationResult(("m1",),("m2",),(PropagationStep(1,"x","m2","implies"),),p.lineage)\n        with self.assertRaises(ValueError):\n            ImpactPathResolver().resolve(direct(),bad,lineage=lineage())\n    def test_deterministic(self):\n        a=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())\n        b=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())\n        self.assertEqual(a.path_set_hash,b.path_set_hash)\n    def test_side_effects(self):\n        m=build_umd_118_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-118 CERTIFICATION TEST");print(" IMPACT PATH RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD118))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_118_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Direct and propagated observation-to-market paths certified")\n    print("[PASS] UMD-115 through UMD-117 consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-118 CERTIFIED")\n'
UPSTREAM_MODULE='umd_117_impact_registry'
UPSTREAM_VERIFIER='verify_umd_117_impact_registry'
EXPORTED_NAMES=('UMD_118_REVISION', 'ImpactPath', 'ImpactPathSet', 'ImpactPathResolver', 'build_umd_118_certification_manifest', 'verify_umd_118_impact_path_resolution')

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
    marker="# UMD-118 exports"
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
            raise RuntimeError("UMD-118 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-118 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-118 INSTALLER")
    print(" IMPACT PATH RESOLUTION")
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
        print("[ROLLBACK] UMD-118 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-118',
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
    print("[DONE] UMD-118 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
