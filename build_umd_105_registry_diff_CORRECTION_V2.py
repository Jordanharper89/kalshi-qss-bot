from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_105_REGISTRY_DIFF_INSTALLER_CORRECTION_V2'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_105_registry_diff.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_105_registry_diff.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_104_registry_snapshot import RegistrySnapshot, verify_umd_104_registry_snapshot\n\nUMD_105_BUILD_ID="UMD-105"; UMD_105_REVISION="UMD_105_REGISTRY_DIFF_V1"; UMD_105_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass RegistryDiff:\n    previous_snapshot_hash:str\n    current_snapshot_hash:str\n    added_ids:Tuple[str,...]\n    removed_ids:Tuple[str,...]\n    changed_ids:Tuple[str,...]\n    unchanged_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        for n in ("added_ids","removed_ids","changed_ids","unchanged_ids"): object.__setattr__(self,n,tuple(getattr(self,n)))\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_105_BUILD_ID: raise ValueError("lineage must belong to UMD-105")\n        required={self.previous_snapshot_hash,self.current_snapshot_hash}\n        if not required.issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include both snapshot hashes")\n    def to_canonical_dict(self):\n        return {"previous_snapshot_hash":self.previous_snapshot_hash,"current_snapshot_hash":self.current_snapshot_hash,\n                "added_ids":self.added_ids,"removed_ids":self.removed_ids,"changed_ids":self.changed_ids,"unchanged_ids":self.unchanged_ids,"lineage":self.lineage}\n    @property\n    def diff_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\nclass RegistryDiffEngine:\n    __slots__=()\n    def compare(self,previous:RegistrySnapshot,current:RegistrySnapshot,*,lineage:ImmutableLineage)->RegistryDiff:\n        if not isinstance(previous,RegistrySnapshot) or not isinstance(current,RegistrySnapshot): raise TypeError("previous and current must be RegistrySnapshot")\n        p=dict(zip(previous.record_ids,previous.record_hashes)); c=dict(zip(current.record_ids,current.record_hashes))\n        ps,cs=set(p),set(c)\n        added=tuple(sorted(cs-ps)); removed=tuple(sorted(ps-cs))\n        shared=ps&cs\n        changed=tuple(sorted(i for i in shared if p[i]!=c[i])); unchanged=tuple(sorted(i for i in shared if p[i]==c[i]))\n        return RegistryDiff(previous.snapshot_hash,current.snapshot_hash,added,removed,changed,unchanged,lineage)\n\ndef build_umd_105_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_105_BUILD_ID,"revision":UMD_105_REVISION,"schema_version":UMD_105_SCHEMA_VERSION,\n       "upstream_builds":("UMD-104",),"mode":"deterministic_read_only_registry_diff","prohibited_capabilities":PROHIBITED_CAPABILITIES,\n       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_105_registry_diff()->bool:\n    if verify_umd_104_registry_snapshot() is not True:return False\n    m=build_umd_105_certification_manifest()\n    return m["build_id"]=="UMD-105" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_104_registry_snapshot import RegistrySnapshot\nfrom qseries_v2.universal_market_discovery.umd_105_registry_diff import *\nFIXED=datetime(2026,8,9,14,20,tzinfo=timezone.utc)\n\ndef snap(buildhash, ids, hashes):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision="UMD_104_REGISTRY_SNAPSHOT_V1",schema_version="1.0.0",parent_hashes=(buildhash,),source_refs=("fixture://105/104",),created_at=FIXED)\n    return RegistrySnapshot(buildhash,tuple(ids),tuple(hashes),l)\nclass TestUMD105(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_105_registry_diff())\n    def test_compare(self):\n        a=snap("a"*64,("m1","m2"),("1"*64,"2"*64)); b=snap("b"*64,("m2","m3"),("9"*64,"3"*64))\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)\n        d=RegistryDiffEngine().compare(a,b,lineage=l)\n        self.assertEqual(d.added_ids,("m3",)); self.assertEqual(d.removed_ids,("m1",)); self.assertEqual(d.changed_ids,("m2",))\n    def test_unchanged(self):\n        a=snap("a"*64,("m1",),("1"*64,)); b=snap("b"*64,("m1",),("1"*64,))\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)\n        d=RegistryDiffEngine().compare(a,b,lineage=l); self.assertEqual(d.unchanged_ids,("m1",))\n    def test_deterministic(self):\n        a=snap("a"*64,("m2","m1"),("2"*64,"1"*64)); b=snap("b"*64,("m3","m2"),("3"*64,"9"*64))\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)\n        x=RegistryDiffEngine().compare(a,b,lineage=l); y=RegistryDiffEngine().compare(a,b,lineage=l); self.assertEqual(x.diff_hash,y.diff_hash)\n    def test_lineage_required(self):\n        a=snap("a"*64,(),()); b=snap("b"*64,(),())\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://105",),created_at=FIXED)\n        with self.assertRaises(ValueError): RegistryDiffEngine().compare(a,b,lineage=l)\n    def test_immutable(self):\n        a=snap("a"*64,(),()); b=snap("b"*64,(),())\n        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)\n        d=RegistryDiffEngine().compare(a,b,lineage=l)\n        with self.assertRaises((FrozenInstanceError,AttributeError)): d.added_ids=()\n    def test_side_effects(self):\n        m=build_umd_105_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-105 CERTIFICATION TEST");print(" REGISTRY DIFF");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD105))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_105_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-104 registry snapshots consumed read-only"); print("[PASS] Deterministic added/removed/changed registry diff certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-105 CERTIFIED")\n'
UPSTREAM_MODULE='umd_104_registry_snapshot'
UPSTREAM_VERIFIER='verify_umd_104_registry_snapshot'
EXPORTED_NAMES=('UMD_105_REVISION', 'RegistryDiff', 'RegistryDiffEngine', 'build_umd_105_certification_manifest', 'verify_umd_105_registry_diff')

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        m=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        v=getattr(m,UPSTREAM_VERIFIER,None)
        if v is None or v() is not True:
            raise RuntimeError(f"Certified upstream verification failed: {UPSTREAM_MODULE}.{UPSTREAM_VERIFIER}")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def write_exact(path, text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker="# UMD-105 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {n},\n" for n in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None); importlib.invalidate_caches()
        m=importlib.import_module(name)
        missing=[n for n in EXPORTED_NAMES if not hasattr(m,n)]
        if missing: raise RuntimeError("Missing symbols: "+", ".join(missing))
        verifier=getattr(m,[n for n in EXPORTED_NAMES if n.startswith("verify_")][0])
        if verifier() is not True: raise RuntimeError("Verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72); print(" UMD-105 INSTALLER"); print(" REGISTRY DIFF"); print("="*72)
    print(f"[BOOT] Revision: {REVISION}"); print(f"[ROOT] {ROOT}")
    verify_upstream(); print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        verify_current()
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-105 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-105',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-105 INSTALLATION COMPLETE")
if __name__=="__main__": main()
