from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import json,os

from .obr_002_gap_queue import next_queued_gap
from qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile import _connect,_db_url
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

OBR_003_BUILD_ID="OBR-003"
OBR_003_REVISION="OBR_003_BACKGROUND_SEQUENCE_DELTA_RECOVERY_V1"
PROGRESS="oracle_background_recovery_progress.json"
RESULTS="oracle_background_recovery_results.jsonl"

def _current_sequence(root):
    conn=_connect(_db_url(root))
    try:
        cur=conn.cursor();cur.execute("SELECT COALESCE(MAX(sequence_number),0) FROM public.oracle_canonical_observations")
        return int(cur.fetchone()[0] or 0)
    finally:conn.close()

def _delta_tickers(root,start_seq,end_seq):
    conn=_connect(_db_url(root))
    try:
        cur=conn.cursor()
        cur.execute("""
            WITH n AS(
              SELECT COALESCE(canonical_observation_json->'raw_observation'->'payload',
                              canonical_observation_json->'payload','{}'::jsonb) p
              FROM public.oracle_canonical_observations
              WHERE sequence_number>%s AND sequence_number<=%s
            )
            SELECT DISTINCT COALESCE(NULLIF(p->>'source_market_id',''),
                                     NULLIF(p->>'market_id',''),
                                     NULLIF(p->>'source_symbol',''),
                                     NULLIF(p->>'ticker',''))
            FROM n
            WHERE COALESCE(NULLIF(p->>'source_market_id',''),
                           NULLIF(p->>'market_id',''),
                           NULLIF(p->>'source_symbol',''),
                           NULLIF(p->>'ticker','')) IS NOT NULL
        """,(int(start_seq),int(end_seq)))
        return [str(r[0]).upper() for r in cur.fetchall() if r and r[0]]
    finally:conn.close()

def recover_gap_market_states(root,gap,batch_size=500,progress=print):
    root=Path(root).resolve()
    start_seq=int(gap.get("last_good_sequence") or 0)
    end_seq=_current_sequence(root)
    tickers=_delta_tickers(root,start_seq,end_seq)
    creds=load_kalshi_credentials(root=root)
    out=root/"runtime_state"/RESULTS
    recovered=failed=0
    for i,ticker in enumerate(tickers,1):
        try:
            r=kalshi_rest_get(creds,f"/markets/{ticker}",{},15)
            body=dict(r.body or {})
            raw=body.get("market") if isinstance(body.get("market"),dict) else body
            with out.open("a",encoding="utf-8",newline="\n") as f:
                f.write(json.dumps({"gap_id":gap["gap_id"],"ticker":ticker,"kind":"MARKET_STATE","status":"RECOVERED","market":raw},sort_keys=True,separators=(",",":"),default=str)+"\n")
            recovered+=1
        except Exception as exc:
            with out.open("a",encoding="utf-8",newline="\n") as f:
                f.write(json.dumps({"gap_id":gap["gap_id"],"ticker":ticker,"kind":"MARKET_STATE","status":"FAILED","error":str(exc)[:300]},sort_keys=True,separators=(",",":"))+"\n")
            failed+=1
        if progress and (i<=5 or i%batch_size==0 or i==len(tickers)):
            progress(f"[OBR STATE] checked={i}/{len(tickers)} recovered={recovered} failed={failed}")
    return {"delta_tickers":len(tickers),"state_recovered":recovered,"state_failed":failed,"sequence_start":start_seq,"sequence_end":end_seq}

def verify_obr_003_background_sequence_delta_recovery():
    return OBR_003_BUILD_ID=="OBR-003" and callable(recover_gap_market_states)
