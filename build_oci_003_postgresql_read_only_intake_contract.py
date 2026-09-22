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

BUILD_ID = 'OCI-003'
TITLE = 'POSTGRESQL READ-ONLY INTAKE CONTRACT'
REVISION = 'OCI_003_PRODUCTION_V1'
MODULE = PACKAGE / 'oci_003_postgresql_read_contract.py'
TEST = ROOT / 'test_oci_003_postgresql_read_only_intake_contract.py'
EXPORTS = ('OCI_003_BUILD_ID', 'OCI_003_REVISION', 'PostgreSQLReadConfig', 'ReadOnlyQuery', 'build_incremental_read_query', 'read_only_session_commands', 'verify_read_only_sql', 'build_oci_003_certification_manifest', 'verify_oci_003_postgresql_read_only_intake_contract')

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json, re
from types import MappingProxyType
from typing import Mapping, Any, Sequence
from .oci_001_foundation import verify_oci_001_continuous_intake_foundation
from .oci_002_upstream_boundary import verify_oci_002_upstream_boundary_inventory

OCI_003_BUILD_ID="OCI-003"
OCI_003_REVISION="OCI_003_POSTGRESQL_READ_ONLY_INTAKE_CONTRACT_V1"
_IDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
FORBIDDEN_SQL=("insert","update","delete","alter","drop","truncate","create","grant","revoke","copy","call","do")

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class PostgreSQLReadConfig:
    host:str
    port:int
    database:str
    user:str
    connect_timeout_seconds:int=5
    statement_timeout_ms:int=5000
    application_name:str="oracle_continuous_intake"

    def __post_init__(self):
        if not self.host or not self.database or not self.user: raise ValueError("host/database/user required")
        if not 1 <= self.port <= 65535: raise ValueError("invalid port")
        if self.connect_timeout_seconds <= 0 or self.statement_timeout_ms <= 0: raise ValueError("timeouts must be positive")

    def safe_dict(self):
        return MappingProxyType(asdict(self))

@dataclass(frozen=True)
class ReadOnlyQuery:
    sql:str
    params:tuple[object,...]
    query_hash:str

def build_incremental_read_query(schema:str,table:str,cursor_column:str,after_value:object,limit:int=500)->ReadOnlyQuery:
    for value in (schema,table,cursor_column):
        if not _IDENT.fullmatch(value): raise ValueError("unsafe SQL identifier")
    if not 1 <= limit <= 10000: raise ValueError("limit outside certified bound")
    sql=f'SELECT * FROM "{schema}"."{table}" WHERE "{cursor_column}" > %s ORDER BY "{cursor_column}" ASC LIMIT %s'
    lowered=sql.lower()
    if any(re.search(r"\b"+word+r"\b",lowered) for word in FORBIDDEN_SQL): raise ValueError("write SQL forbidden")
    params=(after_value,limit)
    return ReadOnlyQuery(sql,params,_hash({"sql":sql,"params":params}))

def read_only_session_commands(statement_timeout_ms:int)->tuple[str,...]:
    if statement_timeout_ms <= 0: raise ValueError("timeout must be positive")
    return (
        "BEGIN READ ONLY",
        f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}",
        "SET LOCAL idle_in_transaction_session_timeout = 10000",
    )

def verify_read_only_sql(sql:str)->bool:
    stripped=sql.strip().lower()
    return stripped.startswith("select ") and not any(re.search(r"\b"+w+r"\b",stripped) for w in FORBIDDEN_SQL)

def build_oci_003_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_003_BUILD_ID,"revision":OCI_003_REVISION,"upstream_builds":("OCI-001","OCI-002"),
         "postgresql_read_enabled":True,"postgresql_write_enabled":False,"read_only_transaction_required":True,
         "network_listener_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_003_postgresql_read_only_intake_contract()->bool:
    q=build_incremental_read_query("public","oracle_live_shadow","sequence_id",0,10)
    m=build_oci_003_certification_manifest()
    return (verify_oci_001_continuous_intake_foundation()
            and verify_oci_002_upstream_boundary_inventory()
            and verify_read_only_sql(q.sql)
            and read_only_session_commands(5000)[0]=="BEGIN READ ONLY"
            and m["postgresql_read_enabled"] and not m["postgresql_write_enabled"] and not m["execution_enabled"])
"""
TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_003_postgresql_read_contract import *

class TestOCI003(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_oci_003_postgresql_read_only_intake_contract())
    def test_query_is_parameterized(self):
        q=build_incremental_read_query("public","oracle_live_shadow","sequence_id",123,50)
        self.assertIn("%s",q.sql);self.assertEqual(q.params,(123,50));self.assertTrue(verify_read_only_sql(q.sql))
    def test_identifier_injection_rejected(self):
        with self.assertRaises(ValueError):build_incremental_read_query("public;drop table x","t","id",0)
    def test_limit_bounded(self):
        with self.assertRaises(ValueError):build_incremental_read_query("public","t","id",0,10001)
    def test_write_sql_rejected(self):
        self.assertFalse(verify_read_only_sql("DELETE FROM x"))
        self.assertFalse(verify_read_only_sql("SELECT 1; DROP TABLE x"))
    def test_read_only_transaction(self):
        self.assertEqual(read_only_session_commands(5000)[0],"BEGIN READ ONLY")

if __name__=="__main__":
    print("="*72);print(" OCI-003 CERTIFICATION TEST");print(" POSTGRESQL READ-ONLY INTAKE CONTRACT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI003))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Parameterized bounded SELECT-only PostgreSQL contract certified")
    print("[DONE] OCI-003 CERTIFIED")
"""

def verify_upstream() -> None:
    p = PACKAGE / "oci_002_upstream_boundary.py"
    t = ROOT / "test_oci_002_upstream_boundary_inventory.py"
    if not p.is_file() or not t.is_file():
        raise RuntimeError("Certified OCI-002 missing")
    sys.path.insert(0, str(ROOT))
    try:
        m = importlib.import_module("qseries_v2.oracle_continuous_intake.oci_002_upstream_boundary")
        if m.verify_oci_002_upstream_boundary_inventory() is not True:
            raise RuntimeError("OCI-002 verification failed")
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
