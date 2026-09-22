from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-012'
TITLE='INCREMENTAL NEW-OBSERVATION SELECTION'
REVISION='OCR_012_PRODUCTION_CORRECTION_V2'
MODULE=PACKAGE/'ocr_012_incremental_observation_selection.py'
TEST=ROOT/'test_ocr_012_incremental_new_observation_selection.py'
EXPORTS=('OCR_012_BUILD_ID', 'OCR_012_REVISION', 'IncrementalObservationSlice', 'read_new_canonical_observations', 'cursor_values_from_last_row', 'build_incremental_cursor_predicate', 'verify_ocr_012_incremental_new_observation_selection')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .ocr_002_live_observation_read_model import load_env,quote_sql_identifier\n\nOCR_012_BUILD_ID="OCR-012"\nOCR_012_REVISION="OCR_012_INCREMENTAL_NEW_OBSERVATION_SELECTION_V1"\nORDER_CANDIDATES=("sequence_number","persisted_at","created_at","observed_at","acquired_at")\n\n@dataclass(frozen=True)\nclass IncrementalObservationSlice:\n    schema:str\n    table:str\n    order_column:str\n    rows:tuple[dict,...]\n    read_only:bool=True\n\ndef _connect(url):\n    try:\n        import psycopg\n        return psycopg.connect(url)\n    except ImportError:\n        import psycopg2\n        return psycopg2.connect(url)\n\ndef _discover_source(cur):\n    cur.execute("""SELECT table_schema,table_name FROM information_schema.columns\n                   WHERE column_name=\'observation_id\' AND table_schema NOT IN (\'pg_catalog\',\'information_schema\')\n                   ORDER BY CASE WHEN table_name=\'oracle_canonical_observations\' THEN 0\n                                 WHEN table_name ILIKE \'%canonical%\' THEN 1\n                                 WHEN table_name ILIKE \'%observation%\' THEN 2 ELSE 3 END,\n                            table_schema,table_name LIMIT 20""")\n    candidates=cur.fetchall()\n    for schema,table in candidates:\n        cur.execute("""SELECT column_name FROM information_schema.columns\n                       WHERE table_schema=%s AND table_name=%s""",(schema,table))\n        cols={r[0] for r in cur.fetchall()}\n        order=next((x for x in ORDER_CANDIDATES if x in cols),None)\n        if order:\n            return schema,table,order\n    raise RuntimeError("No observation table with a supported deterministic order column found")\n\ndef build_incremental_cursor_predicate(order_column):\n    if order_column=="sequence_number":\n        return "numeric"\n    if order_column in ("persisted_at","created_at","observed_at","acquired_at"):\n        return "timestamp"\n    raise ValueError("unsupported order column")\n\ndef read_new_canonical_observations(root=None,cursor=None,limit=50):\n    from .ocr_011_reasoning_cursor_state import empty_reasoning_cursor\n    root=Path(root or Path.cwd()).resolve()\n    cursor=cursor or empty_reasoning_cursor()\n    limit=max(1,min(int(limit),500))\n    env=load_env(root)\n    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")\n    if not url:raise RuntimeError("DATABASE_URL not configured")\n    conn=_connect(url)\n    try:\n        try:conn.set_session(readonly=True,autocommit=False)\n        except Exception:pass\n        cur=conn.cursor()\n        schema,table,order=_discover_source(cur)\n        if cursor.order_column and cursor.order_column!=order:\n            raise RuntimeError("Reasoning cursor order column no longer matches production table")\n        qschema=quote_sql_identifier(schema);qtable=quote_sql_identifier(table);qorder=quote_sql_identifier(order)\n        sql=f"SELECT to_jsonb(t) FROM {qschema}.{qtable} t"\n        params=[]\n        if cursor.order_value:\n            if order=="sequence_number":\n                sql+=f" WHERE ({qorder} > %s::bigint OR ({qorder} = %s::bigint AND observation_id::text > %s))"\n            else:\n                sql+=f" WHERE ({qorder} > %s::timestamptz OR ({qorder} = %s::timestamptz AND observation_id::text > %s))"\n            params.extend((cursor.order_value,cursor.order_value,cursor.observation_id))\n        sql+=f" ORDER BY {qorder} ASC, observation_id ASC LIMIT %s"\n        params.append(limit)\n        cur.execute(sql,tuple(params))\n        rows=tuple(dict(r[0]) for r in cur.fetchall())\n        conn.rollback()\n        return IncrementalObservationSlice(schema,table,order,rows,True)\n    finally:\n        conn.close()\n\ndef cursor_values_from_last_row(slice_):\n    if not slice_.rows:raise ValueError("slice rows required")\n    row=slice_.rows[-1]\n    value=row.get(slice_.order_column)\n    oid=row.get("observation_id")\n    if value is None or oid is None:raise RuntimeError("cursor columns missing from row")\n    return slice_.order_column,str(value),str(oid)\n\ndef verify_ocr_012_incremental_new_observation_selection():\n    return (\n        ORDER_CANDIDATES[0]=="sequence_number"\n        and build_incremental_cursor_predicate("sequence_number")=="numeric"\n        and build_incremental_cursor_predicate("persisted_at")=="timestamp"\n        and IncrementalObservationSlice("s","t","sequence_number",tuple()).read_only\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_012_incremental_new_observation_selection())\n    def test_numeric_cursor_ordering_contract(self):\n        self.assertEqual(build_incremental_cursor_predicate("sequence_number"),"numeric")\n\n    def test_timestamp_cursor_ordering_contract(self):\n        self.assertEqual(build_incremental_cursor_predicate("persisted_at"),"timestamp")\n\n    def test_cursor_values(self):\n        s=IncrementalObservationSlice("s","t","sequence_number",({"sequence_number":7,"observation_id":"o7"},))\n        self.assertEqual(cursor_values_from_last_row(s),("sequence_number","7","o7"))\nif __name__=="__main__":\n    print("="*72);print(" OCR-012 CERTIFICATION TEST");print(" INCREMENTAL NEW-OBSERVATION SELECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] SELECT-only incremental observation selection certified");print("[DONE] OCR-012 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state')
        if getattr(m,'verify_ocr_011_reasoning_cursor_state')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
