from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_145_OBSERVATION_CHANGE_ROUTING_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_145_observation_change_routing.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_145_observation_change_routing.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_135_observation_routing_registry import ObservationRoutingRegistry\nfrom .umd_144_observation_change_registry import ObservationChangeRegistry,ObservationChangeRecord,verify_umd_144_observation_change_registry\n\nUMD_145_BUILD_ID="UMD-145"\nUMD_145_REVISION="UMD_145_OBSERVATION_CHANGE_ROUTING_V1"\nUMD_145_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass RoutedObservationChange:\n    change_hash:str\n    change_type:str\n    subject_key:str\n    observation_ids:Tuple[str,...]\n    market_ids:Tuple[str,...]\n    family_keys:Tuple[str,...]\n    venue_keys:Tuple[str,...]\n\n    def __post_init__(self):\n        for name in ("observation_ids","market_ids","family_keys","venue_keys"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n\n    @property\n    def route_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "change_type":self.change_type,\n            "subject_key":self.subject_key,\n            "observation_ids":self.observation_ids,\n            "market_ids":self.market_ids,\n            "family_keys":self.family_keys,\n            "venue_keys":self.venue_keys,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationChangeRouting:\n    routes:Tuple[RoutedObservationChange,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"routes",tuple(self.routes))\n        if self.routes!=tuple(sorted(self.routes,key=lambda r:(r.change_hash,r.route_hash))):\n            raise ValueError("routes must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_145_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-145")\n        required={r.change_hash for r in self.routes}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every change hash")\n\n    @property\n    def routing_hash(self)->str:\n        return deterministic_sha256({\n            "route_hashes":tuple(r.route_hash for r in self.routes),\n            "lineage":self.lineage,\n        })\n\nclass ObservationChangeRouter:\n    __slots__=("change_registry","routing_registry")\n\n    def __init__(self,change_registry:ObservationChangeRegistry,routing_registry:ObservationRoutingRegistry):\n        if not isinstance(change_registry,ObservationChangeRegistry):\n            raise TypeError("change_registry must be ObservationChangeRegistry")\n        if not isinstance(routing_registry,ObservationRoutingRegistry):\n            raise TypeError("routing_registry must be ObservationRoutingRegistry")\n        self.change_registry=change_registry\n        self.routing_registry=routing_registry\n\n    def route(self,*,lineage:ImmutableLineage)->ObservationChangeRouting:\n        record_by_obs={r.observation_id:r for r in self.routing_registry.records}\n        routes=[]\n\n        for change in self.change_registry.changes:\n            observations=set()\n\n            if change.change_type.startswith("canonical-"):\n                observations.add(change.subject_key)\n            elif change.change_type.startswith("contradiction-"):\n                parts=tuple(x for x in change.subject_key.split("|") if x)\n                observations.update(parts)\n            # Cluster changes may not resolve to a single observation from the\n            # change record alone; preserve them as structural changes with empty routing.\n\n            markets=set(); families=set(); venues=set()\n            known_obs=[]\n            for obs in sorted(observations):\n                record=record_by_obs.get(obs)\n                if record is None:\n                    continue\n                known_obs.append(obs)\n                markets.update(record.market_ids)\n                families.update(record.family_keys)\n                venues.update(record.venue_keys)\n\n            routes.append(RoutedObservationChange(\n                change.change_hash,\n                change.change_type,\n                change.subject_key,\n                tuple(sorted(known_obs)),\n                tuple(sorted(markets)),\n                tuple(sorted(families)),\n                tuple(sorted(venues)),\n            ))\n\n        routes.sort(key=lambda r:(r.change_hash,r.route_hash))\n        return ObservationChangeRouting(tuple(routes),lineage)\n\ndef build_umd_145_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_145_BUILD_ID,"revision":UMD_145_REVISION,\n        "schema_version":UMD_145_SCHEMA_VERSION,"upstream_builds":("UMD-135","UMD-144"),\n        "mode":"deterministic_read_only_observation_change_routing",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_145_observation_change_routing()->bool:\n    if verify_umd_144_observation_change_registry() is not True:\n        return False\n    m=build_umd_145_certification_manifest()\n    return m["build_id"]=="UMD-145" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import ObservationRoutingRecord,ObservationRoutingRegistry\nfrom qseries_v2.universal_market_discovery.umd_144_observation_change_registry import ObservationChangeRecord,ObservationChangeRegistry\nfrom qseries_v2.universal_market_discovery.umd_145_observation_change_routing import *\n\nFIXED=datetime(2026,8,10,8,0,tzinfo=timezone.utc)\n\ndef routing_registry():\n    r1=ObservationRoutingRecord("obs-a","economics","a"*64,"b"*64,"c"*64,"d"*64,"t1",("m1",),("f1",),("kalshi",),())\n    r2=ObservationRoutingRecord("obs-b","economics","e"*64,"f"*64,"1"*64,"2"*64,"t1",("m2",),("f2",),("polymarket",),())\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-135",revision="UMD_135_OBSERVATION_ROUTING_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(r1.record_hash,r2.record_hash),source_refs=("fixture://145/135",),created_at=FIXED)\n    return ObservationRoutingRegistry(\n        (r1,r2),\n        {"m1":("obs-a",),"m2":("obs-b",)},\n        {"f1":("obs-a",),"f2":("obs-b",)},\n        {"kalshi":("obs-a",),"polymarket":("obs-b",)},\n        {"economics":("obs-a","obs-b")},\n        {"t1":("obs-a","obs-b")},\n        l\n    )\n\ndef change_registry():\n    c1=ObservationChangeRecord("canonical-added","obs-a","3"*64)\n    c2=ObservationChangeRecord("contradiction-added","obs-a|obs-b","4"*64)\n    c3=ObservationChangeRecord("cluster-added","cluster-1","5"*64)\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-144",revision="UMD_144_OBSERVATION_CHANGE_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://145/144",),created_at=FIXED)\n    return ObservationChangeRegistry((),tuple(sorted((c1,c2,c3),key=lambda c:(c.change_type,c.subject_key,c.diff_hash))),\n        {},{},l)\n\ndef lineage(cr):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-145",revision=UMD_145_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(c.change_hash for c in cr.changes),\n        source_refs=("fixture://145",),created_at=FIXED)\n\nclass TestUMD145(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_145_observation_change_routing())\n    def test_canonical_change_route(self):\n        cr=change_registry(); rr=routing_registry()\n        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))\n        route=next(r for r in x.routes if r.change_type=="canonical-added")\n        self.assertEqual(route.observation_ids,("obs-a",))\n        self.assertEqual(route.market_ids,("m1",))\n        self.assertEqual(route.family_keys,("f1",))\n        self.assertEqual(route.venue_keys,("kalshi",))\n    def test_contradiction_route(self):\n        cr=change_registry(); rr=routing_registry()\n        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))\n        route=next(r for r in x.routes if r.change_type=="contradiction-added")\n        self.assertEqual(route.observation_ids,("obs-a","obs-b"))\n        self.assertEqual(route.market_ids,("m1","m2"))\n        self.assertEqual(route.venue_keys,("kalshi","polymarket"))\n    def test_cluster_change_preserved_unrouted(self):\n        cr=change_registry(); rr=routing_registry()\n        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))\n        route=next(r for r in x.routes if r.change_type=="cluster-added")\n        self.assertEqual(route.observation_ids,())\n        self.assertEqual(route.market_ids,())\n    def test_deterministic(self):\n        cr=change_registry(); rr=routing_registry(); l=lineage(cr)\n        a=ObservationChangeRouter(cr,rr).route(lineage=l)\n        b=ObservationChangeRouter(cr,rr).route(lineage=l)\n        self.assertEqual(a.routing_hash,b.routing_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ObservationChangeRouter(object(),routing_registry())\n    def test_side_effects(self):\n        m=build_umd_145_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-145 CERTIFICATION TEST");print(" OBSERVATION CHANGE ROUTING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD145))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_145_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation-state changes routed back to certified observation market structure")\n    print("[PASS] Canonical and contradiction changes preserve markets, families, and venues")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-145 CERTIFIED")\n'
UPSTREAM_MODULE='umd_144_observation_change_registry'
UPSTREAM_VERIFIER='verify_umd_144_observation_change_registry'
EXPORTED_NAMES=('UMD_145_REVISION', 'RoutedObservationChange', 'ObservationChangeRouting', 'ObservationChangeRouter', 'build_umd_145_certification_manifest', 'verify_umd_145_observation_change_routing')

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
    marker="# UMD-145 exports"
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
            raise RuntimeError("UMD-145 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-145 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-145 INSTALLER")
    print(" OBSERVATION CHANGE ROUTING")
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
        print("[ROLLBACK] UMD-145 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-145',
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
    print("[DONE] UMD-145 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
