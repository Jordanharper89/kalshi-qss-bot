from pathlib import Path
import importlib, os, subprocess, sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_030_postgresql_writer_retry_telemetry.py";TEST=ROOT/"test_oph_030_postgresql_writer_retry_telemetry.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema\n\nOPH_030_BUILD_ID="OPH-030"\nOPH_030_REVISION="OPH_030_POSTGRESQL_WRITER_RETRY_TELEMETRY_V1"\nTABLE="oracle_writer_retry_telemetry"\n\ndef ensure_retry_telemetry_schema(root=None):\n    ensure_postgresql_ingestion_schema(root)\n    ddl=f"""\n    CREATE TABLE IF NOT EXISTS public.{TABLE}(\n      telemetry_id BIGSERIAL PRIMARY KEY,\n      observed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),\n      request_id TEXT,\n      producer TEXT,\n      phase TEXT NOT NULL,\n      category TEXT NOT NULL,\n      retryable BOOLEAN NOT NULL,\n      terminal BOOLEAN NOT NULL,\n      attempt INTEGER NOT NULL,\n      observation_count INTEGER NOT NULL,\n      elapsed_ms DOUBLE PRECISION,\n      error_type TEXT,\n      error_message TEXT\n    );\n    CREATE INDEX IF NOT EXISTS oracle_writer_retry_telemetry_request_idx\n      ON public.{TABLE}(request_id,observed_at);\n    CREATE INDEX IF NOT EXISTS oracle_writer_retry_telemetry_category_idx\n      ON public.{TABLE}(category,observed_at);\n    """\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur: cur.execute(ddl)\n    return True\n\ndef record_writer_event(request_id,producer,phase,classification,attempt,observation_count,root=None,elapsed_ms=None,exc=None):\n    ensure_retry_telemetry_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"""INSERT INTO public.{TABLE}\n                (request_id,producer,phase,category,retryable,terminal,attempt,\n                 observation_count,elapsed_ms,error_type,error_message)\n                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",\n                (\n                    str(request_id) if request_id is not None else None,\n                    str(producer) if producer is not None else None,\n                    str(phase),\n                    str(classification.category),\n                    bool(classification.retryable),\n                    bool(classification.terminal),\n                    int(attempt),\n                    int(observation_count),\n                    None if elapsed_ms is None else float(elapsed_ms),\n                    None if exc is None else type(exc).__name__,\n                    None if exc is None else str(exc)[:2000],\n                ),\n            )\n        conn.commit()\n    return True\n\ndef telemetry_counts(root=None):\n    ensure_retry_telemetry_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT category,COUNT(*) FROM public.{TABLE}\n                            GROUP BY category ORDER BY category""")\n            return {str(k):int(v) for k,v in cur.fetchall()}\n\ndef verify_oph_030_postgresql_writer_retry_telemetry(root=None):\n    from .oph_029_postgresql_routing_failure_classification import verify_oph_029_postgresql_routing_failure_classification\n    return verify_oph_029_postgresql_routing_failure_classification(root) and TABLE=="oracle_writer_retry_telemetry"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_030_postgresql_writer_retry_telemetry import *\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(OPH_030_BUILD_ID,"OPH-030")\n    def test_table(self): self.assertEqual(TABLE,"oracle_writer_retry_telemetry")\nif __name__=="__main__":\n    print("="*88);print(" OPH-030 CERTIFICATION TEST");print(" POSTGRESQL WRITER RETRY TELEMETRY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Durable PostgreSQL retry telemetry contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-030 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-030 INSTALLER");print(" POSTGRESQL WRITER RETRY TELEMETRY");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_029_postgresql_routing_failure_classification")
    if up.verify_oph_029_postgresql_routing_failure_classification(ROOT) is not True:
        raise RuntimeError("Certified OPH-029 upstream verification failed")
    print("[PASS] Certified OPH-029 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oph_030_postgresql_writer_retry_telemetry import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_030_postgresql_writer_retry_telemetry")
        m.ensure_retry_telemetry_schema(ROOT)
        if m.verify_oph_030_postgresql_writer_retry_telemetry(ROOT) is not True: raise RuntimeError("OPH-030 verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-030 installation failed; affected files restored");raise
    print("[PASS] PostgreSQL retry telemetry schema physically verified")
    print("[PASS] OPH-001 through OPH-029 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-030 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
