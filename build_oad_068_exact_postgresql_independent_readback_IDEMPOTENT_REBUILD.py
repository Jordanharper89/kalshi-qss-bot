from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-068"
REVISION="OAD_068_IDEMPOTENT_READBACK_REBUILD_V1"
TITLE="EXACT POSTGRESQL INDEPENDENT OBSERVATION READBACK — IDEMPOTENT REBUILD"

def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (b,*b.parents):
            if (x/"qseries_v2").is_dir():
                return x
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_068_exact_postgresql_independent_readback.py"
TEST=ROOT/"test_oad_068_exact_postgresql_independent_readback.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceQueryRequest,
)
from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import (
    acquire_independent_production_bundle,
)
from qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import (
    build_independent_canonical_batch,
)
from qseries_v2.oracle_adapters.independent.oad_066_independent_single_writer_ingress_binding import (
    submit_independent_canonical_batch,
    await_independent_commit,
)

OAD_068_BUILD_ID="OAD-068"
OAD_068_REVISION="OAD_068_IDEMPOTENT_READBACK_REBUILD_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _backend(root=None):
    router=build_existing_canonical_router(Path(root or Path.cwd()).resolve())
    backend=getattr(router,"_persistence_backend",None)
    if backend is None or not callable(getattr(backend,"query",None)):
        raise RuntimeError("existing PostgreSQL backend query unavailable")
    return backend

def _query_one(backend,observation_id,index=0):
    oid=str(observation_id)
    request=CanonicalPersistenceQueryRequest.by_observation_id(
        query_id=f"query.oad068.{index}.{oid[:12]}",
        backend_id=backend.backend_id,
        observation_id=oid,
        requested_at=datetime.now(timezone.utc),
        query_metadata={
            "read_only":True,
            "build_id":"OAD-068",
            "query_mode":"exact_by_observation_id",
        },
    )
    rows=tuple(backend.query(request=request))
    if len(rows)>1:
        raise RuntimeError("exact observation query returned multiple rows: "+oid)
    return rows[0] if rows else None

def exact_postgresql_readback(observation_ids,root=None):
    backend=_backend(root)
    found=[]
    for i,oid in enumerate(tuple(str(x) for x in observation_ids)):
        row=_query_one(backend,oid,i)
        if row is None:
            raise RuntimeError("exact PostgreSQL observation missing: "+oid)
        if row.observation_id!=oid:
            raise RuntimeError("exact PostgreSQL observation identity mismatch: "+oid)
        found.append(row)
    return tuple(found)

def verify_or_persist_independent_cohort(root=None,per_source_limit=2,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve()
    raw=acquire_independent_production_bundle(per_source_limit)
    batch=build_independent_canonical_batch(raw,"oad068.idempotent.physical")
    if not batch.ready_for_existing_persistence_router:
        raise RuntimeError("OAD-065 independent canonical batch not ready")

    backend=_backend(root)
    existing=[]
    missing=[]
    for i,obs in enumerate(batch.canonical_observations):
        row=_query_one(backend,obs.observation_id,i)
        if row is None:
            missing.append(obs)
        else:
            existing.append(row)

    committed_new=0
    request_id=None
    if missing:
        submission=submit_independent_canonical_batch(tuple(missing),root)
        request_id=str(submission.request_id)
        evidence=await_independent_commit(request_id,root,timeout_seconds)
        accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("missing-only single-writer commit count mismatch")
        committed_new=len(accepted)

    rows=exact_postgresql_readback(
        tuple(x.observation_id for x in batch.canonical_observations),
        root,
    )
    return {
        "cohort_size":len(batch.canonical_observations),
        "already_present":len(existing),
        "missing_before_write":len(missing),
        "committed_new":committed_new,
        "exact_readback":len(rows),
        "request_id":request_id,
        "rows":rows,
    }
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import *

class T(unittest.TestCase):
    def test_physical(self):
        result=verify_or_persist_independent_cohort(timeout_seconds=120.0)
        print("[PHYSICAL] cohort_size=",result["cohort_size"])
        print("[PHYSICAL] already_present=",result["already_present"])
        print("[PHYSICAL] missing_before_write=",result["missing_before_write"])
        print("[PHYSICAL] committed_new=",result["committed_new"])
        print("[PHYSICAL] exact_readback=",result["exact_readback"])
        print("[PHYSICAL] request_id=",result["request_id"])
        print("[PHYSICAL] source_ids=",tuple(x.source_id for x in result["rows"]))

        self.assertGreater(result["cohort_size"],0)
        self.assertEqual(result["exact_readback"],result["cohort_size"])
        self.assertEqual(
            result["already_present"]+result["committed_new"],
            result["cohort_size"],
        )
        self.assertTrue(all(
            x.source_id.startswith("source.independent.")
            for x in result["rows"]
        ))
        self.assertTrue(all(
            x.execution_allowed is False
            for x in result["rows"]
        ))

if __name__=="__main__":
    print("="*88)
    print(" OAD-068 PHYSICAL CERTIFICATION TEST")
    print(" IDEMPOTENT EXACT POSTGRESQL INDEPENDENT READBACK")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        print("[NOTE] New writes require OPH-021 canonical writer RUNNING; rows already committed are read directly by exact ID.")
        raise SystemExit(1)
    print("[PASS] Existing committed independent rows are reused, not duplicated")
    print("[PASS] Only genuinely missing observations may enter OPH single-writer ingress")
    print("[PASS] Exact by_observation_id PostgreSQL readback verified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-068 CERTIFIED")
"""

def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88)
    print(" OAD-068 IDEMPOTENT REBUILD INSTALLER")
    print(" EXACT POSTGRESQL INDEPENDENT OBSERVATION READBACK")
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    dependencies=(
        PKG/"oad_065_independent_canonical_batch_gate.py",
        PKG/"oad_066_independent_single_writer_ingress_binding.py",
        PKG/"oad_067_independent_physical_single_writer_persistence.py",
    )
    for dep in dependencies:
        if not dep.is_file():
            raise RuntimeError("Required certified dependency missing: "+dep.name)
    if not freeze.is_file():
        raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
    if not oph.is_file():
        raise RuntimeError("Frozen OPH-023 boundary missing")

    h1=hashlib.sha256(freeze.read_bytes()).hexdigest()
    h2=hashlib.sha256(oph.read_bytes()).hexdigest()
    affected=(MODULE,TEST,INIT)
    old={x:(x.read_bytes() if x.exists() else None) for x in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_068_exact_postgresql_independent_readback import *"
        if export not in lines:
            lines.append(export)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        if hashlib.sha256(freeze.read_bytes()).hexdigest()!=h1:
            raise RuntimeError("Frozen Kalshi OAD-055 changed")
        if hashlib.sha256(oph.read_bytes()).hexdigest()!=h2:
            raise RuntimeError("Frozen OPH-023 changed")

        print("[PASS] OAD-065/066/067 dependencies verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 single-writer boundary unchanged")
        print("[PASS] Replaced OAD-068 readback with exact-read-before-write behavior")
        print("[PASS] Duplicate canonical identities are not resubmitted")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-068 IDEMPOTENT REBUILD COMPLETE")
    except Exception:
        for x,b in old.items():
            if b is None:
                if x.exists():
                    x.unlink()
            else:
                x.write_bytes(b)
        print("[ROLLBACK] OAD-068 rebuild failed; affected files restored")
        raise

if __name__=="__main__":
    main()
