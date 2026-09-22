from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_098_MARKET_TAXONOMY_CLASSIFICATION_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_098_market_taxonomy.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_098_market_taxonomy.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_095_market_identity import CanonicalMarketIdentity\nfrom .umd_097_market_relationship_graph import verify_umd_097_market_relationship_graph\n\nUMD_098_BUILD_ID="UMD-098"\nUMD_098_BUILD_NAME="Market Taxonomy Classification"\nUMD_098_REVISION="UMD_098_MARKET_TAXONOMY_CLASSIFICATION_V1"\nUMD_098_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n\ndef _token(value:str,field_name:str)->str:\n    if not isinstance(value,str):\n        raise TypeError(f"{field_name} must be a string")\n    value=value.strip().casefold().replace("_","-").replace(" ","-")\n    while "--" in value:\n        value=value.replace("--","-")\n    if not value:\n        raise ValueError(f"{field_name} must be non-empty")\n    if any(not (c.isalnum() or c=="-") for c in value):\n        raise ValueError(f"{field_name} contains unsupported characters")\n    return value\n\n\ndef _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:\n    if value is None:\n        value={}\n    if not isinstance(value,Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))\n\n\n@dataclass(frozen=True,slots=True)\nclass TaxonomyPath:\n    asset:str\n    domain:str\n    category:str\n    subcategory:str\n    market_type:str\n\n    def __post_init__(self):\n        for name in ("asset","domain","category","subcategory","market_type"):\n            object.__setattr__(self,name,_token(getattr(self,name),name))\n\n    @property\n    def taxonomy_key(self)->str:\n        return "/".join((self.asset,self.domain,self.category,self.subcategory,self.market_type))\n\n\n@dataclass(frozen=True,slots=True)\nclass TaxonomyRule:\n    rule_id:str\n    path:TaxonomyPath\n    category_keys:Tuple[str,...]=()\n    title_terms:Tuple[str,...]=()\n    priority:int=100\n\n    def __post_init__(self):\n        object.__setattr__(self,"rule_id",_token(self.rule_id,"rule_id"))\n        if not isinstance(self.path,TaxonomyPath):\n            raise TypeError("path must be TaxonomyPath")\n        categories=tuple(sorted({_token(x,"category_key") for x in self.category_keys}))\n        terms=tuple(sorted({_token(x,"title_term") for x in self.title_terms}))\n        if not categories and not terms:\n            raise ValueError("taxonomy rule requires category_keys or title_terms")\n        if not isinstance(self.priority,int) or self.priority<0:\n            raise ValueError("priority must be a non-negative integer")\n        object.__setattr__(self,"category_keys",categories)\n        object.__setattr__(self,"title_terms",terms)\n\n    def matches(self,identity:CanonicalMarketIdentity)->bool:\n        if self.category_keys and identity.category_key in self.category_keys:\n            return True\n        title_tokens=set(identity.title_key.split("-"))\n        return bool(self.title_terms and set(self.title_terms).issubset(title_tokens))\n\n\n@dataclass(frozen=True,slots=True)\nclass MarketTaxonomyClassification:\n    canonical_market_id:str\n    identity_hash:str\n    taxonomy_path:TaxonomyPath\n    rule_id:str\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_098_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-098")\n        if self.identity_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include identity hash")\n\n    def to_canonical_dict(self):\n        return {\n            "canonical_market_id":self.canonical_market_id,\n            "identity_hash":self.identity_hash,\n            "taxonomy_key":self.taxonomy_path.taxonomy_key,\n            "rule_id":self.rule_id,\n            "metadata":self.metadata,\n            "lineage":self.lineage,\n        }\n\n    @property\n    def classification_hash(self):\n        return deterministic_sha256(self.to_canonical_dict())\n\n\nclass MarketTaxonomyClassifier:\n    __slots__=("rules",)\n\n    def __init__(self,rules:Iterable[TaxonomyRule]):\n        values=tuple(rules)\n        if not values:\n            raise ValueError("at least one taxonomy rule is required")\n        if any(not isinstance(x,TaxonomyRule) for x in values):\n            raise TypeError("rules must contain TaxonomyRule")\n        if len({x.rule_id for x in values})!=len(values):\n            raise ValueError("rule_id values must be unique")\n        self.rules=tuple(sorted(values,key=lambda x:(x.priority,x.rule_id)))\n\n    def classify(\n        self,\n        identity:CanonicalMarketIdentity,\n        *,\n        lineage:ImmutableLineage,\n        metadata:Mapping[str,Any] | None=None,\n    )->MarketTaxonomyClassification:\n        if not isinstance(identity,CanonicalMarketIdentity):\n            raise TypeError("identity must be CanonicalMarketIdentity")\n        matches=[rule for rule in self.rules if rule.matches(identity)]\n        if not matches:\n            raise LookupError("no taxonomy rule matched market identity")\n        chosen=matches[0]\n        return MarketTaxonomyClassification(\n            canonical_market_id=identity.canonical_market_id,\n            identity_hash=identity.identity_hash,\n            taxonomy_path=chosen.path,\n            rule_id=chosen.rule_id,\n            metadata={} if metadata is None else metadata,\n            lineage=lineage,\n        )\n\n\ndef build_umd_098_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_098_BUILD_ID,"revision":UMD_098_REVISION,\n        "schema_version":UMD_098_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-097"),\n        "hierarchy":("asset","domain","category","subcategory","market_type"),\n        "mode":"deterministic_read_only_taxonomy_classification",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\n\ndef verify_umd_098_market_taxonomy_classification()->bool:\n    if verify_umd_097_market_relationship_graph() is not True:\n        return False\n    m=build_umd_098_certification_manifest()\n    return m["build_id"]=="UMD-098" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver\nfrom qseries_v2.universal_market_discovery.umd_098_market_taxonomy import (\n    UMD_098_REVISION,TaxonomyPath,TaxonomyRule,MarketTaxonomyClassifier,\n    build_umd_098_certification_manifest,verify_umd_098_market_taxonomy_classification,\n)\n\nFIXED=datetime(2026,8,8,13,10,tzinfo=timezone.utc)\n\ndef identity(title="Will BTC exceed 100K?",category="Crypto"):\n    o=MarketObservation(venue="Kalshi",venue_market_id="A",title=title,category=category,status="Open",outcomes=("Yes","No"))\n    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://098/94",),created_at=FIXED)\n    m=MarketNormalizer().normalize(o,lineage=l94)\n    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://098/95",),created_at=FIXED)\n    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)\n\ndef lineage(i):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://098",),created_at=FIXED)\n\ndef rules():\n    return (\n        TaxonomyRule("crypto-price",TaxonomyPath("btc","digital-assets","crypto","bitcoin","price-threshold"),category_keys=("crypto",),priority=10),\n        TaxonomyRule("politics-election",TaxonomyPath("none","politics","elections","candidate","binary-outcome"),category_keys=("politics",),priority=20),\n    )\n\nclass TestUMD098(unittest.TestCase):\n    def test_foundation(self):\n        self.assertTrue(verify_umd_098_market_taxonomy_classification())\n\n    def test_classification(self):\n        i=identity()\n        c=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))\n        self.assertEqual(c.taxonomy_path.taxonomy_key,"btc/digital-assets/crypto/bitcoin/price-threshold")\n        self.assertEqual(c.rule_id,"crypto-price")\n\n    def test_deterministic_rule_order(self):\n        i=identity()\n        a=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))\n        b=MarketTaxonomyClassifier(tuple(reversed(rules()))).classify(i,lineage=lineage(i))\n        self.assertEqual(a.classification_hash,b.classification_hash)\n\n    def test_no_match(self):\n        i=identity("Will rainfall exceed 2 inches?","Weather")\n        with self.assertRaises(LookupError):\n            MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))\n\n    def test_duplicate_rule_id_rejected(self):\n        r=rules()[0]\n        with self.assertRaises(ValueError):\n            MarketTaxonomyClassifier((r,r))\n\n    def test_path_normalization(self):\n        p=TaxonomyPath("BTC","Digital Assets","Crypto","Bitcoin","Price Threshold")\n        self.assertEqual(p.taxonomy_key,"btc/digital-assets/crypto/bitcoin/price-threshold")\n\n    def test_lineage_required(self):\n        i=identity()\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError):\n            MarketTaxonomyClassifier(rules()).classify(i,lineage=bad)\n\n    def test_immutable(self):\n        i=identity()\n        c=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            c.rule_id="x"\n\n    def test_side_effects(self):\n        m=build_umd_098_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-098 CERTIFICATION TEST");print(" MARKET TAXONOMY CLASSIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD098))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_098_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-097 certified relationship capability consumed read-only")\n    print("[PASS] Deterministic hierarchical market taxonomy classification certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-098 CERTIFIED")\n'
UPSTREAM_MODULE='umd_097_market_relationship_graph'
UPSTREAM_VERIFIER='verify_umd_097_market_relationship_graph'
EXPORTED_NAMES=('UMD_098_REVISION', 'TaxonomyPath', 'TaxonomyRule', 'MarketTaxonomyClassification', 'MarketTaxonomyClassifier', 'build_umd_098_certification_manifest', 'verify_umd_098_market_taxonomy_classification')

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

def write_exact(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker=f"# UMD-098 exports"
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
        missing=[n for n in EXPORTED_NAMES if not hasattr(mod,n)]
        if missing:
            raise RuntimeError("UMD-098 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-098 verification returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-098 INSTALLER")
    print(" MARKET TAXONOMY CLASSIFICATION")
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
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        verify_current()
    except Exception:
        for p,previous in backups.items():
            if previous is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(previous)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-098 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-098',
        "revision":REVISION,
        "production_module":MODULE.name,
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
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-098 INSTALLATION COMPLETE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
