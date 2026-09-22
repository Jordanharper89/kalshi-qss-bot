from __future__ import annotations
from pathlib import Path
import json,os

from .olf_011_learned_experience_profile import (
    materialize_learned_experience_profiles,_connect,_db_url,
)

OLF_016_BUILD_ID="OLF-016"
OLF_016_REVISION="OLF_016_OUTCOME_ATTRIBUTED_PATTERN_EXPERIENCE_V1"
OUTPUT_NAME="oracle_outcome_attributed_pattern_experience.json"

def _float(v):
    try:
        if v in (None,""):return None
        x=float(v)
        if x>1.0 and x<=100.0:x/=100.0
        if 0.0<=x<=1.0:return x
    except Exception:pass
    return None

def _payload(raw):
    if isinstance(raw,str):
        try:raw=json.loads(raw)
        except Exception:return {}
    if not isinstance(raw,dict):return {}
    p=raw.get("payload")
    if isinstance(p,dict):return p
    r=raw.get("raw_observation")
    if isinstance(r,dict) and isinstance(r.get("payload"),dict):return r["payload"]
    return raw

def implied_yes_probability(raw):
    p=_payload(raw)
    bid=_float(p.get("yes_bid_dollars") or p.get("yes_bid"))
    ask=_float(p.get("yes_ask_dollars") or p.get("yes_ask"))
    if bid is not None and ask is not None:
        return max(0.0,min(1.0,(bid+ask)/2.0)),"YES_MID"
    last=_float(p.get("last_price_dollars") or p.get("last_price") or p.get("price"))
    if last is not None:return last,"LAST_PRICE"
    no_bid=_float(p.get("no_bid_dollars") or p.get("no_bid"))
    no_ask=_float(p.get("no_ask_dollars") or p.get("no_ask"))
    if no_bid is not None and no_ask is not None:
        return max(0.0,min(1.0,1.0-(no_bid+no_ask)/2.0)),"NO_MID_INVERTED"
    prev=_float(p.get("previous_price_dollars"))
    if prev is not None:return prev,"PREVIOUS_PRICE"
    return None,"NO_PRICE"

def normalize_result(v):
    s=str(v or "").strip().lower()
    if s in ("yes","y","1","true"):return "yes"
    if s in ("no","n","0","false"):return "no"
    return ""

def _table_columns(cur,table):
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s",(table,)
    )
    return {str(r[0]) for r in cur.fetchall()}

def _outcomes(cur,settlement_hashes):
    candidates=(
        "oracle_production_learning_ledger",
        "oracle_grounded_learning_outcome_ledger",
    )
    out={}
    for table in candidates:
        cols=_table_columns(cur,table)
        if not {"settlement_hash","result"}.issubset(cols):continue
        for pos in range(0,len(settlement_hashes),500):
            batch=settlement_hashes[pos:pos+500]
            cur.execute(
                f"SELECT settlement_hash,result FROM public.{table} "
                "WHERE settlement_hash = ANY(%s)",(batch,)
            )
            for h,result in cur.fetchall():
                r=normalize_result(result)
                if r:out.setdefault(str(h),r)
    return out

def build_outcome_attributed_experience(root=None):
    root=Path(root or Path.cwd()).resolve()
    profiles=materialize_learned_experience_profiles(root)
    hashes=[str(x.get("evidence_hash") or "") for x in profiles.get("profiles",[]) if x.get("evidence_hash")]
    settlements=[str(x.get("settlement_hash") or "") for x in profiles.get("profiles",[]) if x.get("settlement_hash")]
    evidence={}
    conn=_connect(_db_url(root))
    try:
        try:conn.set_session(readonly=True,autocommit=False)
        except Exception:pass
        cur=conn.cursor()
        for pos in range(0,len(hashes),500):
            batch=hashes[pos:pos+500]
            cur.execute(
                """SELECT content_hash,observation_id,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE content_hash = ANY(%s) OR observation_id = ANY(%s)""",
                (batch,batch),
            )
            for h,oid,raw in cur.fetchall():
                for key in (str(h or ""),str(oid or "")):
                    if key:evidence.setdefault(key,raw)
        outcomes=_outcomes(cur,settlements)
        try:conn.rollback()
        except Exception:pass
    finally:conn.close()

    rows=[]
    for x in profiles.get("profiles",[]):
        raw=evidence.get(str(x.get("evidence_hash") or ""))
        prob,price_source=implied_yes_probability(raw)
        result=outcomes.get(str(x.get("settlement_hash") or ""),"")
        actual=1.0 if result=="yes" else 0.0 if result=="no" else None
        scored=prob is not None and actual is not None
        rows.append({
            **x,
            "settlement_result":result,
            "implied_yes_probability":prob,
            "probability_source":price_source,
            "scored":scored,
            "predicted_side":("yes" if prob>=.5 else "no") if prob is not None else "",
            "prediction_hit":bool((prob>=.5)==(actual==1.0)) if scored else None,
            "brier_score":((prob-actual)**2) if scored else None,
        })
    return {
        "revision":OLF_016_REVISION,
        "learner_state_hash":profiles["learner_state_hash"],
        "learned_records":profiles["learned_records"],
        "outcome_attributed":sum(1 for x in rows if x["settlement_result"]),
        "probability_recovered":sum(1 for x in rows if x["implied_yes_probability"] is not None),
        "scored_records":sum(1 for x in rows if x["scored"]),
        "records":rows,
        "execution_authority":False,
    }

def materialize_outcome_attributed_experience(root=None):
    root=Path(root or Path.cwd()).resolve();payload=build_outcome_attributed_experience(root)
    path=root/"runtime_state"/OUTPUT_NAME;tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path);return payload

def verify_olf_016_outcome_attributed_pattern_experience():
    p,s=implied_yes_probability({"payload":{"yes_bid_dollars":"0.40","yes_ask_dollars":"0.60"}})
    return OLF_016_BUILD_ID=="OLF-016" and abs(p-.5)<1e-9 and s=="YES_MID" and normalize_result("YES")=="yes"
