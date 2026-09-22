from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_127_MARKET_LADDER_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_127_market_ladder.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_127_market_ladder.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom decimal import Decimal, InvalidOperation\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile\nfrom .umd_110_market_family_resolution import MarketFamily\nfrom .umd_126_impact_coverage_registry import verify_umd_126_impact_coverage_registry\n\nUMD_127_BUILD_ID="UMD-127"\nUMD_127_REVISION="UMD_127_MARKET_LADDER_MODEL_V1"\nUMD_127_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nLADDER_OPERATORS=("above","at-least","below","at-most")\n\n@dataclass(frozen=True,slots=True)\nclass LadderRung:\n    canonical_market_id:str\n    threshold:str\n    threshold_decimal:str\n    operator:str\n    profile_hash:str\n\n    def __post_init__(self):\n        if self.operator not in LADDER_OPERATORS:\n            raise ValueError("unsupported ladder operator")\n        try:\n            parsed=Decimal(self.threshold)\n        except (InvalidOperation,ValueError):\n            raise ValueError("threshold must be decimal-compatible")\n        normalized=format(parsed.normalize(),"f")\n        if "." in normalized:\n            normalized=normalized.rstrip("0").rstrip(".")\n        if normalized=="-0":\n            normalized="0"\n        if self.threshold_decimal!=normalized:\n            raise ValueError("threshold_decimal does not match threshold")\n\n    @property\n    def rung_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "threshold_decimal":self.threshold_decimal,\n            "operator":self.operator,\n            "profile_hash":self.profile_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass MarketLadder:\n    family_key:str\n    operator:str\n    rungs:Tuple[LadderRung,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"rungs",tuple(self.rungs))\n        if not self.rungs:\n            raise ValueError("market ladder requires at least one rung")\n        if any(r.operator!=self.operator for r in self.rungs):\n            raise ValueError("all rungs must use ladder operator")\n        expected=tuple(sorted(\n            self.rungs,\n            key=lambda r:(Decimal(r.threshold_decimal),r.canonical_market_id),\n        ))\n        if expected!=self.rungs:\n            raise ValueError("rungs must be sorted by numeric threshold")\n        thresholds=[r.threshold_decimal for r in self.rungs]\n        if len(thresholds)!=len(set(thresholds)):\n            raise ValueError("duplicate threshold in ladder")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_127_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-127")\n        required={r.profile_hash for r in self.rungs}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every rung profile hash")\n\n    def market_at_threshold(self,threshold:str)->str|None:\n        try:\n            target=Decimal(threshold)\n        except (InvalidOperation,ValueError):\n            return None\n        for rung in self.rungs:\n            if Decimal(rung.threshold_decimal)==target:\n                return rung.canonical_market_id\n        return None\n\n    @property\n    def ladder_hash(self)->str:\n        return deterministic_sha256({\n            "family_key":self.family_key,\n            "operator":self.operator,\n            "rung_hashes":tuple(r.rung_hash for r in self.rungs),\n            "lineage":self.lineage,\n        })\n\nclass MarketLadderBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        family:MarketFamily,\n        profiles:Iterable[MarketSemanticProfile],\n        *,\n        lineage:ImmutableLineage,\n    )->MarketLadder:\n        if not isinstance(family,MarketFamily):\n            raise TypeError("family must be MarketFamily")\n        ps=tuple(profiles)\n        if any(not isinstance(p,MarketSemanticProfile) for p in ps):\n            raise TypeError("profiles must contain MarketSemanticProfile")\n\n        members=set(family.member_market_ids)\n        selected=[p for p in ps if p.canonical_market_id in members]\n        if {p.canonical_market_id for p in selected}!=members:\n            raise ValueError("profiles must cover every family member")\n\n        rungs=[]\n        operator=None\n        for profile in selected:\n            thresholds=profile.values("threshold")\n            operators=profile.values("operator")\n            if len(thresholds)!=1 or len(operators)!=1:\n                raise ValueError("ladder profile requires exactly one threshold and one operator")\n            op=operators[0]\n            if op not in LADDER_OPERATORS:\n                raise ValueError("unsupported ladder operator")\n            if operator is None:\n                operator=op\n            elif operator!=op:\n                raise ValueError("mixed operators cannot form one ladder")\n            parsed=Decimal(thresholds[0])\n            normalized=format(parsed.normalize(),"f")\n            if "." in normalized:\n                normalized=normalized.rstrip("0").rstrip(".")\n            if normalized=="-0":\n                normalized="0"\n            rungs.append(LadderRung(\n                profile.canonical_market_id,\n                thresholds[0],\n                normalized,\n                op,\n                profile.profile_hash,\n            ))\n\n        rungs.sort(key=lambda r:(Decimal(r.threshold_decimal),r.canonical_market_id))\n        return MarketLadder(family.family_key,operator,tuple(rungs),lineage)\n\ndef build_umd_127_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_127_BUILD_ID,"revision":UMD_127_REVISION,\n        "schema_version":UMD_127_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110","UMD-126"),\n        "mode":"deterministic_read_only_market_ladder_model",\n        "ladder_operators":LADDER_OPERATORS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_127_market_ladder_model()->bool:\n    if verify_umd_126_impact_coverage_registry() is not True:\n        return False\n    m=build_umd_127_certification_manifest()\n    return m["build_id"]=="UMD-127" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamily\nfrom qseries_v2.universal_market_discovery.umd_127_market_ladder import *\n\nFIXED=datetime(2026,8,9,23,0,tzinfo=timezone.utc)\n\ndef profile(cid,ih,threshold,operator="Above"):\n    l102=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://127/102",),created_at=FIXED\n    )\n    r=CanonicalMarketRecord(\n        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),\n        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102\n    )\n    l109=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.record_hash,),\n        source_refs=("fixture://127/109",),created_at=FIXED\n    )\n    return MarketSemanticProfiler().build(\n        r,\n        (("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),\n         ("operator",operator),("threshold",threshold),("unit","USD")),\n        lineage=l109,\n    )\n\ndef family(ps):\n    hashes=tuple(p.profile_hash for p in ps)\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,\n        schema_version="1.0.0",parent_hashes=hashes,\n        source_refs=("fixture://127/110",),created_at=FIXED\n    )\n    return MarketFamily(\n        "asset=bitcoin|event=*|metric=price|market_type=price-threshold",\n        ("asset","event","metric","market_type"),\n        tuple(sorted(p.canonical_market_id for p in ps)),\n        tuple(p.profile_hash for p in sorted(ps,key=lambda x:x.canonical_market_id)),\n        l,\n    )\n\ndef lineage(ps):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-127",revision=UMD_127_REVISION,\n        schema_version="1.0.0",parent_hashes=tuple(p.profile_hash for p in ps),\n        source_refs=("fixture://127",),created_at=FIXED\n    )\n\nclass TestUMD127(unittest.TestCase):\n    def setUp(self):\n        self.a=profile("m1","a"*64,"100000")\n        self.b=profile("m2","b"*64,"150000")\n        self.c=profile("m3","c"*64,"200000")\n        self.ps=(self.a,self.b,self.c)\n        self.f=family(self.ps)\n\n    def test_foundation(self): self.assertTrue(verify_umd_127_market_ladder_model())\n    def test_numeric_order(self):\n        ladder=MarketLadderBuilder().build(self.f,(self.c,self.a,self.b),lineage=lineage(self.ps))\n        self.assertEqual(tuple(r.canonical_market_id for r in ladder.rungs),("m1","m2","m3"))\n    def test_threshold_lookup(self):\n        ladder=MarketLadderBuilder().build(self.f,self.ps,lineage=lineage(self.ps))\n        self.assertEqual(ladder.market_at_threshold("150000.0"),"m2")\n    def test_deterministic(self):\n        a=MarketLadderBuilder().build(self.f,self.ps,lineage=lineage(self.ps))\n        b=MarketLadderBuilder().build(self.f,tuple(reversed(self.ps)),lineage=lineage(self.ps))\n        self.assertEqual(a.ladder_hash,b.ladder_hash)\n    def test_mixed_operator_rejected(self):\n        bad=profile("m3","c"*64,"200000","Below")\n        ps=(self.a,self.b,bad)\n        with self.assertRaises(ValueError):\n            MarketLadderBuilder().build(family(ps),ps,lineage=lineage(ps))\n    def test_missing_family_member_rejected(self):\n        with self.assertRaises(ValueError):\n            MarketLadderBuilder().build(self.f,(self.a,self.b),lineage=lineage(self.ps))\n    def test_side_effects(self):\n        m=build_umd_127_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-127 CERTIFICATION TEST");print(" MARKET LADDER MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD127))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_127_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Deterministic numeric threshold ladders certified")\n    print("[PASS] Mixed operators and incomplete family coverage rejected")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-127 CERTIFIED")\n'
UPSTREAM_MODULE='umd_126_impact_coverage_registry'
UPSTREAM_VERIFIER='verify_umd_126_impact_coverage_registry'
EXPORTED_NAMES=('UMD_127_REVISION', 'LADDER_OPERATORS', 'LadderRung', 'MarketLadder', 'MarketLadderBuilder', 'build_umd_127_certification_manifest', 'verify_umd_127_market_ladder_model')

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
    marker="# UMD-127 exports"
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
            raise RuntimeError("UMD-127 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-127 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-127 INSTALLER")
    print(" MARKET LADDER MODEL")
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
        print("[ROLLBACK] UMD-127 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-127',
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
    print("[DONE] UMD-127 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
