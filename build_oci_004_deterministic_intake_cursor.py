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

BUILD_ID = 'OCI-004'
TITLE = 'DETERMINISTIC INTAKE CURSOR'
REVISION = 'OCI_004_PRODUCTION_V1'
MODULE = PACKAGE / 'oci_004_intake_cursor.py'
TEST = ROOT / 'test_oci_004_deterministic_intake_cursor.py'
EXPORTS = ('OCI_004_BUILD_ID', 'OCI_004_REVISION', 'IntakeCursor', 'build_genesis_cursor', 'advance_cursor', 'verify_cursor', 'build_oci_004_certification_manifest', 'verify_oci_004_deterministic_intake_cursor')

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any
from .oci_003_postgresql_read_contract import verify_oci_003_postgresql_read_only_intake_contract

OCI_004_BUILD_ID="OCI-004"
OCI_004_REVISION="OCI_004_DETERMINISTIC_INTAKE_CURSOR_V1"

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class IntakeCursor:
    stream_id:str
    cursor_column:str
    cursor_value:int
    last_source_hash:str
    batch_sequence:int
    checkpoint_parent_hash:str
    cursor_hash:str

def build_genesis_cursor(stream_id:str,cursor_column:str)->IntakeCursor:
    if not stream_id or not cursor_column:raise ValueError("stream and cursor column required")
    raw={"stream_id":stream_id,"cursor_column":cursor_column,"cursor_value":0,"last_source_hash":"0"*64,
         "batch_sequence":0,"checkpoint_parent_hash":"0"*64}
    return IntakeCursor(**raw,cursor_hash=_hash(raw))

def advance_cursor(previous:IntakeCursor,new_value:int,last_source_hash:str)->IntakeCursor:
    if new_value <= previous.cursor_value:raise ValueError("cursor must advance monotonically")
    if len(last_source_hash)!=64:raise ValueError("source hash must be sha256 hex")
    int(last_source_hash,16)
    raw={"stream_id":previous.stream_id,"cursor_column":previous.cursor_column,"cursor_value":int(new_value),
         "last_source_hash":last_source_hash,"batch_sequence":previous.batch_sequence+1,
         "checkpoint_parent_hash":previous.cursor_hash}
    return IntakeCursor(**raw,cursor_hash=_hash(raw))

def verify_cursor(cursor:IntakeCursor)->bool:
    raw={k:v for k,v in asdict(cursor).items() if k!="cursor_hash"}
    try:
        int(cursor.last_source_hash,16); int(cursor.checkpoint_parent_hash,16)
    except ValueError:return False
    return len(cursor.last_source_hash)==64 and len(cursor.checkpoint_parent_hash)==64 and cursor.cursor_hash==_hash(raw)

def build_oci_004_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_004_BUILD_ID,"revision":OCI_004_REVISION,"upstream":"OCI-003",
         "cursor_model":"monotonic_hash_chained","checkpoint_storage_contract":"append_only",
         "destructive_checkpoint_update_allowed":False,"execution_enabled":False,"publication_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_004_deterministic_intake_cursor()->bool:
    a=build_genesis_cursor("live_shadow","sequence_id")
    b=advance_cursor(a,1,"a"*64)
    return verify_oci_003_postgresql_read_only_intake_contract() and verify_cursor(a) and verify_cursor(b) and b.checkpoint_parent_hash==a.cursor_hash
"""
TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import *

class TestOCI004(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_oci_004_deterministic_intake_cursor())
    def test_genesis_deterministic(self):
        self.assertEqual(build_genesis_cursor("s","id").cursor_hash,build_genesis_cursor("s","id").cursor_hash)
    def test_advance_hash_chain(self):
        g=build_genesis_cursor("s","id");a=advance_cursor(g,5,"a"*64)
        self.assertEqual(a.checkpoint_parent_hash,g.cursor_hash);self.assertEqual(a.batch_sequence,1)
    def test_non_monotonic_rejected(self):
        g=build_genesis_cursor("s","id")
        with self.assertRaises(ValueError):advance_cursor(g,0,"a"*64)
    def test_bad_hash_rejected(self):
        g=build_genesis_cursor("s","id")
        with self.assertRaises(ValueError):advance_cursor(g,1,"bad")

if __name__=="__main__":
    print("="*72);print(" OCI-004 CERTIFICATION TEST");print(" DETERMINISTIC INTAKE CURSOR");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI004))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Monotonic hash-chained cursor/checkpoint semantics certified")
    print("[DONE] OCI-004 CERTIFIED")
"""

def verify_upstream() -> None:
    p = PACKAGE / "oci_003_postgresql_read_contract.py"
    t = ROOT / "test_oci_003_postgresql_read_only_intake_contract.py"
    if not p.is_file() or not t.is_file():
        raise RuntimeError("Certified OCI-003 missing")
    sys.path.insert(0, str(ROOT))
    try:
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_003_postgresql_read_contract")
        if m.verify_oci_003_postgresql_read_only_intake_contract() is not True:
            raise RuntimeError("OCI-003 verification failed")
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
