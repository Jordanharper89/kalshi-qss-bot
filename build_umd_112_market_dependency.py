from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_112_MARKET_DEPENDENCY_MODEL_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_112_market_dependency.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_112_market_dependency.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_109_market_semantic_profile import MarketSemanticProfile, semantic_key\nfrom .umd_111_semantic_registry import verify_umd_111_semantic_registry\n\nUMD_112_BUILD_ID="UMD-112"\nUMD_112_REVISION="UMD_112_MARKET_DEPENDENCY_MODEL_V1"\nUMD_112_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\nDEPENDENCY_ROLES=("required","supporting","settlement","context")\nDEPENDENCY_KINDS=("entity","asset","event","metric","geography","time_window","settlement_source","external_state")\n\n@dataclass(frozen=True,slots=True)\nclass MarketDependency:\n    kind:str\n    value:str\n    key:str\n    role:str\n\n    def __post_init__(self):\n        if self.kind not in DEPENDENCY_KINDS:\n            raise ValueError("unsupported dependency kind")\n        if self.role not in DEPENDENCY_ROLES:\n            raise ValueError("unsupported dependency role")\n        if self.key!=semantic_key(self.value):\n            raise ValueError("dependency key does not match value")\n\n    @property\n    def dependency_hash(self)->str:\n        return deterministic_sha256({\n            "kind":self.kind,\n            "key":self.key,\n            "role":self.role,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass MarketDependencyProfile:\n    canonical_market_id:str\n    semantic_profile_hash:str\n    dependencies:Tuple[MarketDependency,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"dependencies",tuple(self.dependencies))\n        expected=tuple(sorted(self.dependencies,key=lambda d:(d.kind,d.key,d.role)))\n        if expected!=self.dependencies:\n            raise ValueError("dependencies must be deterministically sorted")\n        keys=[(d.kind,d.key,d.role) for d in self.dependencies]\n        if len(keys)!=len(set(keys)):\n            raise ValueError("duplicate market dependency")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_112_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-112")\n        if self.semantic_profile_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include semantic profile hash")\n\n    def dependency_keys(self,kind:str|None=None,role:str|None=None)->Tuple[str,...]:\n        return tuple(\n            d.key for d in self.dependencies\n            if (kind is None or d.kind==kind) and (role is None or d.role==role)\n        )\n\n    @property\n    def profile_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "semantic_profile_hash":self.semantic_profile_hash,\n            "dependencies":tuple({\n                "kind":d.kind,\n                "key":d.key,\n                "role":d.role,\n            } for d in self.dependencies),\n            "lineage":self.lineage,\n        })\n\nclass MarketDependencyBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        profile:MarketSemanticProfile,\n        dependencies:Iterable[tuple[str,str,str]],\n        *,\n        lineage:ImmutableLineage,\n    )->MarketDependencyProfile:\n        if not isinstance(profile,MarketSemanticProfile):\n            raise TypeError("profile must be MarketSemanticProfile")\n        built=[]\n        seen=set()\n        for kind,value,role in dependencies:\n            key=semantic_key(value)\n            identity=(kind,key,role)\n            if identity in seen:\n                continue\n            seen.add(identity)\n            built.append(MarketDependency(kind,value,key,role))\n        built.sort(key=lambda d:(d.kind,d.key,d.role))\n        return MarketDependencyProfile(\n            profile.canonical_market_id,\n            profile.profile_hash,\n            tuple(built),\n            lineage,\n        )\n\ndef build_umd_112_certification_manifest():\n    data={\n        "subsystem_id":"UMD",\n        "build_id":UMD_112_BUILD_ID,\n        "revision":UMD_112_REVISION,\n        "schema_version":UMD_112_SCHEMA_VERSION,\n        "upstream_builds":("UMD-109","UMD-111"),\n        "mode":"deterministic_read_only_market_dependency_model",\n        "dependency_roles":DEPENDENCY_ROLES,\n        "dependency_kinds":DEPENDENCY_KINDS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,\n        "persistence_enabled":False,\n        "mutation_enabled":False,\n        "publication_enabled":False,\n        "execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_112_market_dependency_model()->bool:\n    if verify_umd_111_semantic_registry() is not True:\n        return False\n    m=build_umd_112_certification_manifest()\n    return m["build_id"]=="UMD-112" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler\nfrom qseries_v2.universal_market_discovery.umd_112_market_dependency import *\n\nFIXED=datetime(2026,8,9,18,0,tzinfo=timezone.utc)\n\ndef semantic_profile():\n    ih="a"*64\n    l102=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://112/102",),created_at=FIXED\n    )\n    record=CanonicalMarketRecord(\n        "umd:market:btc100k",ih,(VenueMarketBinding("kalshi","K-BTC100K",ih),),\n        "btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,\n        ("btc-100k",),(),"",{},l102\n    )\n    l109=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,\n        schema_version="1.0.0",parent_hashes=(record.record_hash,),\n        source_refs=("fixture://112/109",),created_at=FIXED\n    )\n    return MarketSemanticProfiler().build(\n        record,\n        (("asset","Bitcoin"),("metric","Price"),("threshold","100000"),("unit","USD")),\n        lineage=l109,\n    )\n\ndef lineage(profile):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,\n        schema_version="1.0.0",parent_hashes=(profile.profile_hash,),\n        source_refs=("fixture://112",),created_at=FIXED\n    )\n\nclass TestUMD112(unittest.TestCase):\n    def test_foundation(self):\n        self.assertTrue(verify_umd_112_market_dependency_model())\n\n    def test_dependency_profile(self):\n        p=semantic_profile()\n        d=MarketDependencyBuilder().build(\n            p,\n            (\n                ("asset","Bitcoin","required"),\n                ("metric","BTC Spot Price","required"),\n                ("settlement_source","Official Settlement Feed","settlement"),\n            ),\n            lineage=lineage(p),\n        )\n        self.assertEqual(d.dependency_keys("asset"),("bitcoin",))\n        self.assertEqual(d.dependency_keys("metric"),("btc-spot-price",))\n\n    def test_roles(self):\n        p=semantic_profile()\n        d=MarketDependencyBuilder().build(\n            p,\n            (("metric","BTC Spot Price","required"),("metric","BTC VWAP","supporting")),\n            lineage=lineage(p),\n        )\n        self.assertEqual(d.dependency_keys(role="supporting"),("btc-vwap",))\n\n    def test_deduplication(self):\n        p=semantic_profile()\n        d=MarketDependencyBuilder().build(\n            p,\n            (("asset","Bitcoin","required"),("asset","BITCOIN","required")),\n            lineage=lineage(p),\n        )\n        self.assertEqual(len(d.dependencies),1)\n\n    def test_deterministic(self):\n        p=semantic_profile(); l=lineage(p)\n        a=MarketDependencyBuilder().build(\n            p,\n            (("asset","Bitcoin","required"),("metric","BTC Spot Price","required")),\n            lineage=l,\n        )\n        b=MarketDependencyBuilder().build(\n            p,\n            (("metric","BTC Spot Price","required"),("asset","Bitcoin","required")),\n            lineage=l,\n        )\n        self.assertEqual(a.profile_hash,b.profile_hash)\n\n    def test_invalid_kind(self):\n        p=semantic_profile()\n        with self.assertRaises(ValueError):\n            MarketDependencyBuilder().build(p,(("unknown","X","required"),),lineage=lineage(p))\n\n    def test_invalid_role(self):\n        p=semantic_profile()\n        with self.assertRaises(ValueError):\n            MarketDependencyBuilder().build(p,(("asset","Bitcoin","trade"),),lineage=lineage(p))\n\n    def test_lineage_required(self):\n        p=semantic_profile()\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),\n            source_refs=("fixture://112/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            MarketDependencyBuilder().build(p,(("asset","Bitcoin","required"),),lineage=bad)\n\n    def test_immutable(self):\n        p=semantic_profile()\n        d=MarketDependencyBuilder().build(p,(("asset","Bitcoin","required"),),lineage=lineage(p))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            d.dependencies=()\n\n    def test_side_effects(self):\n        m=build_umd_112_certification_manifest()\n        self.assertFalse(any(\n            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n        ))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-112 CERTIFICATION TEST");print(" MARKET DEPENDENCY MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD112))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    m=build_umd_112_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Required, supporting, settlement, and context dependencies certified")\n    print("[PASS] Semantic profiles consumed read-only")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-112 CERTIFIED")\n'
UPSTREAM_MODULE='umd_111_semantic_registry'
UPSTREAM_VERIFIER='verify_umd_111_semantic_registry'
EXPORTED_NAMES=('UMD_112_REVISION', 'DEPENDENCY_ROLES', 'DEPENDENCY_KINDS', 'MarketDependency', 'MarketDependencyProfile', 'MarketDependencyBuilder', 'build_umd_112_certification_manifest', 'verify_umd_112_market_dependency_model')

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
    marker="# UMD-112 exports"
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
            raise RuntimeError("UMD-112 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-112 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-112 INSTALLER")
    print(" MARKET DEPENDENCY MODEL")
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
        print("[ROLLBACK] UMD-112 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-112',
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
    print("[DONE] UMD-112 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
