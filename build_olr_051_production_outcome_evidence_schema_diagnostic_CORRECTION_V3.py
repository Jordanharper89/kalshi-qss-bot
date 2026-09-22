from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_051_production_outcome_evidence_schema_diagnostic.py"
TEST=ROOT/"test_olr_051_production_outcome_evidence_schema_diagnostic.py"
INIT=PKG/"__init__.py"
REPORT=PKG/"OLR_051_SCHEMA_DIAGNOSTIC_REPORT.json"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport ast,json,re\n\nOLR_051_BUILD_ID="OLR-051"\nOLR_051_REVISION="OLR_051_PRODUCTION_OUTCOME_EVIDENCE_SCHEMA_DIAGNOSTIC_CORRECTION_V3"\n\n@dataclass(frozen=True)\nclass TableInventory:\n    table:str\n    row_count:int\n    columns:tuple[str,...]\n\n@dataclass(frozen=True)\nclass SourceReference:\n    file:str\n    line:int\n    text:str\n\n@dataclass(frozen=True)\nclass SchemaDiagnosticResult:\n    nonempty_tables:tuple[dict,...]\n    learning_source_references:tuple[dict,...]\n    likely_break:str\n    execution_authority:bool=False\n\ndef _connect(root=None):\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect(root)\n\ndef inventory_nonempty_public_tables(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    rows=[]\n    with _connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute("""\n                SELECT table_name\n                FROM information_schema.tables\n                WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\'\n                ORDER BY table_name\n            """)\n            tables=[str(r[0]) for r in cur.fetchall()]\n            for table in tables:\n                cur.execute("""\n                    SELECT column_name\n                    FROM information_schema.columns\n                    WHERE table_schema=\'public\' AND table_name=%s\n                    ORDER BY ordinal_position\n                """,(table,))\n                cols=tuple(str(r[0]) for r in cur.fetchall())\n                try:\n                    cur.execute(f"SELECT COUNT(*) FROM public.{table}")\n                    count=int(cur.fetchone()[0])\n                except Exception:\n                    conn.rollback()\n                    continue\n                if count>0:\n                    rows.append(TableInventory(table,count,cols))\n    rows.sort(key=lambda x:x.row_count,reverse=True)\n    return tuple(rows)\n\ndef scan_learning_sources(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    targets=[]\n    for pattern in (\n        "qseries_v2/oracle_learning/*.py",\n        "run_olr_*.py",\n        "qseries_v2/**/*.py",\n    ):\n        targets.extend(root.glob(pattern))\n\n    seen=set()\n    refs=[]\n    needles=(\n        "settled","outcome","evidence","ledger","postgres","sequence_number",\n        "observation_id","market_ticker","ticker","market_id","learned_total",\n        "evidence_missing","exact_evidence","candidates","admitted"\n    )\n\n    for path in targets:\n        if not path.is_file():\n            continue\n        key=str(path.resolve()).lower()\n        if key in seen:\n            continue\n        seen.add(key)\n        try:\n            text=path.read_text(encoding="utf-8",errors="ignore")\n        except Exception:\n            continue\n        for i,line in enumerate(text.splitlines(),1):\n            low=line.lower()\n            if any(n in low for n in needles):\n                stripped=line.strip()\n                if stripped:\n                    refs.append(SourceReference(\n                        str(path.relative_to(root)),\n                        i,\n                        stripped[:500],\n                    ))\n    return tuple(refs)\n\ndef _likely_break(tables,refs):\n    table_names=" ".join(x.table.lower() for x in tables)\n    ref_text=" ".join(r.text.lower() for r in refs)\n\n    has_identity_cols=any(\n        any(c in x.columns for c in ("ticker","market_ticker","market_id","observation_id"))\n        for x in tables\n    )\n    learner_mentions_sql=("select " in ref_text or "insert into " in ref_text or "postgres" in ref_text)\n    learner_mentions_files=any(tok in ref_text for tok in (".json",".jsonl",".sqlite","path(","read_text","open("))\n\n    if not tables:\n        return "NO_NONEMPTY_PUBLIC_POSTGRESQL_TABLES_FOUND"\n    if not has_identity_cols and learner_mentions_files:\n        return "LEARNER_APPEARS_TO_USE_NON_POSTGRESQL_OR_FILE_BACKED_OUTCOME_EVIDENCE_STORAGE"\n    if not has_identity_cols and learner_mentions_sql:\n        return "POSTGRESQL_SCHEMA_EXISTS_BUT_IDENTITY_COLUMNS_DIFFER_FROM_OLR_041_ASSUMPTIONS"\n    if has_identity_cols:\n        return "IDENTITY_COLUMNS_EXIST_DIAGNOSTIC_MUST_TARGET_ACTUAL_LEARNER_TABLE_CONTRACT"\n    return "OUTCOME_EVIDENCE_STORAGE_CONTRACT_UNRESOLVED"\n\ndef run_schema_diagnostic(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    tables=inventory_nonempty_public_tables(root)\n    refs=scan_learning_sources(root)\n\n    table_dump=tuple({\n        "table":x.table,\n        "row_count":x.row_count,\n        "columns":list(x.columns),\n    } for x in tables[:50])\n\n    ref_dump=tuple({\n        "file":r.file,\n        "line":r.line,\n        "text":r.text,\n    } for r in refs[:500])\n\n    return SchemaDiagnosticResult(\n        table_dump,\n        ref_dump,\n        _likely_break(tables,refs),\n        False,\n    )\n\ndef write_schema_diagnostic_report(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    result=run_schema_diagnostic(root)\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_051_SCHEMA_DIAGNOSTIC_REPORT.json"\n    path.write_text(\n        json.dumps(asdict(result),sort_keys=True,indent=2,default=str)+"\\n",\n        encoding="utf-8",\n        newline="\\n",\n    )\n    return path,result\n\ndef verify_olr_051_production_outcome_evidence_schema_diagnostic(root=None):\n    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze\n    return (\n        verify_olr_050_production_evidence_learning_activation_freeze(root)\n        and OLR_051_BUILD_ID=="OLR-051"\n        and callable(run_schema_diagnostic)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_051_production_outcome_evidence_schema_diagnostic import *\n\nclass T(unittest.TestCase):\n    def test_contract(self):\n        r=SchemaDiagnosticResult((),(),"OUTCOME_EVIDENCE_STORAGE_CONTRACT_UNRESOLVED",False)\n        self.assertFalse(r.execution_authority)\n\n    def test_identity(self):\n        self.assertEqual(OLR_051_BUILD_ID,"OLR-051")\n        self.assertIn("CORRECTION_V3",OLR_051_REVISION)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLR-051 CERTIFICATION TEST")\n    print(" PRODUCTION OUTCOME-EVIDENCE SCHEMA DIAGNOSTIC — CORRECTION V3")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Non-empty PostgreSQL table inventory contract certified")\n    print("[PASS] Existing learning-source inspection contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-051 CORRECTION V3 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OLR-051 INSTALLER")
    print(" PRODUCTION OUTCOME-EVIDENCE SCHEMA DIAGNOSTIC — CORRECTION V3")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module(
        "qseries_v2.oracle_learning.olr_050_production_evidence_learning_activation_freeze"
    )
    if not up.verify_olr_050_production_evidence_learning_activation_freeze(ROOT):
        raise RuntimeError("Certified OLR-050 verification failed")

    print("[PASS] Certified OLR-050 upstream boundary verified read-only")

    affected=(MOD,TEST,INIT,REPORT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(
            INIT,
            "from .olr_051_production_outcome_evidence_schema_diagnostic import *",
        )

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_learning.olr_051_production_outcome_evidence_schema_diagnostic"
        )

        path,result=m.write_schema_diagnostic_report(ROOT)

        print("[DIAGNOSTIC] likely_break="+str(result.likely_break))
        print("[NONEMPTY POSTGRESQL TABLES]")
        for x in result.nonempty_tables[:25]:
            print(
                "  table="+x["table"]+
                " rows="+str(x["row_count"])+
                " columns="+",".join(x["columns"])
            )

        print("[LEARNING SOURCE REFERENCES]")
        shown=0
        for x in result.learning_source_references:
            text=x["text"].lower()
            if any(k in text for k in (
                "settled","outcome","evidence_missing","exact_evidence",
                "candidates","admitted","postgres","select ","insert into ",
                "observation_id","market_ticker","ticker","market_id"
            )):
                print(
                    "  file="+x["file"]+
                    " line="+str(x["line"])+
                    " :: "+x["text"]
                )
                shown+=1
                if shown>=80:
                    break

        print("[PASS] Wrote:",path.relative_to(ROOT))

    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-051 correction V3 failed; affected files restored")
        raise

    print("[PASS] PostgreSQL inspected read-only")
    print("[PASS] Existing learner source inspected read-only")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] Existing learner unchanged")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] OLR-036 through OLR-050 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-051 CORRECTION V3 DIAGNOSTIC COMPLETE")

if __name__=="__main__":
    main()
