from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import ast,json,re

OLR_051_BUILD_ID="OLR-051"
OLR_051_REVISION="OLR_051_PRODUCTION_OUTCOME_EVIDENCE_SCHEMA_DIAGNOSTIC_CORRECTION_V3"

@dataclass(frozen=True)
class TableInventory:
    table:str
    row_count:int
    columns:tuple[str,...]

@dataclass(frozen=True)
class SourceReference:
    file:str
    line:int
    text:str

@dataclass(frozen=True)
class SchemaDiagnosticResult:
    nonempty_tables:tuple[dict,...]
    learning_source_references:tuple[dict,...]
    likely_break:str
    execution_authority:bool=False

def _connect(root=None):
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    return connect(root)

def inventory_nonempty_public_tables(root=None):
    root=Path(root or Path.cwd()).resolve()
    rows=[]
    with _connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema='public' AND table_type='BASE TABLE'
                ORDER BY table_name
            """)
            tables=[str(r[0]) for r in cur.fetchall()]
            for table in tables:
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name=%s
                    ORDER BY ordinal_position
                """,(table,))
                cols=tuple(str(r[0]) for r in cur.fetchall())
                try:
                    cur.execute(f"SELECT COUNT(*) FROM public.{table}")
                    count=int(cur.fetchone()[0])
                except Exception:
                    conn.rollback()
                    continue
                if count>0:
                    rows.append(TableInventory(table,count,cols))
    rows.sort(key=lambda x:x.row_count,reverse=True)
    return tuple(rows)

def scan_learning_sources(root=None):
    root=Path(root or Path.cwd()).resolve()
    targets=[]
    for pattern in (
        "qseries_v2/oracle_learning/*.py",
        "run_olr_*.py",
        "qseries_v2/**/*.py",
    ):
        targets.extend(root.glob(pattern))

    seen=set()
    refs=[]
    needles=(
        "settled","outcome","evidence","ledger","postgres","sequence_number",
        "observation_id","market_ticker","ticker","market_id","learned_total",
        "evidence_missing","exact_evidence","candidates","admitted"
    )

    for path in targets:
        if not path.is_file():
            continue
        key=str(path.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            text=path.read_text(encoding="utf-8",errors="ignore")
        except Exception:
            continue
        for i,line in enumerate(text.splitlines(),1):
            low=line.lower()
            if any(n in low for n in needles):
                stripped=line.strip()
                if stripped:
                    refs.append(SourceReference(
                        str(path.relative_to(root)),
                        i,
                        stripped[:500],
                    ))
    return tuple(refs)

def _likely_break(tables,refs):
    table_names=" ".join(x.table.lower() for x in tables)
    ref_text=" ".join(r.text.lower() for r in refs)

    has_identity_cols=any(
        any(c in x.columns for c in ("ticker","market_ticker","market_id","observation_id"))
        for x in tables
    )
    learner_mentions_sql=("select " in ref_text or "insert into " in ref_text or "postgres" in ref_text)
    learner_mentions_files=any(tok in ref_text for tok in (".json",".jsonl",".sqlite","path(","read_text","open("))

    if not tables:
        return "NO_NONEMPTY_PUBLIC_POSTGRESQL_TABLES_FOUND"
    if not has_identity_cols and learner_mentions_files:
        return "LEARNER_APPEARS_TO_USE_NON_POSTGRESQL_OR_FILE_BACKED_OUTCOME_EVIDENCE_STORAGE"
    if not has_identity_cols and learner_mentions_sql:
        return "POSTGRESQL_SCHEMA_EXISTS_BUT_IDENTITY_COLUMNS_DIFFER_FROM_OLR_041_ASSUMPTIONS"
    if has_identity_cols:
        return "IDENTITY_COLUMNS_EXIST_DIAGNOSTIC_MUST_TARGET_ACTUAL_LEARNER_TABLE_CONTRACT"
    return "OUTCOME_EVIDENCE_STORAGE_CONTRACT_UNRESOLVED"

def run_schema_diagnostic(root=None):
    root=Path(root or Path.cwd()).resolve()
    tables=inventory_nonempty_public_tables(root)
    refs=scan_learning_sources(root)

    table_dump=tuple({
        "table":x.table,
        "row_count":x.row_count,
        "columns":list(x.columns),
    } for x in tables[:50])

    ref_dump=tuple({
        "file":r.file,
        "line":r.line,
        "text":r.text,
    } for r in refs[:500])

    return SchemaDiagnosticResult(
        table_dump,
        ref_dump,
        _likely_break(tables,refs),
        False,
    )

def write_schema_diagnostic_report(root=None):
    root=Path(root or Path.cwd()).resolve()
    result=run_schema_diagnostic(root)
    path=root/"qseries_v2"/"oracle_learning"/"OLR_051_SCHEMA_DIAGNOSTIC_REPORT.json"
    path.write_text(
        json.dumps(asdict(result),sort_keys=True,indent=2,default=str)+"\n",
        encoding="utf-8",
        newline="\n",
    )
    return path,result

def verify_olr_051_production_outcome_evidence_schema_diagnostic(root=None):
    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze
    return (
        verify_olr_050_production_evidence_learning_activation_freeze(root)
        and OLR_051_BUILD_ID=="OLR-051"
        and callable(run_schema_diagnostic)
    )
