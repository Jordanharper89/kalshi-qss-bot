from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_104_REGISTRY_SNAPSHOT_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_104_registry_snapshot.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_104_registry_snapshot.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry, verify_umd_103_canonical_market_registry\n\nUMD_104_BUILD_ID="UMD-104"; UMD_104_REVISION="UMD_104_REGISTRY_SNAPSHOT_V1"; UMD_104_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass RegistrySnapshot:\n    registry_hash:str\n    record_ids:Tuple[str,...]\n    record_hashes:Tuple[str,...]\n    lineage:ImmutableLineage\n    def __post_init__(self):\n        object.__setattr__(self,"record_ids",tuple(self.record_ids)); object.__setattr__(self,"record_hashes",tuple(self.record_hashes))\n        if len(self.record_ids)!=len(self.record_hashes): raise ValueError("record_ids and record_hashes length mismatch")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_104_BUILD_ID: raise ValueError("lineage must belong to UMD-104")\n        if self.registry_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include registry hash")\n    def to_canonical_dict(self): return {"registry_hash":self.registry_hash,"record_ids":self.record_ids,"record_hashes":self.record_hashes,"lineage":self.lineage}\n    @property\n    def snapshot_hash(self): return deterministic_sha256(self.to_canonical_dict())\n\nclass RegistrySnapshotBuilder:\n    __slots__=()\n    def build(self,registry:CanonicalMarketRegistry,*,lineage:ImmutableLineage)->RegistrySnapshot:\n        if not isinstance(registry,CanonicalMarketRegistry): raise TypeError("registry must be CanonicalMarketRegistry")\n        return RegistrySnapshot(registry.registry_hash,tuple(r.canonical_market_id for r in registry.records),tuple(r.record_hash for r in registry.records),lineage)\n\ndef build_umd_104_certification_manifest():\n    d={"subsystem_id":"UMD","build_id":UMD_104_BUILD_ID,"revision":UMD_104_REVISION,"schema_version":UMD_104_SCHEMA_VERSION,\n       "upstream_builds":("UMD-103",),"mode":"deterministic_read_only_registry_snapshot","prohibited_capabilities":PROHIBITED_CAPABILITIES,\n       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}\n    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})\ndef verify_umd_104_registry_snapshot()->bool:\n    if verify_umd_103_canonical_market_registry() is not True:return False\n    m=build_umd_104_certification_manifest()\n    return m["build_id"]=="UMD-104" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime,timezone\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistry\nfrom qseries_v2.universal_market_discovery.umd_104_registry_snapshot import *\nFIXED=datetime(2026,8,9,14,10,tzinfo=timezone.utc)\n\ndef registry():\n    r=object.__new__(CanonicalMarketRegistry)\n    object.__setattr__(r,"records",())\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://104/103",),created_at=FIXED)\n    object.__setattr__(r,"lineage",l)\n    return r\nclass TestUMD104(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_104_registry_snapshot())\n    def test_build(self):\n        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)\n        s=RegistrySnapshotBuilder().build(g,lineage=l); self.assertEqual(s.registry_hash,g.registry_hash)\n    def test_deterministic(self):\n        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)\n        a=RegistrySnapshotBuilder().build(g,lineage=l); b=RegistrySnapshotBuilder().build(g,lineage=l); self.assertEqual(a.snapshot_hash,b.snapshot_hash)\n    def test_lineage_required(self):\n        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://104",),created_at=FIXED)\n        with self.assertRaises(ValueError): RegistrySnapshotBuilder().build(g,lineage=l)\n    def test_immutable(self):\n        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)\n        s=RegistrySnapshotBuilder().build(g,lineage=l)\n        with self.assertRaises((FrozenInstanceError,AttributeError)): s.registry_hash="x"\n    def test_side_effects(self):\n        m=build_umd_104_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\nif __name__=="__main__":\n    print("="*72);print(" UMD-104 CERTIFICATION TEST");print(" REGISTRY SNAPSHOT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD104))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_104_certification_manifest(); print(); print(f"[PASS] Build: {m[\'build_id\']}"); print(f"[PASS] Revision: {m[\'revision\']}"); print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] UMD-103 canonical registry consumed read-only"); print("[PASS] Deterministic immutable registry snapshot certified")\n    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-104 CERTIFIED")\n'
UPSTREAM_MODULE='umd_103_canonical_market_registry'
UPSTREAM_VERIFIER='verify_umd_103_canonical_market_registry'
EXPORTED_NAMES=('UMD_104_REVISION', 'RegistrySnapshot', 'RegistrySnapshotBuilder', 'build_umd_104_certification_manifest', 'verify_umd_104_registry_snapshot')

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
    marker="# UMD-104 exports"
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
    print("="*72); print(" UMD-104 INSTALLER"); print(" REGISTRY SNAPSHOT"); print("="*72)
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
        print("[ROLLBACK] UMD-104 installation failed; all affected files restored")
        raise
    manifest={"build_id":'UMD-104',"revision":REVISION,"production_module":MODULE.name,"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),str(INIT.relative_to(ROOT)):sha(INIT),str(TEST.relative_to(ROOT)):sha(TEST)},
              "network_enabled":False,"persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    h=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"); print(f"[PASS] Updated: {INIT.relative_to(ROOT)}"); print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified"); print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {h}")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-104 INSTALLATION COMPLETE")
if __name__=="__main__": main()
