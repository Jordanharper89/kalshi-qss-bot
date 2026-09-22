from __future__ import annotations
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SPORT_PATTERNS={
"baseball":(r"\bmlb\b",r"\bbaseball\b",r"\binnings?\b",r"\bhome runs?\b",r"\brbis?\b",r"\bpitcher\b",r"\bstrikeouts?\b"),
"hockey":(r"\bnhl\b",r"\bhockey\b",r"\bpuck\b",r"\bpower play\b"),
"basketball":(r"\bnba\b",r"\bwnba\b",r"\bbasketball\b",r"\brebounds?\b",r"\bassists?\b"),
"football":(r"\bnfl\b",r"\bamerican football\b",r"\btouchdowns?\b",r"\bpassing yards?\b",r"\brushing yards?\b"),
"soccer":(r"\bsoccer\b",r"\bpremier league\b",r"\bchampions league\b",r"\bla liga\b",r"\bserie a\b",r"\bbundesliga\b",r"\bligue 1\b",r"\bmls\b",r"\buefa\b",r"\bfifa\b"),
"tennis":(r"\batp\b",r"\bwta\b",r"\btennis\b",r"\bwimbledon\b",r"\bus open\b",r"\baustralian open\b",r"\bfrench open\b"),
"combat":(r"\bufc\b",r"\bmma\b",r"\bboxing\b",r"\bknockout\b",r"\bsubmission\b",r"\bko/tko\b"),
"golf":(r"\bpga\b",r"\blpga\b",r"\bgolf\b",r"\bmasters\b"),
"esports":(r"\besports?\b",r"\bleague of legends\b",r"\bcounter[- ]strike\b",r"\bvalorant\b",r"\bdota\b"),
}

IDENTITY=("ticker","market_ticker","event_ticker","series_ticker","title","subtitle","name","question","description","observation_id","source_id","entity_id")
PAYLOAD=("payload","raw_payload","source_payload","data","metadata","observation_payload","canonical_payload","value")

def _safe_ident(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",name): raise ValueError("unsafe identifier")
    return '"'+name+'"'

def _backend(root):
    router=build_existing_canonical_router(Path(root).resolve())
    backend=getattr(router,"_persistence_backend",None)
    if backend is None: raise RuntimeError("PostgreSQL backend unavailable")
    if not callable(getattr(backend,"_connect",None)): raise RuntimeError("audited backend._connect() unavailable")
    return backend

def _connect_read_only(root):
    conn=_backend(root)._connect()
    if conn is None: raise RuntimeError("backend._connect() returned None")
    with conn.cursor() as cur: cur.execute("BEGIN READ ONLY")
    return conn

def _schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog','information_schema')
        ORDER BY table_schema,table_name,ordinal_position
        """)
        rows=cur.fetchall()
    tables=defaultdict(list)
    for s,t,c,d in rows: tables[(s,t)].append((c,d))
    return tables

def _candidate_tables(tables):
    out=[]
    for (s,t),cols in tables.items():
        names=[c for c,_ in cols]
        ids=[c for c in IDENTITY if c in names]
        payload=[c for c in PAYLOAD if c in names]
        if ids or payload: out.append((s,t,ids,payload))
    return out

def _txt(v):
    if v is None: return ""
    if isinstance(v,(dict,list,tuple)): return json.dumps(v,sort_keys=True,default=str)
    return str(v)

def _classify(text):
    hits=[]
    for fam,patterns in SPORT_PATTERNS.items():
        m=[p for p in patterns if re.search(p,text,re.I)]
        if m: hits.append((fam,len(m),m))
    hits.sort(key=lambda x:(-x[1],x[0]))
    if not hits: return "UNKNOWN","NO_EXPLICIT_FAMILY_SIGNAL",()
    if len(hits)>1 and hits[0][1]==hits[1][1]:
        top=hits[0][1]; tied=tuple(x[0] for x in hits if x[1]==top)
        return "UNKNOWN","CONFLICTING_FAMILY_SIGNAL:"+",".join(tied),tied
    return hits[0][0],"EXPLICIT_POSTGRES_TEXT_SIGNAL",tuple(hits[0][2])

def _looks_sports(text):
    return bool(re.search(r"\b(sport|mlb|nhl|nba|wnba|nfl|soccer|tennis|atp|wta|ufc|mma|boxing|golf|pga|esport|goal|inning|touchdown|rebound|assist|pitcher|strikeout|home run|wimbledon|uefa|fifa)\b",text,re.I))

def _fetch(conn,schema,table,ids,payload,limit):
    cols=[]
    for c in ids+payload:
        if c not in cols: cols.append(c)
    if not cols: return []
    sql=f"SELECT {', '.join(_safe_ident(c) for c in cols)} FROM {_safe_ident(schema)}.{_safe_ident(table)} LIMIT %s"
    with conn.cursor() as cur:
        cur.execute(sql,(int(limit),)); rows=cur.fetchall()
    return [dict(zip(cols,row)) for row in rows]

def run_postgresql_unknown_sports_family_audit(root=None,row_limit_per_table=250000):
    root=Path(root or Path.cwd()).resolve()
    conn=_connect_read_only(root)
    report={"read_only":True,"execution_authority":False,"probability_enabled":False,"connection_path":"OraclePostgreSQLCanonicalObservationPersistenceBackend._connect()","transaction_mode":"BEGIN READ ONLY","tables":[],"family_counts":{},"reason_counts":{},"assignments":[],"still_unknown":[]}
    fam=Counter(); reasons=Counter(); seen=set()
    try:
        candidates=_candidate_tables(_schema(conn)); report["candidate_table_count"]=len(candidates)
        for schema,table,ids,payload in candidates:
            rows=_fetch(conn,schema,table,ids,payload,row_limit_per_table)
            report["tables"].append({"schema":schema,"table":table,"identity_columns":ids,"payload_columns":payload,"rows_read":len(rows)})
            for row in rows:
                joined=" | ".join(_txt(row.get(c)) for c in ids+payload if row.get(c) is not None).strip()
                if not joined or not _looks_sports(joined): continue
                key=(schema,table,joined[:4000])
                if key in seen: continue
                seen.add(key)
                family,reason,signals=_classify(joined)
                fam[family]+=1; reasons[reason]+=1
                rec={"schema":schema,"table":table,"family":family,"reason":reason,"signals":list(signals),"identity":{c:_txt(row.get(c))[:2000] for c in ids if row.get(c) is not None}}
                (report["still_unknown"] if family=="UNKNOWN" else report["assignments"]).append(rec)
        report["family_counts"]=dict(fam.most_common()); report["reason_counts"]=dict(reasons.most_common())
        jp=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_FULL_AUDIT.json"
        cp=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_ASSIGNMENTS.csv"
        up=root/"OAD_POSTGRESQL_STILL_UNKNOWN_SPORTS.csv"
        jp.write_text(json.dumps(report,indent=2,sort_keys=True,default=str),encoding="utf-8")
        with cp.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f); w.writerow(["family","reason","schema","table","signals","identity"])
            for r in report["assignments"]: w.writerow([r["family"],r["reason"],r["schema"],r["table"],json.dumps(r["signals"]),json.dumps(r["identity"],sort_keys=True)])
        with up.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f); w.writerow(["reason","schema","table","identity"])
            for r in report["still_unknown"]: w.writerow([r["reason"],r["schema"],r["table"],json.dumps(r["identity"],sort_keys=True)])
        conn.rollback()
        return report,jp,cp,up
    except Exception:
        conn.rollback(); raise
    finally:
        try: conn.close()
        except Exception: pass
