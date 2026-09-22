from __future__ import annotations

import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path.cwd().resolve()
STATE = ROOT / "runtime_state"
LEDGER = STATE / "oracle_learning_event_ledger.json"
LINE = "=" * 96

SAMPLE = 20
MAX_FILE_BYTES = 25_000_000
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
    return str(
        pick(
            row,
            "ticker","market_ticker","market_id",
            "canonical_market_id","venue_market_id","symbol"
        ) or "UNKNOWN"
    )


def evidence_hash_of(row):
    return str(pick(row,"evidence_hash") or "")


def settlement_hash_of(row):
    return str(pick(row,"settlement_hash","source_hash") or "")


def settlement_ts_of(row):
    return str(pick(row,"settlement_ts","settled_at","settlement_time") or "")


def searchable_files():
    files=[]
    for base in (ROOT/"runtime_state", ROOT/"logs"):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except Exception:
                continue
            files.append(p)
    return files


def build_single_pass_hash_index(target_hashes, files):
    targets={h.lower():h for h in target_hashes if h}
    hits={h:[] for h in targets.values()}

    total=len(files)
    for idx,p in enumerate(files,1):
        try:
            text=p.read_text(encoding="utf-8",errors="ignore")
        except Exception:
            continue

        lower=text.lower()

        for low,original in targets.items():
            pos=lower.find(low)
            if pos>=0:
                start=max(0,pos-200)
                end=min(len(text),pos+len(original)+200)
                excerpt=" ".join(text[start:end].replace("\r"," ").replace("\n"," ").split())
                hits[original].append((p,excerpt))

        if idx % 5000 == 0 or idx == total:
            found=sum(1 for v in hits.values() if v)
            print(
                f"[LOCAL INDEX] files_scanned={idx}/{total} "
                f"hashes_found={found}/{len(targets)}",
                flush=True,
            )

    return hits


def database_url():
    import os
    url=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")
    if url:
        return url

    env=ROOT/".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8",errors="ignore").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            k,v=line.split("=",1)
            if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"):
                return v.strip().strip('"').strip("'")
    return None


def discover_hash_columns(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_schema, table_name, column_name, data_type
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
        return cur.fetchall()


def inspect_postgres_hashes(target_hashes):
    url=database_url()
    if not url:
        return {"status":"NO_DATABASE_URL","hits":{},"columns":[]}

    try:
        import psycopg
        conn=psycopg.connect(url)
    except Exception as exc:
        return {"status":f"CONNECT_ERROR:{type(exc).__name__}:{exc}","hits":{},"columns":[]}

    hits={h:[] for h in target_hashes}
    try:
        conn.autocommit=True
        columns=discover_hash_columns(conn)

        grouped=defaultdict(list)
        for schema,table,column,data_type in columns:
            grouped[(schema,table)].append((column,data_type))

        print(f"[POSTGRES] candidate_tables={len(grouped)} candidate_columns={len(columns)}",flush=True)

        for table_idx,((schema,table),cols) in enumerate(grouped.items(),1):
            safe_schema='"'+str(schema).replace('"','""')+'"'
            safe_table='"'+str(table).replace('"','""')+'"'

            for col,data_type in cols:
                safe_col='"'+str(col).replace('"','""')+'"'

                # Exact hash match
                for h in target_hashes:
                    try:
                        q=f"SELECT 1 FROM {safe_schema}.{safe_table} WHERE {safe_col}::text = %s LIMIT 1"
                        with conn.cursor() as cur:
                            cur.execute(q,(h,))
                            if cur.fetchone():
                                hits[h].append(("EXACT",f"{schema}.{table}",col))
                    except Exception:
                        try: conn.rollback()
                        except Exception: pass

                # Broad payload search only in likely container fields.
                if any(x in col.lower() for x in ("payload","data","json","body","record")):
                    for h in target_hashes:
                        try:
                            q=f"SELECT 1 FROM {safe_schema}.{safe_table} WHERE {safe_col}::text LIKE %s LIMIT 1"
                            with conn.cursor() as cur:
                                cur.execute(q,(f"%{h}%",))
                                if cur.fetchone():
                                    hits[h].append(("PAYLOAD",f"{schema}.{table}",col))
                        except Exception:
                            try: conn.rollback()
                            except Exception: pass

            if table_idx % 10 == 0 or table_idx == len(grouped):
                found=sum(1 for v in hits.values() if v)
                print(
                    f"[POSTGRES INDEX] tables_scanned={table_idx}/{len(grouped)} "
                    f"hashes_found={found}/{len(target_hashes)}",
                    flush=True,
                )

        return {"status":"OK","hits":hits,"columns":columns}

    finally:
        try: conn.close()
        except Exception: pass


def main():
    print(LINE)
    print(" ORACLE PHYSICAL EVIDENCE-HASH PROVENANCE DIAGNOSTIC — FAST V2")
    print(" SINGLE-PASS LOCAL INDEX + BATCHED POSTGRESQL TRACE")
    print(LINE)

    raw=load_json(LEDGER)
    if raw is None:
        print(f"[ERROR] Could not load {LEDGER}")
        raise SystemExit(2)

    rows=ledger_records(raw)
    learned=[r for r in rows if status_of(r)=="learned" and evidence_hash_of(r)]
    sample=learned[:SAMPLE]

    print(f"[LEDGER] records={len(rows)} learned_with_evidence_hash={len(learned)}")
    print(f"[SAMPLE] tracing={len(sample)} known-good hashes")

    hashes=[evidence_hash_of(r) for r in sample]

    files=searchable_files()
    print(f"[LOCAL INDEX] searchable_files={len(files)}")
    local_hits=build_single_pass_hash_index(hashes,files)

    print("-"*96)
    print("[POSTGRES] Starting batch provenance search")
    pg=inspect_postgres_hashes(hashes)
    print(f"[POSTGRES] status={pg['status']}")

    print("="*96)
    print(" HASH-BY-HASH PROVENANCE")
    print("="*96)

    local_found=0
    pg_found=0
    locations=Counter()

    for idx,row in enumerate(sample,1):
        ticker=ticker_of(row)
        ehash=evidence_hash_of(row)
        shash=settlement_hash_of(row)
        sts=settlement_ts_of(row)

        lh=local_hits.get(ehash,[])
        ph=pg.get("hits",{}).get(ehash,[])

        if lh:
            local_found+=1
            for p,_ in lh:
                try: loc=str(p.relative_to(ROOT))
                except Exception: loc=str(p)
                locations[f"FILE:{loc}"]+=1

        if ph:
            pg_found+=1
            for kind,table,col in ph:
                locations[f"PG:{table}.{col}:{kind}"]+=1

        print(
            f"[{idx:02d}/{len(sample):02d}] "
            f"ticker={ticker} "
            f"evidence_hash={ehash[:16]}... "
            f"local_hits={len(lh)} postgres_hits={len(ph)} "
            f"settlement_hash={shash[:16]+'...' if shash else 'NONE'} "
            f"settlement_ts={sts or 'NONE'}"
        )

        for p,excerpt in lh[:2]:
            try: label=p.relative_to(ROOT)
            except Exception: label=p
            print(f"    [LOCAL] {label}")
            print(f"            {excerpt[:380]}")

        for kind,table,col in ph[:4]:
            print(f"    [POSTGRES] kind={kind} location={table}.{col}")

    print("="*96)
    print(" PROVENANCE SUMMARY")
    print("="*96)
    print(f"[KNOWN-GOOD HASHES TRACED] {len(sample)}")
    print(f"[FOUND IN LOCAL RUNTIME FILES] {local_found}")
    print(f"[FOUND IN POSTGRESQL] {pg_found}")

    if locations:
        print("[TOP PHYSICAL LOCATIONS]")
        for loc,count in locations.most_common(20):
            print(f"  {loc}: {count}")
    else:
        print("[TOP PHYSICAL LOCATIONS] NONE")

    if pg_found:
        print("[DIAGNOSIS] Known-good evidence hashes are physically recoverable in PostgreSQL.")
        print("[NEXT] Compare their exact storage table/column and market identity path against evidence_missing cases.")
    elif local_found:
        print("[DIAGNOSIS] Known-good evidence hashes are recoverable in runtime files but not PostgreSQL.")
        print("[NEXT] Trace the live learner's non-PostgreSQL evidence source or transformed persistence path.")
    else:
        print("[DIAGNOSIS] Known-good evidence hashes are not stored verbatim in searched runtime files or PostgreSQL.")
        print("[NEXT] Evidence hashes are likely derived from canonicalized content; trace the hash-generation function/source next.")

    print("[PASS] Fast provenance diagnostic performed read-only")
    print("[PASS] No PostgreSQL writes")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] OHL historical subsystem untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE FAST V2 EVIDENCE-HASH PROVENANCE DIAGNOSTIC COMPLETE")


if __name__=="__main__":
    main()
