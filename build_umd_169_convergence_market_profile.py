from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_169_CONVERGENCE_MARKET_PROFILE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_169_convergence_market_profile.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_169_convergence_market_profile.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_165_convergence_surface_registry import ConvergenceSurfaceRegistry\nfrom .umd_168_convergence_context_registry import ConvergenceContextRegistry,verify_umd_168_convergence_context_registry\n\nUMD_169_BUILD_ID="UMD-169"\nUMD_169_REVISION="UMD_169_CONVERGENCE_MARKET_PROFILE_V1"\nUMD_169_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceMarketProfile:\n    canonical_market_id:str\n    change_types:Tuple[str,...]\n    ladder_hashes:Tuple[str,...]\n    partition_hashes:Tuple[str,...]\n    venue_keys:Tuple[str,...]\n    dependency_keys:Tuple[str,...]\n    dependency_roles:Tuple[str,...]\n    constraint_types:Tuple[str,...]\n    relation_types:Tuple[str,...]\n\n    def __post_init__(self):\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        for name in (\n            "change_types","ladder_hashes","partition_hashes","venue_keys",\n            "dependency_keys","dependency_roles","constraint_types","relation_types"\n        ):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if not self.change_types:\n            raise ValueError("profile requires at least one convergence change type")\n\n    @property\n    def profile_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "change_types":self.change_types,\n            "ladder_hashes":self.ladder_hashes,\n            "partition_hashes":self.partition_hashes,\n            "venue_keys":self.venue_keys,\n            "dependency_keys":self.dependency_keys,\n            "dependency_roles":self.dependency_roles,\n            "constraint_types":self.constraint_types,\n            "relation_types":self.relation_types,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceMarketProfileSet:\n    profiles:Tuple[ConvergenceMarketProfile,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"profiles",tuple(self.profiles))\n        if self.profiles!=tuple(sorted(self.profiles,key=lambda p:(p.canonical_market_id,p.profile_hash))):\n            raise ValueError("profiles must be deterministically sorted")\n        if len({p.canonical_market_id for p in self.profiles})!=len(self.profiles):\n            raise ValueError("canonical market profiles must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_169_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-169")\n        required={p.profile_hash for p in self.profiles}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every market profile hash")\n\n    def get(self,market_id:str)->ConvergenceMarketProfile|None:\n        for profile in self.profiles:\n            if profile.canonical_market_id==market_id:\n                return profile\n        return None\n\n    @property\n    def profile_set_hash(self)->str:\n        return deterministic_sha256({\n            "profile_hashes":tuple(p.profile_hash for p in self.profiles),\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceMarketProfiler:\n    __slots__=("surface_registry","context_registry")\n\n    def __init__(\n        self,\n        surface_registry:ConvergenceSurfaceRegistry,\n        context_registry:ConvergenceContextRegistry,\n    ):\n        if not isinstance(surface_registry,ConvergenceSurfaceRegistry):\n            raise TypeError("surface_registry must be ConvergenceSurfaceRegistry")\n        if not isinstance(context_registry,ConvergenceContextRegistry):\n            raise TypeError("context_registry must be ConvergenceContextRegistry")\n        self.surface_registry=surface_registry\n        self.context_registry=context_registry\n\n    @staticmethod\n    def _reverse(index,market_id):\n        return tuple(sorted(key for key,markets in index.items() if market_id in markets))\n\n    def build(self,*,lineage_factory)->ConvergenceMarketProfileSet:\n        surface_markets=set(self.surface_registry.market_index)\n        context_markets=set(self.context_registry.market_index)\n        markets=tuple(sorted(surface_markets|context_markets))\n        profiles=[]\n\n        for market_id in markets:\n            surface_types=self.surface_registry.change_types_for_market(market_id)\n            context_types=self.context_registry.change_types_for_market(market_id)\n            if surface_types and context_types and surface_types!=context_types:\n                raise ValueError("surface/context convergence change types disagree")\n            change_types=surface_types or context_types\n\n            profiles.append(ConvergenceMarketProfile(\n                market_id,\n                change_types,\n                self._reverse(self.surface_registry.ladder_index,market_id),\n                self._reverse(self.surface_registry.partition_index,market_id),\n                self._reverse(self.surface_registry.venue_index,market_id),\n                self._reverse(self.context_registry.dependency_index,market_id),\n                self._reverse(self.context_registry.role_index,market_id),\n                self._reverse(self.context_registry.constraint_index,market_id),\n                self._reverse(self.context_registry.relation_index,market_id),\n            ))\n\n        profiles.sort(key=lambda p:(p.canonical_market_id,p.profile_hash))\n        lineage=lineage_factory(tuple(p.profile_hash for p in profiles))\n        return ConvergenceMarketProfileSet(tuple(profiles),lineage)\n\ndef build_umd_169_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_169_BUILD_ID,"revision":UMD_169_REVISION,\n        "schema_version":UMD_169_SCHEMA_VERSION,"upstream_builds":("UMD-165","UMD-168"),\n        "mode":"deterministic_read_only_convergence_market_profile",\n        "semantics":"canonical_structural_profile_no_score_probability_or_prediction",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_169_convergence_market_profile()->bool:\n    if verify_umd_168_convergence_context_registry() is not True:\n        return False\n    m=build_umd_169_certification_manifest()\n    return m["build_id"]=="UMD-169" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_165_convergence_surface_registry import ConvergenceSurfaceRegistry\nfrom qseries_v2.universal_market_discovery.umd_168_convergence_context_registry import ConvergenceContextRegistry\nfrom qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import *\n\nFIXED=datetime(2026,8,10,16,0,tzinfo=timezone.utc)\nL="a"*64; P="b"*64\n\ndef surface():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-165",revision="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/165",),created_at=FIXED\n    )\n    return ConvergenceSurfaceRegistry(\n        (),(),\n        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},\n        {L:("m1","m2")},{P:("m2",)},\n        {"kalshi":("m1","m2"),"polymarket":("m1",)},\n        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},\n        l\n    )\n\ndef context():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-168",revision="UMD_168_CONVERGENCE_CONTEXT_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/168",),created_at=FIXED\n    )\n    return ConvergenceContextRegistry(\n        (),(),\n        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},\n        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},\n        {"required":("m1",),"supporting":("m2",)},\n        {"implies":("m1",),"threshold_monotonic":("m2",)},\n        {"impacted":("m1",),"boundary":("m2",)},\n        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},\n        l\n    )\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-169",revision=UMD_169_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://169",),created_at=FIXED\n    )\n\nclass TestUMD169(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_169_convergence_market_profile())\n    def test_profile(self):\n        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)\n        p=s.get("m1")\n        self.assertEqual(p.change_types,("convergence-added",))\n        self.assertEqual(p.ladder_hashes,(L,))\n        self.assertEqual(p.venue_keys,("kalshi","polymarket"))\n        self.assertEqual(p.dependency_keys,("asset=bitcoin",))\n        self.assertEqual(p.constraint_types,("implies",))\n    def test_second_profile(self):\n        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)\n        p=s.get("m2")\n        self.assertEqual(p.partition_hashes,(P,))\n        self.assertEqual(p.dependency_roles,("supporting",))\n        self.assertEqual(p.relation_types,("boundary",))\n    def test_unknown(self):\n        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)\n        self.assertIsNone(s.get("missing"))\n    def test_deterministic(self):\n        profiler=ConvergenceMarketProfiler(surface(),context())\n        a=profiler.build(lineage_factory=lf); b=profiler.build(lineage_factory=lf)\n        self.assertEqual(a.profile_set_hash,b.profile_set_hash)\n    def test_bad_surface(self):\n        with self.assertRaises(TypeError): ConvergenceMarketProfiler(object(),context())\n    def test_mismatch_rejected(self):\n        c=context()\n        bad_l=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-165",revision="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1",\n            schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/bad",),created_at=FIXED\n        )\n        bad=ConvergenceSurfaceRegistry(\n            (),(),{"m1":("convergence-removed",)}, {},{}, {},{"convergence-removed":("m1",)},bad_l\n        )\n        with self.assertRaises(ValueError):\n            ConvergenceMarketProfiler(bad,c).build(lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_169_certification_manifest()\n        self.assertEqual(m["semantics"],"canonical_structural_profile_no_score_probability_or_prediction")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-169 CERTIFICATION TEST");print(" CONVERGENCE MARKET PROFILE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD169))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_169_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical convergence market profiles combine topology, venue, dependency, constraint, and relation context")\n    print("[PASS] Surface/context convergence change-type alignment certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-169 CERTIFIED")\n'
UPSTREAM_MODULE='umd_168_convergence_context_registry'
UPSTREAM_VERIFIER='verify_umd_168_convergence_context_registry'
EXPORTED_NAMES=('UMD_169_REVISION', 'ConvergenceMarketProfile', 'ConvergenceMarketProfileSet', 'ConvergenceMarketProfiler', 'build_umd_169_certification_manifest', 'verify_umd_169_convergence_market_profile')

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
    marker="# UMD-169 exports"
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
            raise RuntimeError("UMD-169 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-169 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-169 INSTALLER")
    print(" CONVERGENCE MARKET PROFILE")
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
        print("[ROLLBACK] UMD-169 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-169',
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
    print("[DONE] UMD-169 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
