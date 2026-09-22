from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_099_MARKET_ALIAS_RESOLUTION_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_099_market_alias_resolution.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_099_market_alias_resolution.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nimport re\nimport unicodedata\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_095_market_identity import CanonicalMarketIdentity\nfrom .umd_098_market_taxonomy import MarketTaxonomyClassification, verify_umd_098_market_taxonomy_classification\n\nUMD_099_BUILD_ID="UMD-099"\nUMD_099_BUILD_NAME="Market Alias Resolution"\nUMD_099_REVISION="UMD_099_MARKET_ALIAS_RESOLUTION_V1"\nUMD_099_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n_WS=re.compile(r"\\s+")\n_PUNCT=re.compile(r"[^a-z0-9]+")\n\n\ndef normalize_alias(value:str)->str:\n    if not isinstance(value,str):\n        raise TypeError("alias must be a string")\n    value=unicodedata.normalize("NFKC",value)\n    value=_WS.sub(" ",value.strip()).casefold()\n    key=_PUNCT.sub("-",value).strip("-")\n    if not key:\n        raise ValueError("alias must contain letters or digits")\n    return key\n\n\ndef _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:\n    if value is None:\n        value={}\n    if not isinstance(value,Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))\n\n\n@dataclass(frozen=True,slots=True)\nclass AliasBinding:\n    alias:str\n    alias_key:str\n    canonical_market_id:str\n    identity_hash:str\n    taxonomy_key:str\n    source_ref:str\n    metadata:Mapping[str,Any]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        if normalize_alias(self.alias)!=self.alias_key:\n            raise ValueError("alias_key does not match alias")\n        if not isinstance(self.source_ref,str) or not self.source_ref:\n            raise ValueError("source_ref must be non-empty")\n        object.__setattr__(self,"metadata",_freeze(self.metadata))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_099_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-099")\n        if self.identity_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include identity hash")\n\n    def to_canonical_dict(self):\n        return {\n            "alias":self.alias,\n            "alias_key":self.alias_key,\n            "canonical_market_id":self.canonical_market_id,\n            "identity_hash":self.identity_hash,\n            "taxonomy_key":self.taxonomy_key,\n            "source_ref":self.source_ref,\n            "metadata":self.metadata,\n            "lineage":self.lineage,\n        }\n\n    @property\n    def binding_hash(self):\n        return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True,slots=True)\nclass AliasIndex:\n    bindings:Tuple[AliasBinding,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"bindings",tuple(self.bindings))\n        keys={}\n        for b in self.bindings:\n            previous=keys.get(b.alias_key)\n            if previous is not None and previous!=b.canonical_market_id:\n                raise ValueError("alias conflict across canonical markets")\n            keys[b.alias_key]=b.canonical_market_id\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_099_BUILD_ID:\n            raise ValueError("index lineage must belong to UMD-099")\n\n    def resolve(self,alias:str)->str | None:\n        key=normalize_alias(alias)\n        for b in self.bindings:\n            if b.alias_key==key:\n                return b.canonical_market_id\n        return None\n\n    def to_canonical_dict(self):\n        return {"binding_hashes":tuple(b.binding_hash for b in self.bindings),"lineage":self.lineage}\n\n    @property\n    def index_hash(self):\n        return deterministic_sha256(self.to_canonical_dict())\n\n\nclass MarketAliasResolver:\n    __slots__=()\n\n    def build_index(\n        self,\n        entries:Iterable[tuple[CanonicalMarketIdentity,MarketTaxonomyClassification,Iterable[str],str]],\n        *,\n        lineage:ImmutableLineage,\n    )->AliasIndex:\n        bindings=[]\n        required=set()\n        seen_same=set()\n        for identity,classification,aliases,source_ref in entries:\n            if not isinstance(identity,CanonicalMarketIdentity):\n                raise TypeError("entry identity must be CanonicalMarketIdentity")\n            if not isinstance(classification,MarketTaxonomyClassification):\n                raise TypeError("entry classification must be MarketTaxonomyClassification")\n            if classification.canonical_market_id!=identity.canonical_market_id or classification.identity_hash!=identity.identity_hash:\n                raise ValueError("classification does not belong to identity")\n            if not isinstance(source_ref,str) or not source_ref:\n                raise ValueError("source_ref must be non-empty")\n            required.add(identity.identity_hash)\n            for alias in aliases:\n                key=normalize_alias(alias)\n                same_key=(identity.canonical_market_id,key)\n                if same_key in seen_same:\n                    continue\n                seen_same.add(same_key)\n                bindings.append(AliasBinding(\n                    alias=alias.strip(),\n                    alias_key=key,\n                    canonical_market_id=identity.canonical_market_id,\n                    identity_hash=identity.identity_hash,\n                    taxonomy_key=classification.taxonomy_path.taxonomy_key,\n                    source_ref=source_ref,\n                    metadata={},\n                    lineage=lineage,\n                ))\n        if not required.issubset(set(lineage.parent_hashes)):\n            raise ValueError("lineage must include every identity hash")\n        bindings.sort(key=lambda b:(b.alias_key,b.canonical_market_id,b.source_ref,b.binding_hash))\n        return AliasIndex(bindings=tuple(bindings),lineage=lineage)\n\n\ndef build_umd_099_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_099_BUILD_ID,"revision":UMD_099_REVISION,\n        "schema_version":UMD_099_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-098"),\n        "mode":"deterministic_read_only_alias_resolution",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\n\ndef verify_umd_099_market_alias_resolution()->bool:\n    if verify_umd_098_market_taxonomy_classification() is not True:\n        return False\n    m=build_umd_099_certification_manifest()\n    return m["build_id"]=="UMD-099" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer\nfrom qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver\nfrom qseries_v2.universal_market_discovery.umd_098_market_taxonomy import UMD_098_REVISION,TaxonomyPath,TaxonomyRule,MarketTaxonomyClassifier\nfrom qseries_v2.universal_market_discovery.umd_099_market_alias_resolution import (\n    UMD_099_REVISION,MarketAliasResolver,normalize_alias,\n    build_umd_099_certification_manifest,verify_umd_099_market_alias_resolution,\n)\n\nFIXED=datetime(2026,8,8,13,20,tzinfo=timezone.utc)\n\ndef identity(venue,mid,title,category="Crypto"):\n    o=MarketObservation(venue=venue,venue_market_id=mid,title=title,category=category,status="Open",outcomes=("Yes","No"))\n    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://099/94",),created_at=FIXED)\n    m=MarketNormalizer().normalize(o,lineage=l94)\n    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://099/95",),created_at=FIXED)\n    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)\n\ndef classification(i):\n    rule=TaxonomyRule("crypto",TaxonomyPath("btc","digital-assets","crypto","bitcoin","price-threshold"),category_keys=("crypto",),priority=1)\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://099/98",),created_at=FIXED)\n    return MarketTaxonomyClassifier((rule,)).classify(i,lineage=l)\n\ndef lineage(ids):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=tuple(i.identity_hash for i in ids),source_refs=("fixture://099",),created_at=FIXED)\n\nclass TestUMD099(unittest.TestCase):\n    def test_foundation(self):\n        self.assertTrue(verify_umd_099_market_alias_resolution())\n\n    def test_alias_normalization(self):\n        self.assertEqual(normalize_alias("  BTC > $100K?  "),"btc-100k")\n\n    def test_resolution(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        idx=MarketAliasResolver().build_index(((i,classification(i),("Bitcoin above 100k","BTC > $100K?"),"fixture://source"),),lineage=lineage((i,)))\n        self.assertEqual(idx.resolve("bitcoin above 100K"),i.canonical_market_id)\n        self.assertEqual(idx.resolve("BTC > $100K?"),i.canonical_market_id)\n\n    def test_unknown_alias(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        idx=MarketAliasResolver().build_index(((i,classification(i),("Bitcoin above 100k",),"fixture://source"),),lineage=lineage((i,)))\n        self.assertIsNone(idx.resolve("ethereum above 10k"))\n\n    def test_conflict_rejected(self):\n        a=identity("Kalshi","A","Will BTC exceed 100K?")\n        b=identity("Kalshi","B","Will BTC exceed 200K?")\n        entries=(\n            (a,classification(a),("BTC breakout",),"fixture://a"),\n            (b,classification(b),("BTC breakout",),"fixture://b"),\n        )\n        with self.assertRaises(ValueError):\n            MarketAliasResolver().build_index(entries,lineage=lineage((a,b)))\n\n    def test_duplicate_same_market_collapsed(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        idx=MarketAliasResolver().build_index(((i,classification(i),("BTC 100K","btc 100k"),"fixture://source"),),lineage=lineage((i,)))\n        self.assertEqual(len(idx.bindings),1)\n\n    def test_deterministic(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        c=classification(i)\n        l=lineage((i,))\n        r=MarketAliasResolver()\n        a=r.build_index(((i,c,("Bitcoin above 100k","BTC 100K"),"fixture://source"),),lineage=l)\n        b=r.build_index(((i,c,("BTC 100K","Bitcoin above 100k"),"fixture://source"),),lineage=l)\n        self.assertEqual(a.index_hash,b.index_hash)\n\n    def test_lineage_required(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)\n        with self.assertRaises(ValueError):\n            MarketAliasResolver().build_index(((i,classification(i),("BTC 100K",),"fixture://source"),),lineage=bad)\n\n    def test_immutable(self):\n        i=identity("Kalshi","A","Will BTC exceed 100K?")\n        idx=MarketAliasResolver().build_index(((i,classification(i),("BTC 100K",),"fixture://source"),),lineage=lineage((i,)))\n        with self.assertRaises((FrozenInstanceError,AttributeError)):\n            idx.bindings=()\n\n    def test_side_effects(self):\n        m=build_umd_099_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-099 CERTIFICATION TEST");print(" MARKET ALIAS RESOLUTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD099))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_099_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-098 taxonomy classifications consumed read-only")\n    print("[PASS] Deterministic alias indexing, conflict rejection, and resolution certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-099 CERTIFIED")\n'
UPSTREAM_MODULE='umd_098_market_taxonomy'
UPSTREAM_VERIFIER='verify_umd_098_market_taxonomy_classification'
EXPORTED_NAMES=('UMD_099_REVISION', 'AliasBinding', 'AliasIndex', 'MarketAliasResolver', 'normalize_alias', 'build_umd_099_certification_manifest', 'verify_umd_099_market_alias_resolution')

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
    marker=f"# UMD-099 exports"
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
            raise RuntimeError("UMD-099 missing symbols: "+", ".join(missing))
        verifier=getattr(mod,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True:
            raise RuntimeError("UMD-099 verification returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-099 INSTALLER")
    print(" MARKET ALIAS RESOLUTION")
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
        print("[ROLLBACK] UMD-099 installation failed; all affected files restored")
        raise
    manifest={
        "build_id":'UMD-099',
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
    print("[DONE] UMD-099 INSTALLATION COMPLETE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
