from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_134_OBSERVATION_TIMELINE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_134_observation_timeline.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_134_observation_timeline.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom types import MappingProxyType\nfrom typing import Iterable,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_132_observation_routing import ObservationRoute\nfrom .umd_133_observation_priority import ObservationPriorityProfile,verify_umd_133_observation_priority_profile\n\nUMD_134_BUILD_ID="UMD-134"\nUMD_134_REVISION="UMD_134_OBSERVATION_TIMELINE_REGISTRY_V1"\nUMD_134_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _utc(value:datetime)->datetime:\n    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:\n        raise ValueError("observed_at must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n@dataclass(frozen=True,slots=True)\nclass ObservationTimelineEntry:\n    observation_id:str\n    observed_at:datetime\n    route_hash:str\n    priority_profile_hash:str\n    domain:str\n\n    def __post_init__(self):\n        object.__setattr__(self,"observed_at",_utc(self.observed_at))\n        if not self.observation_id:\n            raise ValueError("observation_id must be non-empty")\n        if not self.domain:\n            raise ValueError("domain must be non-empty")\n\n    @property\n    def entry_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "observed_at":self.observed_at,\n            "route_hash":self.route_hash,\n            "priority_profile_hash":self.priority_profile_hash,\n            "domain":self.domain,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationTimeline:\n    timeline_id:str\n    entries:Tuple[ObservationTimelineEntry,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"entries",tuple(self.entries))\n        if not self.timeline_id:\n            raise ValueError("timeline_id must be non-empty")\n        expected=tuple(sorted(self.entries,key=lambda e:(e.observed_at,e.observation_id,e.entry_hash)))\n        if self.entries!=expected:\n            raise ValueError("timeline entries must be deterministically sorted")\n        if len({e.observation_id for e in self.entries})!=len(self.entries):\n            raise ValueError("timeline observation ids must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_134_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-134")\n        required={e.route_hash for e in self.entries}|{e.priority_profile_hash for e in self.entries}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every route and priority profile hash")\n\n    def observations_between(self,start:datetime,end:datetime)->Tuple[str,...]:\n        start=_utc(start); end=_utc(end)\n        if end<start:\n            raise ValueError("end must be at or after start")\n        return tuple(e.observation_id for e in self.entries if start<=e.observed_at<=end)\n\n    @property\n    def timeline_hash(self)->str:\n        return deterministic_sha256({\n            "timeline_id":self.timeline_id,\n            "entry_hashes":tuple(e.entry_hash for e in self.entries),\n            "lineage":self.lineage,\n        })\n\nclass ObservationTimelineBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        timeline_id:str,\n        items:Iterable[tuple[ObservationRoute,ObservationPriorityProfile,datetime]],\n        *,\n        lineage_factory,\n    )->ObservationTimeline:\n        entries=[]\n        for route,priority,observed_at in items:\n            if not isinstance(route,ObservationRoute):\n                raise TypeError("route must be ObservationRoute")\n            if not isinstance(priority,ObservationPriorityProfile):\n                raise TypeError("priority must be ObservationPriorityProfile")\n            if priority.observation_id!=route.observation_id or priority.route_hash!=route.route_hash:\n                raise ValueError("priority profile does not belong to route")\n            entries.append(ObservationTimelineEntry(\n                route.observation_id,observed_at,route.route_hash,priority.profile_hash,route.domain\n            ))\n        entries.sort(key=lambda e:(e.observed_at,e.observation_id,e.entry_hash))\n        lineage=lineage_factory(tuple(\n            h for e in entries for h in (e.route_hash,e.priority_profile_hash)\n        ))\n        return ObservationTimeline(timeline_id,tuple(entries),lineage)\n\ndef build_umd_134_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_134_BUILD_ID,"revision":UMD_134_REVISION,\n        "schema_version":UMD_134_SCHEMA_VERSION,"upstream_builds":("UMD-132","UMD-133"),\n        "mode":"deterministic_read_only_observation_timeline_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_134_observation_timeline_registry()->bool:\n    if verify_umd_133_observation_priority_profile() is not True:\n        return False\n    m=build_umd_134_certification_manifest()\n    return m["build_id"]=="UMD-134" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone,timedelta\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute\nfrom qseries_v2.universal_market_discovery.umd_133_observation_priority import ObservationPriorityProfile\nfrom qseries_v2.universal_market_discovery.umd_134_observation_timeline import *\n\nBASE=datetime(2026,8,10,1,0,tzinfo=timezone.utc)\n\ndef route(obs,seed):\n    c=seed*64; e=chr(ord(seed)+1)*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",\n        schema_version="1.0.0",parent_hashes=(c,e),source_refs=("fixture://134/132",),created_at=BASE)\n    return ObservationRoute(obs,"economics",c,e,(),(),(),(),(),(),(),l)\n\ndef priority(r):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-133",revision="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1",\n        schema_version="1.0.0",parent_hashes=(r.route_hash,),source_refs=("fixture://134/133",),created_at=BASE)\n    return ObservationPriorityProfile(r.observation_id,r.route_hash,0,0,0,0,0,0,0,l)\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-134",revision=UMD_134_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://134",),created_at=BASE)\n\nclass TestUMD134(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_134_observation_timeline_registry())\n    def test_temporal_order(self):\n        a=route("obs-a","a"); b=route("obs-b","c")\n        t=ObservationTimelineBuilder().build("macro",(\n            (b,priority(b),BASE+timedelta(minutes=2)),\n            (a,priority(a),BASE),\n        ),lineage_factory=lf)\n        self.assertEqual(tuple(e.observation_id for e in t.entries),("obs-a","obs-b"))\n    def test_range_query(self):\n        a=route("obs-a","a"); b=route("obs-b","c")\n        t=ObservationTimelineBuilder().build("macro",(\n            (a,priority(a),BASE),(b,priority(b),BASE+timedelta(minutes=2))\n        ),lineage_factory=lf)\n        self.assertEqual(t.observations_between(BASE,BASE+timedelta(minutes=1)),("obs-a",))\n    def test_naive_time_rejected(self):\n        a=route("obs-a","a")\n        with self.assertRaises(ValueError):\n            ObservationTimelineBuilder().build("macro",(\n                (a,priority(a),datetime(2026,8,10,1,0)),\n            ),lineage_factory=lf)\n    def test_priority_mismatch_rejected(self):\n        a=route("obs-a","a"); b=route("obs-b","c")\n        with self.assertRaises(ValueError):\n            ObservationTimelineBuilder().build("macro",((a,priority(b),BASE),),lineage_factory=lf)\n    def test_duplicate_observation_rejected(self):\n        a=route("obs-a","a"); p=priority(a)\n        with self.assertRaises(ValueError):\n            ObservationTimelineBuilder().build("macro",(\n                (a,p,BASE),(a,p,BASE+timedelta(minutes=1))\n            ),lineage_factory=lf)\n    def test_deterministic(self):\n        a=route("obs-a","a"); b=route("obs-b","c")\n        items=((a,priority(a),BASE),(b,priority(b),BASE+timedelta(minutes=1)))\n        x=ObservationTimelineBuilder().build("macro",items,lineage_factory=lf)\n        y=ObservationTimelineBuilder().build("macro",tuple(reversed(items)),lineage_factory=lf)\n        self.assertEqual(x.timeline_hash,y.timeline_hash)\n    def test_side_effects(self):\n        m=build_umd_134_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-134 CERTIFICATION TEST");print(" OBSERVATION TIMELINE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD134))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_134_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Deterministic timezone-aware observation timelines certified")\n    print("[PASS] Route-to-priority ownership and duplicate observation rejection certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-134 CERTIFIED")\n'
UPSTREAM_MODULE='umd_133_observation_priority'
UPSTREAM_VERIFIER='verify_umd_133_observation_priority_profile'
EXPORTED_NAMES=('UMD_134_REVISION', 'ObservationTimelineEntry', 'ObservationTimeline', 'ObservationTimelineBuilder', 'build_umd_134_certification_manifest', 'verify_umd_134_observation_timeline_registry')

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
    marker="# UMD-134 exports"
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
            raise RuntimeError("UMD-134 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-134 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-134 INSTALLER")
    print(" OBSERVATION TIMELINE REGISTRY")
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
        print("[ROLLBACK] UMD-134 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-134',
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
    print("[DONE] UMD-134 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
