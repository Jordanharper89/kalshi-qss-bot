from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_146_OBSERVATION_CHANGE_IMPACT_SURFACE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_146_observation_change_impact_surface.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_146_observation_change_impact_surface.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_145_observation_change_routing import ObservationChangeRouting,verify_umd_145_observation_change_routing\n\nUMD_146_BUILD_ID="UMD-146"\nUMD_146_REVISION="UMD_146_OBSERVATION_CHANGE_IMPACT_SURFACE_V1"\nUMD_146_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationChangeImpactSurface:\n    routing_hash:str\n    market_to_changes:Mapping[str,Tuple[str,...]]\n    family_to_changes:Mapping[str,Tuple[str,...]]\n    venue_to_changes:Mapping[str,Tuple[str,...]]\n    change_to_markets:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in ("market_to_changes","family_to_changes","venue_to_changes","change_to_markets"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_146_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-146")\n        if self.routing_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include change routing hash")\n\n    def changes_for_market(self,key:str)->Tuple[str,...]:\n        return self.market_to_changes.get(key,())\n    def changes_for_family(self,key:str)->Tuple[str,...]:\n        return self.family_to_changes.get(key,())\n    def changes_for_venue(self,key:str)->Tuple[str,...]:\n        return self.venue_to_changes.get(key,())\n    def markets_for_change(self,change_hash:str)->Tuple[str,...]:\n        return self.change_to_markets.get(change_hash,())\n\n    @property\n    def surface_hash(self)->str:\n        return deterministic_sha256({\n            "routing_hash":self.routing_hash,\n            "market_to_changes":self.market_to_changes,\n            "family_to_changes":self.family_to_changes,\n            "venue_to_changes":self.venue_to_changes,\n            "change_to_markets":self.change_to_markets,\n            "lineage":self.lineage,\n        })\n\nclass ObservationChangeImpactSurfaceBuilder:\n    __slots__=()\n\n    def build(self,routing:ObservationChangeRouting,*,lineage:ImmutableLineage)->ObservationChangeImpactSurface:\n        if not isinstance(routing,ObservationChangeRouting):\n            raise TypeError("routing must be ObservationChangeRouting")\n        market={}; family={}; venue={}; change_to_markets={}\n\n        for route in routing.routes:\n            change_to_markets[route.change_hash]=route.market_ids\n            for key in route.market_ids:\n                market.setdefault(key,[]).append(route.change_hash)\n            for key in route.family_keys:\n                family.setdefault(key,[]).append(route.change_hash)\n            for key in route.venue_keys:\n                venue.setdefault(key,[]).append(route.change_hash)\n\n        for index in (market,family,venue):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        return ObservationChangeImpactSurface(\n            routing.routing_hash,market,family,venue,change_to_markets,lineage\n        )\n\ndef build_umd_146_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_146_BUILD_ID,"revision":UMD_146_REVISION,\n        "schema_version":UMD_146_SCHEMA_VERSION,"upstream_builds":("UMD-145",),\n        "mode":"deterministic_read_only_observation_change_impact_surface",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_146_observation_change_impact_surface()->bool:\n    if verify_umd_145_observation_change_routing() is not True:\n        return False\n    m=build_umd_146_certification_manifest()\n    return m["build_id"]=="UMD-146" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_145_observation_change_routing import RoutedObservationChange,ObservationChangeRouting\nfrom qseries_v2.universal_market_discovery.umd_146_observation_change_impact_surface import *\n\nFIXED=datetime(2026,8,10,8,10,tzinfo=timezone.utc)\n\ndef routing():\n    a=RoutedObservationChange("a"*64,"canonical-added","obs-a",("obs-a",),("m1",),("f1",),("kalshi",))\n    b=RoutedObservationChange("b"*64,"contradiction-added","obs-a|obs-b",("obs-a","obs-b"),("m1","m2"),("f1","f2"),("kalshi","polymarket"))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-145",revision="UMD_145_OBSERVATION_CHANGE_ROUTING_V1",\n        schema_version="1.0.0",parent_hashes=(a.change_hash,b.change_hash),source_refs=("fixture://146/145",),created_at=FIXED)\n    return ObservationChangeRouting(tuple(sorted((a,b),key=lambda r:(r.change_hash,r.route_hash))),l)\n\ndef lineage(r):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-146",revision=UMD_146_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.routing_hash,),source_refs=("fixture://146",),created_at=FIXED)\n\nclass TestUMD146(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_146_observation_change_impact_surface())\n    def test_market_query(self):\n        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))\n        self.assertEqual(s.changes_for_market("m2"),("b"*64,))\n    def test_family_query(self):\n        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))\n        self.assertEqual(s.changes_for_family("f1"),("a"*64,"b"*64))\n    def test_venue_query(self):\n        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))\n        self.assertEqual(s.changes_for_venue("polymarket"),("b"*64,))\n    def test_reverse_query(self):\n        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))\n        self.assertEqual(s.markets_for_change("b"*64),("m1","m2"))\n    def test_unknown(self):\n        r=routing(); s=ObservationChangeImpactSurfaceBuilder().build(r,lineage=lineage(r))\n        self.assertEqual(s.changes_for_market("missing"),())\n    def test_deterministic(self):\n        r=routing(); l=lineage(r)\n        a=ObservationChangeImpactSurfaceBuilder().build(r,lineage=l)\n        b=ObservationChangeImpactSurfaceBuilder().build(r,lineage=l)\n        self.assertEqual(a.surface_hash,b.surface_hash)\n    def test_side_effects(self):\n        m=build_umd_146_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-146 CERTIFICATION TEST");print(" OBSERVATION CHANGE IMPACT SURFACE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD146))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_146_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation changes projected across canonical markets, families, and venues")\n    print("[PASS] Forward and reverse structural change-impact queries certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-146 CERTIFIED")\n'
UPSTREAM_MODULE='umd_145_observation_change_routing'
UPSTREAM_VERIFIER='verify_umd_145_observation_change_routing'
EXPORTED_NAMES=('UMD_146_REVISION', 'ObservationChangeImpactSurface', 'ObservationChangeImpactSurfaceBuilder', 'build_umd_146_certification_manifest', 'verify_umd_146_observation_change_impact_surface')

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
    marker="# UMD-146 exports"
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
            raise RuntimeError("UMD-146 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-146 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-146 INSTALLER")
    print(" OBSERVATION CHANGE IMPACT SURFACE")
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
        print("[ROLLBACK] UMD-146 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-146',
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
    print("[DONE] UMD-146 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
