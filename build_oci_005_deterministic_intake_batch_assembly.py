from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "qseries_v2").is_dir():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_continuous_intake"
INIT = PACKAGE / "__init__.py"

def write_exact(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker: str, module_name: str, exports: tuple[str, ...]) -> None:
    current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block = marker + "\nfrom ." + module_name + " import (\n"
    block += "".join(f"    {name},\n" for name in exports)
    block += ")\n"
    write_exact(INIT, current.rstrip() + ("\n\n" if current.strip() else "") + block)

def run_test(test_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(test_path)], cwd=str(ROOT), text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Certification test failed: {test_path.name}")

BUILD_ID = 'OCI-005'
TITLE = 'DETERMINISTIC INTAKE BATCH ASSEMBLY'
REVISION = 'OCI_005_PRODUCTION_V1'
MODULE = PACKAGE / 'oci_005_intake_batch.py'
TEST = ROOT / 'test_oci_005_deterministic_intake_batch_assembly.py'
EXPORTS = ('OCI_005_BUILD_ID', 'OCI_005_REVISION', 'IntakeRecord', 'IntakeBatch', 'assemble_intake_batch', 'verify_batch', 'build_oci_005_certification_manifest', 'verify_oci_005_deterministic_intake_batch_assembly')

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any, Iterable
from .oci_001_foundation import OCIIntakeLineage
from .oci_004_intake_cursor import IntakeCursor, advance_cursor, verify_cursor, verify_oci_004_deterministic_intake_cursor

OCI_005_BUILD_ID="OCI-005"
OCI_005_REVISION="OCI_005_DETERMINISTIC_INTAKE_BATCH_ASSEMBLY_V1"

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()

@dataclass(frozen=True)
class IntakeRecord:
    cursor_value:int
    source_ref:str
    payload:Mapping[str,Any]
    source_hash:str

    @staticmethod
    def from_payload(cursor_value:int,source_ref:str,payload:Mapping[str,Any])->"IntakeRecord":
        if cursor_value < 0 or not source_ref:raise ValueError("invalid source identity")
        canonical={str(k):payload[k] for k in sorted(payload)}
        h=_hash({"cursor_value":cursor_value,"source_ref":source_ref,"payload":canonical})
        return IntakeRecord(cursor_value,source_ref,MappingProxyType(canonical),h)

@dataclass(frozen=True)
class IntakeBatch:
    stream_id:str
    batch_sequence:int
    records:tuple[IntakeRecord,...]
    start_cursor_hash:str
    end_cursor:IntakeCursor
    lineage:tuple[OCIIntakeLineage,...]
    batch_hash:str

def assemble_intake_batch(cursor:IntakeCursor,records:Iterable[IntakeRecord],observed_at:str)->IntakeBatch:
    if not verify_cursor(cursor):raise ValueError("invalid starting cursor")
    ordered=tuple(sorted(records,key=lambda r:(r.cursor_value,r.source_hash)))
    if not ordered:raise ValueError("empty intake batch")
    values=[r.cursor_value for r in ordered]
    if any(v <= cursor.cursor_value for v in values):raise ValueError("records must be after cursor")
    if len(values)!=len(set(values)):raise ValueError("duplicate cursor value")
    end=advance_cursor(cursor,ordered[-1].cursor_value,ordered[-1].source_hash)
    lineage=tuple(OCIIntakeLineage("postgresql",r.source_ref,r.source_hash,observed_at,i) for i,r in enumerate(ordered,start=1))
    raw={"stream_id":cursor.stream_id,"batch_sequence":end.batch_sequence,
         "record_hashes":[r.source_hash for r in ordered],"start_cursor_hash":cursor.cursor_hash,
         "end_cursor_hash":end.cursor_hash,"lineage_hashes":[x.lineage_hash for x in lineage]}
    return IntakeBatch(cursor.stream_id,end.batch_sequence,ordered,cursor.cursor_hash,end,lineage,_hash(raw))

def verify_batch(batch:IntakeBatch)->bool:
    if not batch.records or not verify_cursor(batch.end_cursor):return False
    raw={"stream_id":batch.stream_id,"batch_sequence":batch.batch_sequence,
         "record_hashes":[r.source_hash for r in batch.records],"start_cursor_hash":batch.start_cursor_hash,
         "end_cursor_hash":batch.end_cursor.cursor_hash,"lineage_hashes":[x.lineage_hash for x in batch.lineage]}
    return batch.batch_hash==_hash(raw) and len(batch.records)==len(batch.lineage)

def build_oci_005_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_005_BUILD_ID,"revision":OCI_005_REVISION,"upstream_builds":("OCI-001","OCI-004"),
         "capability_slice":"postgresql_live_shadow_to_deterministic_intake_batch",
         "next_boundary":"OI_UMD_OML_read_only_binding","network_write_enabled":False,
         "postgresql_write_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_005_deterministic_intake_batch_assembly()->bool:
    from .oci_004_intake_cursor import build_genesis_cursor
    g=build_genesis_cursor("live_shadow","sequence_id")
    recs=(IntakeRecord.from_payload(1,"row:1",{"x":1}),IntakeRecord.from_payload(2,"row:2",{"x":2}))
    b=assemble_intake_batch(g,recs,"2026-08-12T00:00:00Z")
    m=build_oci_005_certification_manifest()
    return verify_oci_004_deterministic_intake_cursor() and verify_batch(b) and not m["postgresql_write_enabled"] and not m["execution_enabled"]
"""
TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import build_genesis_cursor
from qseries_v2.oracle_continuous_intake.oci_005_intake_batch import *

class TestOCI005(unittest.TestCase):
    def setUp(self):self.g=build_genesis_cursor("live_shadow","sequence_id")
    def test_verifier(self):self.assertTrue(verify_oci_005_deterministic_intake_batch_assembly())
    def test_order_independent_assembly(self):
        a=IntakeRecord.from_payload(1,"row:1",{"b":2,"a":1});b=IntakeRecord.from_payload(2,"row:2",{"x":2})
        x=assemble_intake_batch(self.g,(b,a),"2026-08-12T00:00:00Z")
        y=assemble_intake_batch(self.g,(a,b),"2026-08-12T00:00:00Z")
        self.assertEqual(x.batch_hash,y.batch_hash);self.assertTrue(verify_batch(x))
    def test_duplicate_cursor_rejected(self):
        a=IntakeRecord.from_payload(1,"row:1",{"x":1});b=IntakeRecord.from_payload(1,"row:2",{"x":2})
        with self.assertRaises(ValueError):assemble_intake_batch(self.g,(a,b),"2026-08-12T00:00:00Z")
    def test_replay_before_cursor_rejected(self):
        from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import advance_cursor
        c=advance_cursor(self.g,5,"a"*64);r=IntakeRecord.from_payload(5,"row:5",{"x":5})
        with self.assertRaises(ValueError):assemble_intake_batch(c,(r,),"2026-08-12T00:00:00Z")
    def test_manifest_points_to_next_capability(self):
        self.assertEqual(build_oci_005_certification_manifest()["next_boundary"],"OI_UMD_OML_read_only_binding")

if __name__=="__main__":
    print("="*72);print(" OCI-005 CERTIFICATION TEST");print(" DETERMINISTIC INTAKE BATCH ASSEMBLY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI005))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] PostgreSQL/live-shadow observations assemble into deterministic replayable batches")
    print("[PASS] Next certified boundary: OI -> UMD -> OML read-only binding")
    print("[DONE] OCI-005 CERTIFIED")
"""

def verify_upstream() -> None:
    p = PACKAGE / "oci_004_intake_cursor.py"
    t = ROOT / "test_oci_004_deterministic_intake_cursor.py"
    if not p.is_file() or not t.is_file():
        raise RuntimeError("Certified OCI-004 missing")
    sys.path.insert(0, str(ROOT))
    try:
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_004_intake_cursor")
        if m.verify_oci_004_deterministic_intake_cursor() is not True:
            raise RuntimeError("OCI-004 verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))


def main() -> None:
    print("=" * 72)
    print(f" {BUILD_ID} INSTALLER")
    print(f" {TITLE}")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init(f"# {BUILD_ID} exports", MODULE.stem, EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
        compile(INIT.read_text(encoding="utf-8"), str(INIT), "exec")
        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_continuous_intake." + MODULE.stem
            sys.modules.pop(name, None)
            mod = importlib.import_module(name)
            missing = [name for name in EXPORTS if not hasattr(mod, name)]
            if missing:
                raise RuntimeError("Missing production symbols: " + ", ".join(missing))
            verifier = getattr(mod, [n for n in EXPORTS if n.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for path, old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)
        importlib.invalidate_caches()
        print(f"[ROLLBACK] {BUILD_ID} installation failed; affected files restored")
        raise

    manifest = {
        "build_id": BUILD_ID,
        "revision": REVISION,
        "module": str(MODULE.relative_to(ROOT)),
        "test": TEST.name,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
        },
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print(f"[PASS] Deterministic install hash: {digest}")
    print(f"[DONE] {BUILD_ID} INSTALLATION AND CERTIFICATION COMPLETE")

if __name__ == "__main__":
    main()
