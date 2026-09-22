from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_121_IMPACT_FAMILY_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_121_impact_family_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_121_impact_family_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_110_market_family_resolution import MarketFamily\nfrom .umd_119_impact_provenance import ImpactProvenanceBundle\nfrom .umd_120_impact_query_engine import verify_umd_120_impact_query_engine\n\nUMD_121_BUILD_ID="UMD-121"\nUMD_121_REVISION="UMD_121_IMPACT_FAMILY_PROJECTION_V1"\nUMD_121_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass FamilyImpact:\n    family_key:str\n    family_hash:str\n    impacted_market_ids:Tuple[str,...]\n    direct_market_ids:Tuple[str,...]\n    propagated_market_ids:Tuple[str,...]\n\n    def __post_init__(self):\n        for name in ("impacted_market_ids","direct_market_ids","propagated_market_ids"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n        if set(self.direct_market_ids)|set(self.propagated_market_ids) != set(self.impacted_market_ids):\n            raise ValueError("direct and propagated markets must exactly cover impacted markets")\n        if set(self.direct_market_ids)&set(self.propagated_market_ids):\n            raise ValueError("market cannot be both direct and propagated within one projection")\n\n    @property\n    def impact_hash(self)->str:\n        return deterministic_sha256({\n            "family_key":self.family_key,\n            "family_hash":self.family_hash,\n            "impacted_market_ids":self.impacted_market_ids,\n            "direct_market_ids":self.direct_market_ids,\n            "propagated_market_ids":self.propagated_market_ids,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass FamilyImpactProjection:\n    observation_hash:str\n    family_impacts:Tuple[FamilyImpact,...]\n    unmatched_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"family_impacts",tuple(self.family_impacts))\n        object.__setattr__(self,"unmatched_market_ids",tuple(self.unmatched_market_ids))\n        if tuple(sorted(self.family_impacts,key=lambda x:(x.family_key,x.family_hash)))!=self.family_impacts:\n            raise ValueError("family_impacts must be deterministically sorted")\n        if self.unmatched_market_ids!=tuple(sorted(set(self.unmatched_market_ids))):\n            raise ValueError("unmatched_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_121_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-121")\n\n    def markets_in_family(self,family_key:str)->Tuple[str,...]:\n        for impact in self.family_impacts:\n            if impact.family_key==family_key:\n                return impact.impacted_market_ids\n        return ()\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "family_impact_hashes":tuple(x.impact_hash for x in self.family_impacts),\n            "unmatched_market_ids":self.unmatched_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ImpactFamilyProjector:\n    __slots__=()\n\n    def project(\n        self,\n        bundle:ImpactProvenanceBundle,\n        families:Iterable[MarketFamily],\n        *,\n        lineage:ImmutableLineage,\n    )->FamilyImpactProjection:\n        if not isinstance(bundle,ImpactProvenanceBundle):\n            raise TypeError("bundle must be ImpactProvenanceBundle")\n        fs=tuple(families)\n        if any(not isinstance(f,MarketFamily) for f in fs):\n            raise TypeError("families must contain MarketFamily")\n\n        entries={e.canonical_market_id:e for e in bundle.entries}\n        impacted=set(entries)\n        assigned=set()\n        results=[]\n\n        for family in sorted(fs,key=lambda f:(f.family_key,f.family_hash)):\n            members=tuple(sorted(impacted & set(family.member_market_ids)))\n            if not members:\n                continue\n            direct=tuple(m for m in members if entries[m].direct)\n            propagated=tuple(m for m in members if not entries[m].direct)\n            results.append(FamilyImpact(\n                family.family_key,\n                family.family_hash,\n                members,\n                direct,\n                propagated,\n            ))\n            assigned.update(members)\n\n        return FamilyImpactProjection(\n            bundle.observation_hash,\n            tuple(results),\n            tuple(sorted(impacted-assigned)),\n            lineage,\n        )\n\ndef build_umd_121_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_121_BUILD_ID,"revision":UMD_121_REVISION,\n        "schema_version":UMD_121_SCHEMA_VERSION,"upstream_builds":("UMD-110","UMD-119","UMD-120"),\n        "mode":"deterministic_read_only_impact_family_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_121_impact_family_projection()->bool:\n    if verify_umd_120_impact_query_engine() is not True:\n        return False\n    m=build_umd_121_certification_manifest()\n    return m["build_id"]=="UMD-121" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import MarketFamily\nfrom qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle\nfrom qseries_v2.universal_market_discovery.umd_121_impact_family_projection import *\n\nFIXED=datetime(2026,8,9,21,0,tzinfo=timezone.utc)\n\ndef bundle():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://121/119",),created_at=FIXED)\n    return ImpactProvenanceBundle(\n        "a"*64,\n        (\n            MarketImpactProvenance("m1",True,(("asset","bitcoin"),),("m1",),()),\n            MarketImpactProvenance("m2",False,(),("m1","m2"),("implies",)),\n            MarketImpactProvenance("m3",True,(("asset","ethereum"),),("m3",),()),\n        ),\n        l,\n    )\n\ndef family(key,members,seed):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=tuple((seed+i)*64 for i in range(len(members))) if False else tuple("a"*64 for _ in members),\n        source_refs=("fixture://121/110",),created_at=FIXED)\n    # Construct directly through the certified dataclass with valid member hashes and lineage.\n    hashes=tuple(chr(ord("a")+i)*64 for i in range(len(members)))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",\n        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://121/110",),created_at=FIXED)\n    return MarketFamily(key,("asset",),tuple(members),hashes,l)\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision=UMD_121_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://121",),created_at=FIXED)\n\nclass TestUMD121(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_121_impact_family_projection())\n    def test_family_projection(self):\n        f1=family("asset=bitcoin",("m1","m2"),0)\n        f2=family("asset=ethereum",("m3",),2)\n        p=ImpactFamilyProjector().project(bundle(),(f2,f1),lineage=lineage())\n        self.assertEqual(tuple(x.family_key for x in p.family_impacts),("asset=bitcoin","asset=ethereum"))\n        self.assertEqual(p.markets_in_family("asset=bitcoin"),("m1","m2"))\n    def test_direct_propagated_split(self):\n        f1=family("asset=bitcoin",("m1","m2"),0)\n        p=ImpactFamilyProjector().project(bundle(),(f1,),lineage=lineage())\n        x=p.family_impacts[0]\n        self.assertEqual(x.direct_market_ids,("m1",))\n        self.assertEqual(x.propagated_market_ids,("m2",))\n    def test_unmatched(self):\n        f1=family("asset=bitcoin",("m1","m2"),0)\n        p=ImpactFamilyProjector().project(bundle(),(f1,),lineage=lineage())\n        self.assertEqual(p.unmatched_market_ids,("m3",))\n    def test_deterministic(self):\n        f1=family("asset=bitcoin",("m1","m2"),0)\n        f2=family("asset=ethereum",("m3",),2)\n        a=ImpactFamilyProjector().project(bundle(),(f1,f2),lineage=lineage())\n        b=ImpactFamilyProjector().project(bundle(),(f2,f1),lineage=lineage())\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_family(self):\n        with self.assertRaises(TypeError):\n            ImpactFamilyProjector().project(bundle(),(object(),),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_121_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-121 CERTIFICATION TEST");print(" IMPACT FAMILY PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD121))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_121_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation impact projected across semantic market families")\n    print("[PASS] Direct, propagated, and unmatched family coverage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-121 CERTIFIED")\n'
UPSTREAM_MODULE='umd_120_impact_query_engine'
UPSTREAM_VERIFIER='verify_umd_120_impact_query_engine'
EXPORTED_NAMES=('UMD_121_REVISION', 'FamilyImpact', 'FamilyImpactProjection', 'ImpactFamilyProjector', 'build_umd_121_certification_manifest', 'verify_umd_121_impact_family_projection')

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
    marker="# UMD-121 exports"
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
            raise RuntimeError("UMD-121 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-121 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-121 INSTALLER")
    print(" IMPACT FAMILY PROJECTION")
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
        print("[ROLLBACK] UMD-121 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-121',
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
    print("[DONE] UMD-121 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
