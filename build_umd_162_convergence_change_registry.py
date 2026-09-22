from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_162_CONVERGENCE_CHANGE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_162_convergence_change_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_162_convergence_change_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_161_convergence_diff import ConvergenceDiff,verify_umd_161_convergence_diff\n\nUMD_162_BUILD_ID="UMD-162"\nUMD_162_REVISION="UMD_162_CONVERGENCE_CHANGE_REGISTRY_V1"\nUMD_162_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\nCHANGE_TYPES=("convergence-added","convergence-removed","convergence-composition-changed")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceChangeRecord:\n    change_type:str\n    canonical_market_id:str\n    diff_hash:str\n    added_change_hashes:Tuple[str,...]\n    removed_change_hashes:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"added_change_hashes",tuple(self.added_change_hashes))\n        object.__setattr__(self,"removed_change_hashes",tuple(self.removed_change_hashes))\n        if self.change_type not in CHANGE_TYPES:\n            raise ValueError("unsupported convergence change type")\n        if not self.canonical_market_id:\n            raise ValueError("canonical_market_id must be non-empty")\n        if self.added_change_hashes!=tuple(sorted(set(self.added_change_hashes))):\n            raise ValueError("added_change_hashes must be unique and sorted")\n        if self.removed_change_hashes!=tuple(sorted(set(self.removed_change_hashes))):\n            raise ValueError("removed_change_hashes must be unique and sorted")\n\n    @property\n    def record_hash(self)->str:\n        return deterministic_sha256({\n            "change_type":self.change_type,\n            "canonical_market_id":self.canonical_market_id,\n            "diff_hash":self.diff_hash,\n            "added_change_hashes":self.added_change_hashes,\n            "removed_change_hashes":self.removed_change_hashes,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceChangeRegistry:\n    diffs:Tuple[ConvergenceDiff,...]\n    records:Tuple[ConvergenceChangeRecord,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    type_index:Mapping[str,Tuple[str,...]]\n    source_change_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"diffs",tuple(self.diffs))\n        object.__setattr__(self,"records",tuple(self.records))\n        for name in ("market_index","type_index","source_change_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.diffs!=tuple(sorted(self.diffs,key=lambda d:d.diff_hash)):\n            raise ValueError("diffs must be deterministically sorted")\n        if self.records!=tuple(sorted(\n            self.records,key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash)\n        )):\n            raise ValueError("records must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_162_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-162")\n        required={d.diff_hash for d in self.diffs}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every convergence diff hash")\n\n    def record_hashes_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def markets_for_type(self,change_type:str)->Tuple[str,...]:\n        return self.type_index.get(change_type,())\n\n    def markets_for_source_change(self,change_hash:str)->Tuple[str,...]:\n        return self.source_change_index.get(change_hash,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "diff_hashes":tuple(d.diff_hash for d in self.diffs),\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "market_index":self.market_index,\n            "type_index":self.type_index,\n            "source_change_index":self.source_change_index,\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceChangeRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        diffs:Iterable[ConvergenceDiff],\n        *,\n        lineage_factory,\n    )->ConvergenceChangeRegistry:\n        values=tuple(diffs)\n        if any(not isinstance(d,ConvergenceDiff) for d in values):\n            raise TypeError("diffs must contain ConvergenceDiff")\n        values=tuple(sorted(values,key=lambda d:d.diff_hash))\n\n        records=[]\n        market={}\n        type_index={}\n        source={}\n\n        def add(record):\n            records.append(record)\n            market.setdefault(record.canonical_market_id,[]).append(record.record_hash)\n            type_index.setdefault(record.change_type,[]).append(record.canonical_market_id)\n            for change_hash in record.added_change_hashes+record.removed_change_hashes:\n                source.setdefault(change_hash,[]).append(record.canonical_market_id)\n\n        for diff in values:\n            for market_id in diff.added_market_ids:\n                add(ConvergenceChangeRecord(\n                    "convergence-added",market_id,diff.diff_hash,(),()\n                ))\n            for market_id in diff.removed_market_ids:\n                add(ConvergenceChangeRecord(\n                    "convergence-removed",market_id,diff.diff_hash,(),()\n                ))\n            for changed in diff.changed_markets:\n                add(ConvergenceChangeRecord(\n                    "convergence-composition-changed",\n                    changed.canonical_market_id,\n                    diff.diff_hash,\n                    changed.added_change_hashes,\n                    changed.removed_change_hashes,\n                ))\n\n        records.sort(key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash))\n        for index in (market,type_index,source):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        lineage=lineage_factory(tuple(d.diff_hash for d in values))\n        return ConvergenceChangeRegistry(\n            values,tuple(records),market,type_index,source,lineage\n        )\n\ndef build_umd_162_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_162_BUILD_ID,"revision":UMD_162_REVISION,\n        "schema_version":UMD_162_SCHEMA_VERSION,"upstream_builds":("UMD-161",),\n        "mode":"deterministic_read_only_convergence_change_registry",\n        "change_types":CHANGE_TYPES,\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_162_convergence_change_registry()->bool:\n    if verify_umd_161_convergence_diff() is not True:\n        return False\n    m=build_umd_162_certification_manifest()\n    return m["build_id"]=="UMD-162" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_161_convergence_diff import ConvergenceMarketChange,ConvergenceDiff\nfrom qseries_v2.universal_market_discovery.umd_162_convergence_change_registry import *\n\nFIXED=datetime(2026,8,10,13,20,tzinfo=timezone.utc)\nC1="1"*64; C2="2"*64; C3="3"*64\n\ndef diff(seed,added=(),removed=(),changed=()):\n    before=seed*64\n    after=chr(ord(seed)+1)*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-161",revision="UMD_161_CONVERGENCE_DIFF_V1",\n        schema_version="1.0.0",parent_hashes=(before,after),\n        source_refs=("fixture://162/161",),created_at=FIXED\n    )\n    return ConvergenceDiff(before,after,tuple(added),tuple(removed),tuple(changed),l)\n\ndef lf(parents):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-162",revision=UMD_162_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,\n        source_refs=("fixture://162",),created_at=FIXED\n    )\n\nclass TestUMD162(unittest.TestCase):\n    def setUp(self):\n        changed=ConvergenceMarketChange(\n            "m3",(C1,C2),(C1,C2,C3),(C3,),()\n        )\n        self.d=diff("a",added=("m1",),removed=("m2",),changed=(changed,))\n        self.r=ConvergenceChangeRegistryBuilder().build((self.d,),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_162_convergence_change_registry())\n    def test_change_types(self):\n        self.assertEqual(set(r.change_type for r in self.r.records),set(CHANGE_TYPES))\n    def test_market_query(self):\n        self.assertEqual(len(self.r.record_hashes_for_market("m3")),1)\n    def test_type_query(self):\n        self.assertEqual(self.r.markets_for_type("convergence-added"),("m1",))\n        self.assertEqual(self.r.markets_for_type("convergence-removed"),("m2",))\n    def test_source_change_query(self):\n        self.assertEqual(self.r.markets_for_source_change(C3),("m3",))\n    def test_unknown(self):\n        self.assertEqual(self.r.record_hashes_for_market("missing"),())\n        self.assertEqual(self.r.markets_for_source_change("9"*64),())\n    def test_deterministic(self):\n        x=ConvergenceChangeRegistryBuilder().build((self.d,),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ConvergenceChangeRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(x.records,())\n    def test_bad_diff(self):\n        with self.assertRaises(TypeError):\n            ConvergenceChangeRegistryBuilder().build((object(),),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_162_certification_manifest()\n        self.assertEqual(m["change_types"],CHANGE_TYPES)\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-162 CERTIFICATION TEST");print(" CONVERGENCE CHANGE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD162))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_162_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Added, removed, and composition-changed convergence registry queries certified")\n    print("[PASS] Convergence evolution remains deterministic, read-only, structural, and non-predictive")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-162 CERTIFIED")\n'
UPSTREAM_MODULE='umd_161_convergence_diff'
UPSTREAM_VERIFIER='verify_umd_161_convergence_diff'
EXPORTED_NAMES=('UMD_162_REVISION', 'CHANGE_TYPES', 'ConvergenceChangeRecord', 'ConvergenceChangeRegistry', 'ConvergenceChangeRegistryBuilder', 'build_umd_162_certification_manifest', 'verify_umd_162_convergence_change_registry')

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
    marker="# UMD-162 exports"
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
            raise RuntimeError("UMD-162 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-162 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-162 INSTALLER")
    print(" CONVERGENCE CHANGE REGISTRY")
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
        print("[ROLLBACK] UMD-162 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-162',
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
    print("[DONE] UMD-162 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
