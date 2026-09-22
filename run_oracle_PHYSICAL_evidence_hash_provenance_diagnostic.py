from __future__ import annotations

import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path.cwd().resolve()
STATE = ROOT / "runtime_state"
LEDGER = STATE / "oracle_learning_event_ledger.json"
LINE = "=" * 96
SAMPLE = 20

TEXT_SUFFIXES = {".json", ".jsonl", ".txt", ".log", ".ndjson"}


def load_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def ledger_records(obj):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if isinstance(v,dict):
                r=dict(v)
                r.setdefault("_ledger_key",k)
                out.append(r)
    elif isinstance(obj,list):
        out=[x for x in obj if isinstance(x,dict)]
    return out


def pick(row,*names):
    for name in names:
        value=row.get(name)
        if value not in (None,"",[],{}):
            return value
    return None


def status_of(row):
    return str(pick(row,"status","learning_status","admission_status") or "unknown").lower()


def ticker_of(row):
    return str(pick(row,"ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol") or "UNKNOWN")


def evidence_hash_of(row):
    return str(pick(row,"evidence_hash") or "")


def settlement_hash_of(row):
    return str(pick(row,"settlement_hash","source_hash") or "")


def settlement_ts_of(row):
    return str(pick(row,"settlement_ts","settled_at","settlement_time") or "")


def searchable_runtime_files():
    files=[]
    roots=[
        ROOT/"runtime_state",
        ROOT/"logs",
    ]
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if p.stat().st_size > 25_000_000:
                    continue
            except Exception:
                continue
            files.append(p)
    return files


def search_hash_in_files(target_hash, files):
    hits=[]
    if not target_hash:
        return hits
    needle=target_hash.lower()
    for p in files:
        try:
            text=p.read_text(encoding="utf-8",errors="ignore")
        except Exception:
            continue
        idx=text.lower().find(needle)
        if idx>=0:
            start=max(0,idx-250)
            end=min(len(text),idx+len(target_hash)+250)
            excerpt=" ".join(text[start:end].replace("\r"," ").replace("\n"," ").split())
            hits.append((p,excerpt))
    return hits


def inspect_postgres_by_hash(target_hash):
    results=[]
    if not target_hash:
        return results

    # Discover database URL from environment/.env without printing credentials.
    import os
    url=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")
    if not url:
        env=ROOT/".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8",errors="ignore").splitlines():
                if "=" not in line or line.lstrip().startswith("#"):
                    continue
                k,v=line.split("=",1)
                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"):
                    url=v.strip().strip('"').strip("'")
                    break
    if not url:
        return [("NO_DATABASE_URL",None,None,None)]

    try:
        import psycopg
        conn=psycopg.connect(url)
    except Exception as exc:
        return [("CONNECT_ERROR",type(exc).__name__,str(exc),None)]

    try:
        conn.autocommit=True
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_schema, table_name, column_name
                FROM information_schema.columns
                WHERE table_schema NOT IN ('pg_catalog','information_schema')
                  AND (
                    column_name ILIKE '%hash%'
                    OR column_name ILIKE '%evidence%'
                    OR column_name ILIKE '%observation%'
                    OR column_name ILIKE '%payload%'
                    OR column_name ILIKE '%data%'
                  )
                ORDER BY table_schema, table_name, ordinal_position
            """)
            cols=cur.fetchall()

        grouped=defaultdict(list)
        for schema,table,column in cols:
            grouped[(schema,table)].append(column)

        for (schema,table),columns in grouped.items():
            safe_schema='"'+str(schema).replace('"','""')+'"'
            safe_table='"'+str(table).replace('"','""')+'"'
            for col in columns:
                safe_col='"'+str(col).replace('"','""')+'"'
                query=f"SELECT {safe_col}::text FROM {safe_schema}.{safe_table} WHERE {safe_col}::text = %s LIMIT 3"
                try:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN READ ONLY")
                        cur.execute(query,(target_hash,))
                        rows=cur.fetchall()
                        cur.execute("ROLLBACK")
                    if rows:
                        results.append(("EXACT_COLUMN_MATCH",f"{schema}.{table}",col,len(rows)))
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            # Broad text search only for likely JSON/text payload columns.
            likely=[c for c in columns if any(x in c.lower() for x in ("payload","data","json","body","record"))]
            for col in likely:
                safe_col='"'+str(col).replace('"','""')+'"'
                query=f"SELECT {safe_col}::text FROM {safe_schema}.{safe_table} WHERE {safe_col}::text LIKE %s LIMIT 3"
                try:
                    with conn.cursor() as cur:
                        cur.execute("BEGIN READ ONLY")
                        cur.execute(query,(f"%{target_hash}%",))
                        rows=cur.fetchall()
                        cur.execute("ROLLBACK")
                    if rows:
                        results.append(("PAYLOAD_TEXT_MATCH",f"{schema}.{table}",col,len(rows)))
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return results


def main():
    print(LINE)
    print(" ORACLE PHYSICAL EVIDENCE-HASH PROVENANCE DIAGNOSTIC")
    print(" READ-ONLY — TRACE KNOWN-GOOD LEARNED EVIDENCE BACK TO PHYSICAL STORAGE")
    print(LINE)

    raw=load_json(LEDGER)
    if raw is None:
        print(f"[ERROR] Could not load {LEDGER}")
        raise SystemExit(2)

    rows=ledger_records(raw)
    learned=[r for r in rows if status_of(r)=="learned" and evidence_hash_of(r)]
    missing=[r for r in rows if status_of(r)=="evidence_missing"]

    print(f"[LEDGER] records={len(rows)} learned_with_evidence_hash={len(learned)} evidence_missing={len(missing)}")
    print(f"[SAMPLE] tracing_first={min(SAMPLE,len(learned))} learned evidence hashes")

    files=searchable_runtime_files()
    print(f"[LOCAL SEARCH] searchable_runtime_files={len(files)}")
    print("-"*96)

    storage_counter=Counter()
    local_found=0
    pg_found=0

    for idx,row in enumerate(learned[:SAMPLE],1):
        ticker=ticker_of(row)
        ehash=evidence_hash_of(row)
        shash=settlement_hash_of(row)
        sts=settlement_ts_of(row)

        local_hits=search_hash_in_files(ehash,files)
        pg_hits=inspect_postgres_by_hash(ehash)

        real_pg_hits=[x for x in pg_hits if x and x[0] in ("EXACT_COLUMN_MATCH","PAYLOAD_TEXT_MATCH")]

        if local_hits:
            local_found+=1
            for p,_ in local_hits:
                storage_counter[f"FILE:{p.relative_to(ROOT)}"]+=1
        if real_pg_hits:
            pg_found+=1
            for kind,table,col,count in real_pg_hits:
                storage_counter[f"PG:{table}.{col}:{kind}"]+=1

        print(
            f"[{idx:02d}/{min(SAMPLE,len(learned)):02d}] "
            f"ticker={ticker} evidence_hash={ehash[:16]}... "
            f"settlement_hash={shash[:16]+'...' if shash else 'NONE'} "
            f"settlement_ts={sts or 'NONE'}"
        )
        print(f"    local_hash_hits={len(local_hits)} postgres_hash_hits={len(real_pg_hits)}")

        for p,excerpt in local_hits[:3]:
            print(f"    [LOCAL] {p.relative_to(ROOT)}")
            print(f"            {excerpt[:420]}")

        for kind,table,col,count in real_pg_hits[:5]:
            print(f"    [POSTGRES] kind={kind} location={table}.{col} rows={count}")

        if not local_hits and not real_pg_hits:
            special=[x for x in pg_hits if x and x[0] not in ("EXACT_COLUMN_MATCH","PAYLOAD_TEXT_MATCH")]
            for x in special[:1]:
                print(f"    [POSTGRES STATUS] {x}")

    print("="*96)
    print(" PROVENANCE SUMMARY")
    print("="*96)
    print(f"[KNOWN-GOOD HASHES TRACED] {min(SAMPLE,len(learned))}")
    print(f"[FOUND IN LOCAL RUNTIME FILES] {local_found}")
    print(f"[FOUND IN POSTGRESQL] {pg_found}")

    if storage_counter:
        print("[TOP PHYSICAL LOCATIONS]")
        for loc,count in storage_counter.most_common(20):
            print(f"  {loc}: {count}")
    else:
        print("[TOP PHYSICAL LOCATIONS] NONE")

    if pg_found:
        print("[DIAGNOSIS] Known-good evidence hashes are physically recoverable in PostgreSQL.")
        print("[NEXT] Compare their storage table/column + market identity path against evidence_missing records.")
        print("[CLASSIFICATION] Matcher/storage-path mismatch is strongly indicated; frozen OLR still remains untouched until exact defect is isolated.")
    elif local_found:
        print("[DIAGNOSIS] Known-good evidence hashes are physically recoverable in local runtime state/log storage, but not PostgreSQL.")
        print("[NEXT] Learning provenance is likely flowing through a non-PostgreSQL persisted surface or a transformed hash not indexed by the historical matcher.")
        print("[CLASSIFICATION] Do NOT modify frozen OLR yet.")
    else:
        print("[DIAGNOSIS] Known-good learned evidence hashes were not directly recoverable from searched PostgreSQL columns or runtime text state.")
        print("[NEXT] The evidence hash is likely derived from canonicalized content rather than stored verbatim, or lives behind a different persistence/read model.")
        print("[CLASSIFICATION] Do NOT modify frozen OLR yet; inspect the hash-generation source next.")

    print("[PASS] Provenance diagnostic performed read-only")
    print("[PASS] No PostgreSQL writes")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] OHL historical subsystem untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE PHYSICAL EVIDENCE-HASH PROVENANCE DIAGNOSTIC COMPLETE")


if __name__=="__main__":
    main()
