from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_130_OBSERVATION_CLASSIFICATION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_130_observation_classification.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_130_observation_classification.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_109_market_semantic_profile import semantic_key\nfrom .umd_115_observation_impact import OBSERVATION_FIELDS\nfrom .umd_129_market_topology import verify_umd_129_market_topology_registry\n\nUMD_130_BUILD_ID="UMD-130"\nUMD_130_REVISION="UMD_130_OBSERVATION_CLASSIFICATION_V1"\nUMD_130_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\nOBSERVATION_DOMAINS=(\n    "weather",\n    "politics",\n    "economics",\n    "central-banking",\n    "corporate",\n    "regulatory",\n    "blockchain",\n    "energy",\n    "geopolitics",\n    "sports",\n    "science",\n    "space",\n    "health",\n    "technology",\n    "legal",\n    "other",\n)\n\nDOMAIN_ALIASES=MappingProxyType({\n    "weather":"weather",\n    "climate":"weather",\n    "politics":"politics",\n    "political":"politics",\n    "election":"politics",\n    "economics":"economics",\n    "economic":"economics",\n    "macro":"economics",\n    "macroeconomics":"economics",\n    "central-banking":"central-banking",\n    "central-bank":"central-banking",\n    "federal-reserve":"central-banking",\n    "fed":"central-banking",\n    "corporate":"corporate",\n    "company":"corporate",\n    "earnings":"corporate",\n    "regulatory":"regulatory",\n    "regulation":"regulatory",\n    "blockchain":"blockchain",\n    "crypto":"blockchain",\n    "on-chain":"blockchain",\n    "energy":"energy",\n    "geopolitics":"geopolitics",\n    "geopolitical":"geopolitics",\n    "sports":"sports",\n    "sport":"sports",\n    "science":"science",\n    "scientific":"science",\n    "space":"space",\n    "health":"health",\n    "medical":"health",\n    "technology":"technology",\n    "tech":"technology",\n    "legal":"legal",\n    "law":"legal",\n    "other":"other",\n})\n\ndef canonical_observation_domain(value:str)->str:\n    key=semantic_key(value)\n    domain=DOMAIN_ALIASES.get(key)\n    if domain is None:\n        raise ValueError("unsupported observation domain")\n    return domain\n\n@dataclass(frozen=True,slots=True)\nclass CanonicalObservationClassification:\n    observation_id:str\n    domain:str\n    routing_facts:Tuple[Tuple[str,str],...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        if not isinstance(self.observation_id,str) or not self.observation_id.strip():\n            raise ValueError("observation_id must be non-empty")\n        normalized=[]\n        for kind,value in self.routing_facts:\n            if kind=="entity":\n                raise ValueError("entity facts must be resolved by UMD-131")\n            if kind not in OBSERVATION_FIELDS:\n                raise ValueError("unsupported routing fact kind")\n            normalized.append((kind,semantic_key(value)))\n        normalized=tuple(sorted(set(normalized)))\n        object.__setattr__(self,"domain",canonical_observation_domain(self.domain))\n        object.__setattr__(self,"routing_facts",normalized)\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_130_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-130")\n\n    @property\n    def classification_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "domain":self.domain,\n            "routing_facts":self.routing_facts,\n            "lineage":self.lineage,\n        })\n\nclass ObservationClassifier:\n    __slots__=()\n\n    def classify(\n        self,\n        observation_id:str,\n        domain:str,\n        routing_facts:Iterable[tuple[str,str]]=(),\n        *,\n        lineage:ImmutableLineage,\n    )->CanonicalObservationClassification:\n        return CanonicalObservationClassification(\n            observation_id,\n            domain,\n            tuple(routing_facts),\n            lineage,\n        )\n\ndef build_umd_130_certification_manifest():\n    data={\n        "subsystem_id":"UMD",\n        "build_id":UMD_130_BUILD_ID,\n        "revision":UMD_130_REVISION,\n        "schema_version":UMD_130_SCHEMA_VERSION,\n        "upstream_builds":("UMD-109","UMD-115","UMD-129"),\n        "mode":"deterministic_read_only_observation_classification",\n        "observation_domains":OBSERVATION_DOMAINS,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,\n        "persistence_enabled":False,\n        "mutation_enabled":False,\n        "publication_enabled":False,\n        "execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_130_observation_classification()->bool:\n    if verify_umd_129_market_topology_registry() is not True:\n        return False\n    m=build_umd_130_certification_manifest()\n    return m["build_id"]=="UMD-130" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_130_observation_classification import *\n\nFIXED=datetime(2026,8,9,23,30,tzinfo=timezone.utc)\n\ndef lineage():\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-130",\n        revision=UMD_130_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(),\n        source_refs=("fixture://130",),\n        created_at=FIXED,\n    )\n\nclass TestUMD130(unittest.TestCase):\n    def test_foundation(self):\n        self.assertTrue(verify_umd_130_observation_classification())\n\n    def test_classification(self):\n        c=ObservationClassifier().classify(\n            "obs-1",\n            "Economic",\n            (("metric","Consumer Price Index"),("event","CPI Release")),\n            lineage=lineage(),\n        )\n        self.assertEqual(c.domain,"economics")\n        self.assertEqual(\n            c.routing_facts,\n            (("event","cpi-release"),("metric","consumer-price-index")),\n        )\n\n    def test_domain_alias(self):\n        c=ObservationClassifier().classify("obs-2","FED",(),lineage=lineage())\n        self.assertEqual(c.domain,"central-banking")\n\n    def test_deduplication(self):\n        c=ObservationClassifier().classify(\n            "obs-3","crypto",\n            (("asset","Bitcoin"),("asset","BITCOIN")),\n            lineage=lineage(),\n        )\n        self.assertEqual(c.routing_facts,(("asset","bitcoin"),))\n\n    def test_entity_reserved_for_131(self):\n        with self.assertRaises(ValueError):\n            ObservationClassifier().classify(\n                "obs-4","politics",\n                (("entity","Federal Reserve"),),\n                lineage=lineage(),\n            )\n\n    def test_unknown_domain_rejected(self):\n        with self.assertRaises(ValueError):\n            ObservationClassifier().classify("obs-5","unknown-domain",(),lineage=lineage())\n\n    def test_deterministic(self):\n        a=ObservationClassifier().classify(\n            "obs-6","weather",\n            (("event","Hurricane Warning"),("geography","Gulf Coast")),\n            lineage=lineage(),\n        )\n        b=ObservationClassifier().classify(\n            "obs-6","weather",\n            (("geography","Gulf Coast"),("event","Hurricane Warning")),\n            lineage=lineage(),\n        )\n        self.assertEqual(a.classification_hash,b.classification_hash)\n\n    def test_immutable(self):\n        c=ObservationClassifier().classify("obs-7","sports",(),lineage=lineage())\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            c.domain="weather"\n\n    def test_side_effects(self):\n        m=build_umd_130_certification_manifest()\n        self.assertFalse(any(\n            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n        ))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-130 CERTIFICATION TEST");print(" OBSERVATION CLASSIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD130))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    m=build_umd_130_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical observation domains and routing-fact normalization certified")\n    print("[PASS] Entity resolution remains isolated to UMD-131")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-130 CERTIFIED")\n'
UPSTREAM_MODULE='umd_129_market_topology'
UPSTREAM_VERIFIER='verify_umd_129_market_topology_registry'
EXPORTED_NAMES=('UMD_130_REVISION', 'OBSERVATION_DOMAINS', 'DOMAIN_ALIASES', 'canonical_observation_domain', 'CanonicalObservationClassification', 'ObservationClassifier', 'build_umd_130_certification_manifest', 'verify_umd_130_observation_classification')

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
    marker="# UMD-130 exports"
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
            raise RuntimeError("UMD-130 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-130 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-130 INSTALLER")
    print(" OBSERVATION CLASSIFICATION")
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
        print("[ROLLBACK] UMD-130 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-130',
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
    print("[DONE] UMD-130 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
