from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
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
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-002'
TITLE='POSTGRESQL LIVE OBSERVATION READ MODEL'
REVISION='OCR_002_PRODUCTION_CORRECTION_V2'
MODULE=PACKAGE/'ocr_002_live_observation_read_model.py'
TEST=ROOT/'test_ocr_002_postgresql_live_observation_read_model.py'
EXPORTS=('OCR_002_BUILD_ID', 'OCR_002_REVISION', 'LiveObservationReadResult', 'load_env', 'read_latest_canonical_observations', 'quote_sql_identifier', 'verify_ocr_002_postgresql_live_observation_read_model')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os,re\n\nOCR_002_BUILD_ID="OCR-002"\nOCR_002_REVISION="OCR_002_POSTGRESQL_LIVE_OBSERVATION_READ_MODEL_V1"\n\nIDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")\n\n@dataclass(frozen=True)\nclass LiveObservationReadResult:\n    schema:str\n    table:str\n    rows:tuple[dict,...]\n    read_only:bool=True\n\ndef load_env(root):\n    env=dict(os.environ)\n    p=Path(root)/".env"\n    if p.is_file():\n        for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n            line=raw.strip()\n            if not line or line.startswith("#") or "=" not in line: continue\n            k,v=line.split("=",1); k=k.strip(); v=v.strip().strip(\'"\').strip("\'")\n            if k and k not in env: env[k]=v\n    return env\n\ndef _connect(url):\n    try:\n        import psycopg\n        return psycopg.connect(url)\n    except ImportError:\n        import psycopg2\n        return psycopg2.connect(url)\n\ndef quote_sql_identifier(name):\n    if not IDENT.fullmatch(name): raise ValueError("unsafe SQL identifier")\n    return \'"\'+name+\'"\'\n\ndef read_latest_canonical_observations(root=None,limit=25):\n    root=Path(root or Path.cwd()).resolve()\n    limit=max(1,min(int(limit),100))\n    env=load_env(root)\n    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")\n    if not url: raise RuntimeError("DATABASE_URL not configured")\n    conn=_connect(url)\n    try:\n        try: conn.set_session(readonly=True,autocommit=False)\n        except Exception: pass\n        cur=conn.cursor()\n        cur.execute("""SELECT table_schema,table_name FROM information_schema.columns\n                       WHERE column_name=\'observation_id\' AND table_schema NOT IN (\'pg_catalog\',\'information_schema\')\n                       ORDER BY CASE WHEN table_name ILIKE \'%canonical%\' THEN 0 WHEN table_name ILIKE \'%observation%\' THEN 1 ELSE 2 END,\n                                table_schema,table_name LIMIT 20""")\n        candidates=cur.fetchall()\n        if not candidates: raise RuntimeError("No PostgreSQL observation table with observation_id column found")\n        last_error=None\n        for schema,table in candidates:\n            try:\n                cur.execute("""SELECT column_name FROM information_schema.columns\n                               WHERE table_schema=%s AND table_name=%s""",(schema,table))\n                cols={r[0] for r in cur.fetchall()}\n                order=next((c for c in ("sequence_number","persisted_at","observed_at","created_at","acquired_at") if c in cols),None)\n                sql=f"SELECT to_jsonb(t) FROM {quote_sql_identifier(schema)}.{quote_sql_identifier(table)} t"\n                if order: sql+=f" ORDER BY {quote_sql_identifier(order)} DESC"\n                sql+=" LIMIT %s"\n                cur.execute(sql,(limit,))\n                rows=tuple(dict(r[0]) for r in cur.fetchall())\n                if rows:\n                    conn.rollback()\n                    return LiveObservationReadResult(schema,table,rows,True)\n            except Exception as exc:\n                conn.rollback(); last_error=exc; cur=conn.cursor()\n        raise RuntimeError("Observation tables found but no readable rows: "+str(last_error))\n    finally:\n        conn.close()\n\ndef verify_ocr_002_postgresql_live_observation_read_model():\n    return quote_sql_identifier("observation_id")==\'"observation_id"\' and LiveObservationReadResult("s","t",tuple()).read_only\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ocr_002_postgresql_live_observation_read_model())\n    def test_identifier_rejected(self):\n        with self.assertRaises(ValueError): quote_sql_identifier("x;drop")\n    def test_limit_contract(self): self.assertTrue(LiveObservationReadResult("s","t",tuple()).read_only)\nif __name__=="__main__":\n    print("="*72);print(" OCR-002 CERTIFICATION TEST");print(" POSTGRESQL LIVE OBSERVATION READ MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] SELECT-only live observation read model certified")\n    print("[DONE] OCR-002 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_001_foundation')
        if getattr(m,'verify_ocr_001_continuous_reasoning_runtime_foundation')() is not True:
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
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

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
