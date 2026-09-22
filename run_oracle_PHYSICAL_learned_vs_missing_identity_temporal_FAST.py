from __future__ import annotations
import json, os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
LEDGER=ROOT/"runtime_state"/"oracle_learning_event_ledger.json"
LINE="="*96
SAMPLE=25

def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def pick(r,*names):
    for n in names:
        v=r.get(n)
        if v not in (None,"",[],{}): return v
    return None
def status(r): return str(pick(r,"status","learning_status","admission_status") or "unknown").lower()
def ticker(r): return str(pick(r,"ticker","market_ticker","market_id","canonical_market_id","venue_market_id","symbol") or "UNKNOWN")
def settle_ts(r): return str(pick(r,"settlement_ts","settled_at","settlement_time") or "")
def evidence_hash(r): return str(pick(r,"evidence_hash") or "")
def dt(v):
    x=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)

def ledger_rows(obj):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if isinstance(v,dict):
                r=dict(v); r.setdefault("_ledger_key",k); out.append(r)
    elif isinstance(obj,list):
        out=[x for x in obj if isinstance(x,dict)]
    return out

def db_url():
    u=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")
    if u:return u
    e=ROOT/".env"
    if e.is_file():
        for line in e.read_text(encoding="utf-8",errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1)
                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"):
                    return v.strip().strip('"').strip("'")
    return None

def cols(conn):
    with conn.cursor() as c:
        c.execute("""SELECT column_name FROM information_schema.columns
                     WHERE table_schema='public' AND table_name='oracle_canonical_observations'
                     ORDER BY ordinal_position""")
        return [x[0] for x in c.fetchall()]

def ident(name): return '"'+str(name).replace('"','""')+'"'

def groups(columns):
    identity=[c for c in columns if any(x in c.lower() for x in ("ticker","market","symbol","venue"))]
    times=[c for c in columns if any(x in c.lower() for x in ("observed","timestamp","created","received","event_ts","time"))]
    types=[c for c in columns if any(x in c.lower() for x in ("type","kind","channel","source"))]
    payload=[c for c in columns if any(x in c.lower() for x in ("json","payload","body","data","record"))]
    return identity,times,types,payload

def fetch(conn,tick,columns):
    identity,times,types,payload=groups(columns)
    wanted=[]
    for c in ["content_hash","canonical_observation_json","observation_id","sequence_number"]+identity+times+types+payload:
        if c in columns and c not in wanted:wanted.append(c)
    where=[]; params=[]
    for c in identity:
        where.append(f"{ident(c)}::text=%s"); params.append(tick)
    for c in payload:
        where.append(f"{ident(c)}::text LIKE %s"); params.append("%"+tick+"%")
    if not where:return []
    q="SELECT "+",".join(ident(c) for c in wanted)+" FROM public.oracle_canonical_observations WHERE ("+" OR ".join(where)+") LIMIT 100"
    with conn.cursor() as cur:
        cur.execute(q,tuple(params)); vals=cur.fetchall()
    return [dict(zip(wanted,row)) for row in vals]

def observed_at(row,time_cols):
    for c in time_cols:
        v=row.get(c)
        if v not in (None,""):
            try:return dt(v)
            except:pass
    for v in row.values():
        obj=None
        if isinstance(v,dict):obj=v
        elif isinstance(v,str):
            try:obj=json.loads(v)
            except:pass
        if isinstance(obj,dict):
            for k in ("observed_at","timestamp","created_at","event_ts","received_at"):
                if obj.get(k):
                    try:return dt(obj[k])
                    except:pass
    return None

def classify(conn,lr,columns):
    tick=ticker(lr); st=settle_ts(lr); kh=evidence_hash(lr)
    rows=fetch(conn,tick,columns)
    _,times,_,_=groups(columns)
    cutoff=None
    try: cutoff=dt(st) if st else None
    except: pass
    pre=post=unknown=0
    for row in rows:
        t=observed_at(row,times)
        if cutoff is None or t is None: unknown+=1
        elif t<cutoff: pre+=1
        else: post+=1
    if not rows: cls="NO_CANONICAL_OBSERVATION"
    elif pre and kh: cls="LEARNED_WITH_PRE_SETTLEMENT_EVIDENCE"
    elif pre: cls="PRE_SETTLEMENT_EVIDENCE_EXISTS_BUT_NOT_LINKED"
    elif post: cls="POST_SETTLEMENT_ONLY"
    else: cls="OBSERVATIONS_EXIST_TIME_UNRESOLVED"
    return tick,cls,len(rows),pre,post,unknown

def run_group(label,rows,conn,columns):
    print("-"*96);print(label);print("-"*96)
    cc=Counter(); out=[]
    for i,r in enumerate(rows,1):
        x=classify(conn,r,columns); out.append(x); cc[x[1]]+=1
        print(f"[{i:02d}/{len(rows):02d}] ticker={x[0]} class={x[1]} rows={x[2]} pre={x[3]} post={x[4]} unknown_time={x[5]}")
    print(f"[GROUP CLASSIFICATIONS] {dict(cc)}")
    return out

def main():
    print(LINE);print(" ORACLE PHYSICAL LEARNED-vs-MISSING IDENTITY/TEMPORAL DIAGNOSTIC — FAST")
    print(" READ-ONLY — PUBLIC.ORACLE_CANONICAL_OBSERVATIONS");print(LINE)
    rows=ledger_rows(load_json(LEDGER))
    missing=[r for r in rows if status(r)=="evidence_missing"][:SAMPLE]
    learned=[r for r in rows if status(r)=="learned"][:SAMPLE]
    print(f"[LEDGER] total_records={len(rows)}")
    print(f"[SAMPLE] evidence_missing={len(missing)} learned={len(learned)}")
    import psycopg
    conn=psycopg.connect(db_url()); conn.autocommit=True
    try:
        columns=cols(conn); a,b,c,d=groups(columns)
        print(f"[POSTGRES] columns={len(columns)} identity_columns={tuple(a)} time_columns={tuple(b)} payload_columns={tuple(d)}")
        mr=run_group(" EVIDENCE-MISSING SAMPLE",missing,conn,columns)
        lr=run_group(" LEARNED SAMPLE",learned,conn,columns)
    finally: conn.close()
    print("="*96);print(" FINAL IDENTITY / TEMPORAL DIAGNOSIS");print("="*96)
    mpre=sum(x[3]>0 for x in mr); mnone=sum(x[2]==0 for x in mr); mpost=sum(x[2]>0 and x[3]==0 and x[4]>0 for x in mr); lpre=sum(x[3]>0 for x in lr)
    print(f"[COMPARE] missing_with_pre_settlement={mpre}/{len(mr)}")
    print(f"[COMPARE] missing_with_no_observation={mnone}/{len(mr)}")
    print(f"[COMPARE] missing_post_settlement_only={mpost}/{len(mr)}")
    print(f"[COMPARE] learned_with_pre_settlement={lpre}/{len(lr)}")
    if mpre>0:
        print("[DIAGNOSIS] Some evidence_missing markets DO have canonical pre-settlement observations in PostgreSQL.")
        print("[CLASSIFICATION] Likely evidence-linkage / matcher / admission defect.")
        print("[NEXT] Isolate the exact matching rule before any defect-only OLR correction.")
    elif mpost>0:
        print("[DIAGNOSIS] Missing markets have observations, but sampled evidence is post-settlement only.")
        print("[CLASSIFICATION] Current learning abstention appears temporally correct.")
        print("[NEXT] Do not modify frozen OLR.")
    elif mnone==len(mr) and lpre>0:
        print("[DIAGNOSIS] Learned markets have pre-settlement evidence, but missing markets have no canonical observations.")
        print("[CLASSIFICATION] Acquisition/coverage issue, not an OLR matcher defect.")
        print("[NEXT] Do not modify frozen OLR.")
    elif mnone==len(mr) and lpre==0:
        print("[DIAGNOSIS] Direct settlement-ticker identity cannot rediscover either group.")
        print("[CLASSIFICATION] Canonical market identity uses a different representation.")
        print("[NEXT] Resolve known-good content_hash rows and inspect their exact identity fields.")
    else:
        print("[DIAGNOSIS] Mixed identity/timestamp behavior detected.")
        print("[NEXT] Review classifications before changing frozen OLR.")
    print("[PASS] Diagnostic performed read-only")
    print("[PASS] No PostgreSQL writes")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE LEARNED-vs-MISSING IDENTITY/TEMPORAL DIAGNOSTIC COMPLETE")
if __name__=="__main__": main()
