from pathlib import Path
import json,time
import hashlib,os

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import OracleKalshiPublicMarketShadowSourceAdapter
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect as _opd_exo_connect

EXECUTION_AUTHORITY=False
PUBLICATION_ALLOWED=False
HURDLE=0.020
MIN_NET_EDGE=0.005
MIN_CASES=20
MIN_TICKERS=3
MIN_DIRECTION_PROB=0.58
MIN_MEAN_SIMILARITY=0.20
MAX_STATE_AGE_SECONDS=120.0
MAX_NEIGHBORS=100
CATEGORIES=("K","CB","CC","L")
HORIZONS=(5,15,30,60,300,900,3600)


# EXOGENOUS_EVIDENCE_FREEZE_ROOT_DISCOVERED_LEDGER_V1

_EXO_ALLOW=("usgs","weather","official","macro","economic","news","network","solana","onchain",
            "chain","provider","condition","event","calendar","release","announcement","gmgn")
_EXO_DENY=("kalshi","coinbase","price","return","spread","volume","orderbook","bid","ask",
           "midpoint","last_trade","anchor_price","future","outcome","resolution","pnl","profit")

def _opd_exogenous_freeze_snapshot(state):
    if not isinstance(state,dict):
        return {}
    raw=state.get("exogenous_evidence_state")
    if not isinstance(raw,dict) or not raw:
        return {}
    out={}
    for k in sorted(raw):
        v=raw.get(k)
        if not isinstance(v,dict):
            continue
        sid=str(v.get("source_id") or "")
        typ=str(v.get("observation_type") or "")
        low=(sid+" "+typ).lower()
        deny=("kalshi","coinbase","polymarket","market_data","orderbook",
              "prediction","learned_case","historical_window")
        if any(x in low for x in deny):
            continue
        out[str(k)]={
            "sequence_number":v.get("sequence_number"),
            "observed_epoch":v.get("observed_epoch"),
            "source_id":sid,
            "observation_type":typ,
            "canonical_observation":v.get("canonical_observation"),
        }
        if len(out)>=64:
            break
    return out

def _rows(p):
    out=[]
    if not p.exists(): return out
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def _asset(ticker):
    u=str(ticker or "").upper().strip()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return None


def _cats(tokens):
    d={k:set() for k in CATEGORIES}
    for x in tokens or []:
        s=str(x)
        if ":" not in s: continue
        p=s.split(":",1)[0]
        if p in d:d[p].add(s)
    return d

def _jaccard(a,b):
    if not a and not b:return None
    u=a|b
    return len(a&b)/len(u) if u else None

def _similarity(a,b):
    ca,cb=_cats(a),_cats(b); vals=[]
    for k in CATEGORIES:
        if ca[k]:
            z=_jaccard(ca[k],cb[k])
            if z is not None: vals.append(z)
    return sum(vals)/len(vals) if vals else 0.0

def _weighted_mean(pairs):
    sw=sum(w for w,_ in pairs)
    return None if sw<=0 else sum(w*x for w,x in pairs)/sw

def _anchor_from_row(row):
    seq,oid,outer_epoch,obj=row
    p=canonical_point(obj,float(outer_epoch))
    if not p:return None
    asset=_asset(p["ticker"])
    if not asset:return None
    return {
      "anchor_id":str(oid),"ticker":p["ticker"],"asset":asset,
      "observed_epoch":float(p["event_epoch"]),"anchor_price":float(p["price"]),
      "anchor_sequence_boundary":int(seq),"anchor_sequence_basis":"EXACT_CANONICAL_OBSERVATION",
      "kalshi_state":{"sequence_number":int(seq),"event_epoch":float(p["event_epoch"]),
        "trade_price":float(p["price"]),"yes_bid":None,"yes_ask":None,"spread":None,
        "yes_bid_size":None,"yes_ask_size":None,"last_trade_size":None,"volume":None,
        "open_interest":None,"observation_type":"canonical_market_data",
        "event_time_path":"OPD046_CANONICAL_POINT"},"post_freeze":True,
    }

def _iso_epoch(value):
    if value is None:return None
    text=str(value).strip()
    if not text:return None
    try:
        from datetime import datetime,timezone
        if text.endswith('Z'):text=text[:-1]+'+00:00'
        dt=datetime.fromisoformat(text)
        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
        return float(dt.timestamp())
    except Exception:return None

def _public_contract_close_metadata(ticker,adapter_cls=OracleKalshiPublicMarketShadowSourceAdapter):
    try:
        from datetime import datetime,timezone
        adapter=adapter_cls(
            market_status="open",
            market_tickers=(str(ticker),),
            page_limit=1,
            max_pages=1,
            timeout_seconds=10,
        )
        rows=adapter.acquire(acquired_at=datetime.now(timezone.utc))
    except Exception as e:
        return {'close_epoch':None,'metadata_sequence':None,
          'basis':'PUBLIC_CLOSE_LOOKUP_FAILED_'+type(e).__name__.upper()}
    for obs in rows:
        payload=dict(obs.payload)
        if str(payload.get('source_market_id') or '') != str(ticker):
            continue
        epoch=_iso_epoch(payload.get('source_close_time'))
        if epoch is not None:
            return {'close_epoch':epoch,'metadata_sequence':None,
              'basis':'LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME'}
        return {'close_epoch':None,'metadata_sequence':None,
          'basis':'INVALID_LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME'}
    return {'close_epoch':None,'metadata_sequence':None,
      'basis':'NO_LIVE_PUBLIC_KALSHI_MARKET_METADATA'}

def _contract_close_metadata(root,ticker):
    sql=f"""SELECT sequence_number,
      COALESCE(canonical_observation_json->'raw_observation'->'payload',
               canonical_observation_json->'payload','{{}}'::jsonb)->>'source_close_time'
      FROM public.oracle_canonical_observations
      WHERE observation_type='market_snapshot'
        AND ({MARKET_ID_EXPRESSION})=%s
      ORDER BY sequence_number DESC LIMIT 1"""
    row=None
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute('SET TRANSACTION READ ONLY')
                q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute(sql,(str(ticker),));row=q.fetchone()
            c.rollback()
    except Exception:
        row=None
    if row:
        epoch=_iso_epoch(row[1])
        if epoch is not None:
            return {'close_epoch':epoch,'metadata_sequence':int(row[0]),
              'basis':'INDEXED_CANONICAL_SOURCE_CLOSE_TIME'}
    return _public_contract_close_metadata(ticker)

def latest_live_anchor(root):
    sql='''SELECT sequence_number,observation_id,EXTRACT(EPOCH FROM observed_at),canonical_observation_json
           FROM public.oracle_canonical_observations
           WHERE source_id=%s
             AND ((canonical_observation_json->'payload'->>'source_market_id') ILIKE '%%BTC%%'
               OR (canonical_observation_json->'payload'->>'source_market_id') ILIKE '%%ETH%%'
               OR (canonical_observation_json->'payload'->>'source_market_id') ILIKE '%%SOL%%')
           ORDER BY sequence_number DESC LIMIT 64'''
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='5000ms'")
            q.execute(sql,(SOURCE,)); rows=q.fetchall() or []
        c.rollback()
    for row in rows:
        a=_anchor_from_row(row)
        if a:
            meta=_contract_close_metadata(root,a['ticker'])
            a['contract_close_epoch']=meta['close_epoch']
            a['contract_close_metadata_sequence']=meta['metadata_sequence']
            a['contract_close_basis']=meta['basis']
            return a
    return None

def _opd_exogenous_source_eligible(anchor,sid,typ,obj):
    sid=str(sid or ""); typ=str(typ or ""); low=(sid+" "+typ).lower()
    deny=("kalshi","coinbase","polymarket","prospective_forecast","prospective_binding",
          "experience","learned_case","prediction","outcome","resolution","profit","pnl",
          "historical_window","market_data","orderbook","sports.","source.sports")
    if any(x in low for x in deny):
        return False
    ticker=str((anchor or {}).get("ticker") or "").upper()
    asset="BTC" if ticker.startswith("KXBTC") else "ETH" if ticker.startswith("KXETH") else "SOL" if ticker.startswith("KXSOL") else None
    words={"BTC":("btc","bitcoin"),"ETH":("eth","ethereum"),"SOL":("sol","solana")}
    all_words=("btc","bitcoin","eth","ethereum","sol","solana")
    if asset:
        mentions_asset=any(x in low for x in all_words)
        if mentions_asset and not any(x in low for x in words[asset]):
            return False
    if "gmgn" in low:
        return asset=="SOL" and ("solana" in low or ".sol" in low)
    allow=("usgs","weather","official","macro","economic","economy","network","onchain",
           "on_chain","chain","mempool","block","provider","event","calendar","release",
           "announcement","ethereum","solana","bitcoin","btc","eth","sol")
    return any(x in low for x in allow)

def _opd_load_exogenous_canonical_asof(anchor,root):
    root=Path(root or Path.cwd()).resolve()
    try:
        seq=int(anchor["anchor_sequence_boundary"]); t=float(anchor["observed_epoch"])
    except Exception:
        return {}
    sql="""SELECT sequence_number,source_id,observation_type,
                  EXTRACT(EPOCH FROM observed_at),canonical_observation_json
           FROM public.oracle_canonical_observations
           WHERE sequence_number<=%s AND observed_at<=to_timestamp(%s)
           ORDER BY sequence_number DESC LIMIT 4096"""
    out={}
    try:
        with _opd_exo_connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='12000ms'")
                q.execute(sql,(seq,t)); rows=q.fetchall() or []
            c.rollback()
    except Exception as e:
        print("[EXOGENOUS ASOF READ ERROR]",type(e).__name__,str(e)[:220]); return {}
    for rseq,sid,typ,obs_epoch,obj in rows:
        if not _opd_exogenous_source_eligible(anchor,sid,typ,obj):
            continue
        key=str(sid or "")+"|"+str(typ or "")
        if key in out:
            continue
        try: oe=float(obs_epoch)
        except Exception: oe=None
        if int(rseq)>seq or (oe is not None and oe>t):
            continue
        out[key]={"sequence_number":int(rseq),"observed_epoch":oe,
                  "source_id":str(sid or ""),"observation_type":str(typ or ""),
                  "canonical_observation":obj}
        if len(out)>=64:
            break
    return out

def materialize_current_states(anchor,root):
    extra=assemble(anchor,root)
    exogenous=_opd_load_exogenous_canonical_asof(anchor,root)
    extra=dict(extra)
    extra["exogenous_evidence_state"]=exogenous
    out=[]
    for h in HORIZONS:
        world={"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":anchor["observed_epoch"],"horizon_seconds":h,
          "anchor_price":anchor["anchor_price"],"kalshi_state":anchor["kalshi_state"],
          "coinbase_hf_state":extra["coinbase_hf_state"],
          "crypto_condition_state":extra["crypto_condition_state"],
          "learned_state":extra["learned_state"],
          "exogenous_evidence_state":exogenous}
        out.append({"state_id":"LIVE_IN_MEMORY_"+anchor["anchor_id"]+"_"+str(h),
          "anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":float(anchor["observed_epoch"]),"horizon_seconds":h,
          "anchor_price":anchor["anchor_price"],
          "contract_close_epoch":anchor.get("contract_close_epoch"),
          "contract_close_basis":anchor.get("contract_close_basis"),
          "exogenous_evidence_state":exogenous,
          "tokens":list(materialize_exact_live_tokens(root,world))})
    return out,extra


PROSPECTIVE_EDGE_GATE_REVISION="PROSPECTIVE_REALIZED_EDGE_GATE_V1"
PROSPECTIVE_EDGE_MIN_N=12
PROSPECTIVE_EDGE_MIN_TICKERS=3
PROSPECTIVE_EDGE_Z=1.2815515655446004
PROSPECTIVE_EDGE_PROB_BIN=0.10
PROSPECTIVE_EDGE_AGREE_BIN=0.25

def _prospective_contract_family(ticker):
    u=str(ticker or "").upper()
    if u.startswith("KXBTC15M") or u.startswith("KXETH15M") or u.startswith("KXSOL15M"):
        return "CRYPTO_15M"
    if u.startswith("KXBTCD") or u.startswith("KXETHD") or u.startswith("KXSOLD"):
        return "CRYPTO_DAILY_THRESHOLD"
    if u.startswith("KXBTC-") or u.startswith("KXETH-") or u.startswith("KXSOL-"):
        return "CRYPTO_RANGE"
    if u.startswith("KXBTC") or u.startswith("KXETH") or u.startswith("KXSOL"):
        return "CRYPTO_OTHER"
    return "NON_CRYPTO"

def _prospective_bin(v,width):
    try:
        x=float(v)
    except Exception:
        return None
    x=max(0.0,min(1.0,x))
    return round(int(x/width)*width,6)

def _prospective_rows(root):
    p=Path(root)/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    return _rows(p)

def _prospective_resolution_epoch(row):
    for k in ("resolution_epoch","resolved_epoch","outcome_resolved_epoch","materialized_epoch"):
        try:
            v=row.get(k)
            if v is not None:
                return float(v)
        except Exception:
            pass
    return None

def _prospective_segment_stats(score,root,cutoff_epoch):
    st=score.get("state") or {}
    asset=str(score.get("asset") or _asset(st.get("ticker")) or "")
    horizon=int(score.get("horizon_seconds") or 0)
    direction=str(score.get("direction") or "")
    family=_prospective_contract_family(st.get("ticker"))
    pbin=_prospective_bin(score.get("predicted_probability"),PROSPECTIVE_EDGE_PROB_BIN)
    abin=_prospective_bin(score.get("evidence_agreement"),PROSPECTIVE_EDGE_AGREE_BIN)

    eligible=[]
    for r in _prospective_rows(root):
        if r.get("resolution_status")!="RESOLVED_EXACT_FUTURE":
            continue
        resolved_at=_prospective_resolution_epoch(r)
        if resolved_at is None or resolved_at>float(cutoff_epoch):
            continue
        rticker=str(r.get("ticker") or "")
        if _asset(rticker)!=asset:
            continue
        try:
            if int(r.get("horizon_seconds") or -1)!=horizon:
                continue
        except Exception:
            continue
        if str(r.get("predicted_direction") or r.get("direction") or "")!=direction:
            continue
        if _prospective_contract_family(rticker)!=family:
            continue
        if _prospective_bin(r.get("predicted_probability"),PROSPECTIVE_EDGE_PROB_BIN)!=pbin:
            continue
        if _prospective_bin(r.get("evidence_agreement"),PROSPECTIVE_EDGE_AGREE_BIN)!=abin:
            continue
        try:
            dr=float(r.get("directional_return"))
        except Exception:
            continue
        eligible.append((r,dr-HURDLE))

    n=len(eligible)
    tickers=len({str(r.get("ticker") or "") for r,_ in eligible})
    vals=[v for _,v in eligible]
    mean=(sum(vals)/n) if n else None
    if n>=2:
        var=sum((v-mean)**2 for v in vals)/(n-1)
        sd=var**0.5
        se=sd/(n**0.5)
        lower=mean-PROSPECTIVE_EDGE_Z*se
    else:
        sd=se=lower=None
    positive=sum(1 for v in vals if v>0)
    return {
      "revision":PROSPECTIVE_EDGE_GATE_REVISION,
      "segment":{
        "asset":asset,"contract_family":family,"horizon_seconds":horizon,
        "direction":direction,"probability_bin":pbin,"agreement_bin":abin,
      },
      "n":n,"unique_tickers":tickers,"mean_net_after_2pct":mean,
      "net_stddev":sd,"net_standard_error":se,"lower_bound_net_after_2pct":lower,
      "positive_net_rate":(positive/n) if n else None,
      "strict_cutoff_epoch":float(cutoff_epoch),
    }

def _prospective_gate_apply(score,root=None):
    root=Path(root or Path.cwd()).resolve()
    st=score.get("state") or {}
    cutoff=float(st.get("observed_epoch") or 0.0)
    stats=_prospective_segment_stats(score,root,cutoff)
    ok=(
      stats["n"]>=PROSPECTIVE_EDGE_MIN_N and
      stats["unique_tickers"]>=PROSPECTIVE_EDGE_MIN_TICKERS and
      stats["lower_bound_net_after_2pct"] is not None and
      stats["lower_bound_net_after_2pct"]>0.0
    )
    score["prospective_realized_edge"]=stats
    score["checks"]["prospective_realized_edge"]=bool(ok)
    score["passed"]=all(score["checks"].values())
    return score

def _score_state(cur,states,outcomes,now):
    score=_score_state_preprospective(cur,states,outcomes,now)
    return _prospective_gate_apply(score,Path.cwd())

def _score_state_preprospective(cur,states,outcomes,now):
    h=int(cur["horizon_seconds"]); asset=_asset(cur.get("ticker"));t=float(cur["observed_epoch"]);hist=[]
    for s in states:
        if s.get("state_id")==cur.get("state_id") or int(s.get("horizon_seconds",-1))!=h:continue
        if asset and _asset(s.get("ticker"))!=asset:continue
        if float(s.get("observed_epoch",0))>=t:continue
        o=outcomes.get(s.get("state_id"))
        if not o or float(o.get("resolution_epoch",1e99))>t:continue
        sim=_similarity(cur.get("tokens") or [],s.get("tokens") or [])
        if sim<=0:continue
        try:r=float(o["future_return"]);mfe=float(o["mfe"]);mae=float(o["mae"])
        except Exception:continue
        hist.append((sim,s,o,r,mfe,mae))
    hist.sort(key=lambda z:(z[0],float(z[1].get("observed_epoch",0))),reverse=True);hist=hist[:MAX_NEIGHBORS]
    n=len(hist);tickers=len({x[1].get("ticker") for x in hist});mean_sim=sum(x[0] for x in hist)/n if n else 0.0
    mean_ret=_weighted_mean([(x[0],x[3]) for x in hist])
    if hist:
        sw=sum(x[0] for x in hist);up_prob=sum(x[0]*(1.0 if x[3]>0 else .5 if x[3]==0 else 0.0) for x in hist)/sw
        mean_mfe=sum(x[0]*x[4] for x in hist)/sw;mean_mae=sum(x[0]*x[5] for x in hist)/sw
    else:up_prob=mean_mfe=mean_mae=None
    direction=prob=None
    if up_prob is not None:
        direction="UP" if up_prob>=.5 else "DOWN";prob=up_prob if direction=="UP" else 1.0-up_prob
    directional_return=None if mean_ret is None else (mean_ret if direction=="UP" else -mean_ret)
    net=None if directional_return is None else directional_return-HURDLE
    curcats=_cats(cur.get("tokens") or []);votes={}
    for k in CATEGORIES:
        if not curcats[k]:continue
        pairs=[]
        for _,s,o,r,_,_ in hist:
            z=_jaccard(curcats[k],_cats(s.get("tokens") or [])[k])
            if z and z>0:pairs.append((z,r))
        m=_weighted_mean(pairs);votes[k]={"cases":len(pairs),"mean_return":m,"direction":None if m is None or abs(m)<1e-12 else ("UP" if m>0 else "DOWN")}
    directional_votes=[v["direction"] for v in votes.values() if v["direction"]]
    agree=(sum(v==direction for v in directional_votes)/len(directional_votes)) if direction and directional_votes else None
    age=max(0.0,float(now)-t)
    close_epoch=cur.get('contract_close_epoch')
    try:close_epoch=None if close_epoch is None else float(close_epoch)
    except Exception:close_epoch=None
    remaining=None if close_epoch is None else close_epoch-t
    horizon_eligible=close_epoch is not None and (t+float(h))<=close_epoch
    checks={"fresh_state":age<=MAX_STATE_AGE_SECONDS,"contract_horizon":horizon_eligible,"comparable_cases":n>=MIN_CASES,
      "ticker_breadth":tickers>=MIN_TICKERS,"mean_similarity":mean_sim>=MIN_MEAN_SIMILARITY,
      "direction_probability":prob is not None and prob>=MIN_DIRECTION_PROB,
      "net_edge":net is not None and net>=MIN_NET_EDGE,
      "evidence_agreement":agree is not None and len(directional_votes)>=2 and agree>=0.60}
    return {"state":cur,"asset":asset,"horizon_seconds":h,"age_seconds":age,"comparable_cases":n,
      "unique_tickers":tickers,"mean_similarity":mean_sim,"direction":direction,"predicted_probability":prob,
      "expected_return":directional_return,"net_edge_after_2pct":net,"expected_mfe":mean_mfe,"expected_mae":mean_mae,
      "evidence_votes":votes,
            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(cur),"evidence_agreement":agree,"contract_close_epoch":close_epoch,
      "contract_remaining_seconds":remaining,"horizon_eligible":horizon_eligible,
      "checks":checks,"passed":all(checks.values())}

PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
PREDICTION_LEDGER_REVISION="FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1"

def _prediction_id(anchor,horizon_seconds,generation=2,family_id=None):
    parts=[
      PREDICTION_LEDGER_REVISION,
      str(anchor.get("anchor_id") or ""),
      str(anchor.get("anchor_sequence_boundary") or ""),
      str(anchor.get("ticker") or ""),
      str(int(horizon_seconds)),
    ]
    generation=int(generation or 2)
    if generation!=2 or family_id:
        parts.extend(["GEN",str(generation),"FAMILY",str(family_id or "")])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

def _freeze_predictions(root,anchor,scores,frozen_epoch):
    path=Path(root)/"runtime"/"predictive_data"/PREDICTION_LEDGER_NAME
    path.parent.mkdir(parents=True,exist_ok=True)
    known=set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    pid=json.loads(line).get("prediction_id")
                    if pid: known.add(str(pid))
                except Exception:
                    pass
    frozen=duplicates=0
    with path.open("a",encoding="utf-8") as f:
        for z in scores:
            h=int(z["horizon_seconds"])
            pid=_prediction_id(anchor,h,z.get("generation",2),z.get("family_id"))
            if pid in known:
                duplicates+=1
                continue
            st=z["state"]
            row={
              "prediction_id":pid,
              "revision":PREDICTION_LEDGER_REVISION,
              "generation":int(z.get("generation") or 2),
              "family_id":z.get("family_id"),
              "model_basis":z.get("model_basis") or "FULL_EVIDENCE_CURRENT_MODEL",
              "gen1_formula":z.get("gen1_formula"),
              "gen1_target":z.get("gen1_target"),
              "gen1_original_activation_epoch":z.get("gen1_original_activation_epoch"),
              "prospective_realized_edge":z.get("prospective_realized_edge"),
              "prediction_frozen_epoch":float(frozen_epoch),
              "anchor_id":anchor.get("anchor_id"),
              "anchor_sequence_boundary":anchor.get("anchor_sequence_boundary"),
              "ticker":st.get("ticker"),
              "asset":z.get("asset"),
              "market_title":anchor.get("market_title"),
              "market_subtitle":anchor.get("market_subtitle"),
              "yes_sub_title":anchor.get("yes_sub_title"),
              "no_sub_title":anchor.get("no_sub_title"),
              "floor_strike":anchor.get("floor_strike"),
              "cap_strike":anchor.get("cap_strike"),
              "functional_strike":anchor.get("functional_strike"),
              "yes_semantic":anchor.get("yes_semantic"),
              "anchor_observed_epoch":float(st.get("observed_epoch")),
              "anchor_price":st.get("anchor_price"),
              "horizon_seconds":h,
              "resolution_due_epoch":float(st.get("observed_epoch"))+h,
              "contract_close_epoch":z.get("contract_close_epoch"),
              "contract_close_basis":anchor.get("contract_close_basis"),
              "horizon_eligible":bool(z.get("horizon_eligible")),
              "direction":z.get("direction"),
              "predicted_probability":z.get("predicted_probability"),
              "expected_return":z.get("expected_return"),
              "net_edge_after_2pct":z.get("net_edge_after_2pct"),
              "comparable_cases":int(z.get("comparable_cases") or 0),
              "unique_tickers":int(z.get("unique_tickers") or 0),
              "mean_similarity":z.get("mean_similarity"),
              "evidence_agreement":z.get("evidence_agreement"),
              "evidence_votes":z.get("evidence_votes"),
              "exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {},
              "checks":dict(z.get("checks") or {}),
              "actionable_at_freeze":bool(z.get("passed")),
              "decision_at_freeze":z.get("direction") if z.get("passed") else "ABSTAIN",
              "evidence_tokens":list(st.get("tokens") or []),
              "profitability_status":"PROSPECTIVE_UNRESOLVED",
              "certified":False,
              "publication_allowed":False,
              "execution_authority":False,
            }
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
            f.flush();os.fsync(f.fileno())
            known.add(pid);frozen+=1
    return {"path":str(path),"frozen":frozen,"duplicates":duplicates}


GENERATION_CHALLENGER_REVISION="GEN1_GEN2_PROSPECTIVE_CHALLENGER_V1"
GEN1_FREEZE_NAME="opd_031_prospective_candidate_freeze.json"
GEN1_MIN_RESOLVED=12
GEN1_MIN_TICKERS=3
GEN1_Z=1.2815515655446004

def _gen1_target_direction(target):
    return "DOWN" if str(target) in ("DOWN_5C","DOWN_10C","RETURN_NEG") else "UP"

def _gen1_load_freeze(root):
    p=Path(root)/"runtime"/"predictive_data"/GEN1_FREEZE_NAME
    if not p.exists():
        raise RuntimeError("ORIGINAL_GEN1_OPD031_FREEZE_MISSING")
    body=json.loads(p.read_text(encoding="utf-8"))
    if body.get("schema_version")!="OPD-031":
        raise RuntimeError("INVALID_GEN1_OPD031_FREEZE")
    if body.get("formula_retuning_allowed") is not False:
        raise RuntimeError("GEN1_FORMULA_RETUNING_BOUNDARY_VIOLATED")
    return body

def _gen1_prior_stats(root,family_id,horizon,direction,cutoff_epoch):
    vals=[];tickers=set()
    p=Path(root)/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    for r in _rows(p):
        if r.get("resolution_status")!="RESOLVED_EXACT_FUTURE":
            continue
        if int(r.get("generation") or 2)!=1:
            continue
        if str(r.get("family_id") or "")!=str(family_id or ""):
            continue
        try:
            if int(r.get("horizon_seconds") or -1)!=int(horizon):
                continue
            resolved_at=float(r.get("resolved_epoch"))
            dr=float(r.get("directional_return"))
        except Exception:
            continue
        if resolved_at>float(cutoff_epoch):
            continue
        if str(r.get("direction") or "")!=str(direction):
            continue
        vals.append(dr-HURDLE)
        tickers.add(str(r.get("ticker") or ""))
    n=len(vals);mean=(sum(vals)/n) if n else None
    if n>=2:
        var=sum((x-mean)**2 for x in vals)/(n-1)
        sd=var**0.5;se=sd/(n**0.5);lower=mean-GEN1_Z*se
    else:
        sd=se=lower=None
    return {
      "revision":GENERATION_CHALLENGER_REVISION,
      "generation":1,"family_id":family_id,"n":n,
      "unique_tickers":len(tickers),
      "mean_net_after_2pct":mean,"net_stddev":sd,
      "net_standard_error":se,
      "lower_bound_net_after_2pct":lower,
      "strict_cutoff_epoch":float(cutoff_epoch),
    }

def _gen1_challenger_scores(root,base_scores,now):
    root=Path(root).resolve()
    freeze=_gen1_load_freeze(root)
    out=[]
    for c in freeze.get("candidates") or []:
        h=int(c.get("horizon_seconds") or -1)
        direction=_gen1_target_direction(c.get("target"))
        formula=list(c.get("formula") or [])
        for base in base_scores:
            if int(base.get("horizon_seconds") or -2)!=h:
                continue
            st=base.get("state") or {}
            toks=set(st.get("tokens") or [])
            match=all(str(x) in toks for x in formula)
            if not match:
                continue
            stats=_gen1_prior_stats(
                root,c.get("family_id"),h,direction,
                float(st.get("observed_epoch") or 0.0)
            )
            support=stats["n"]>=GEN1_MIN_RESOLVED and stats["unique_tickers"]>=GEN1_MIN_TICKERS
            positive=stats["lower_bound_net_after_2pct"] is not None and stats["lower_bound_net_after_2pct"]>0.0
            fresh=bool((base.get("checks") or {}).get("fresh_state"))
            horizon_ok=bool((base.get("checks") or {}).get("contract_horizon"))
            checks={
              "fresh_state":fresh,
              "contract_horizon":horizon_ok,
              "gen1_exact_frozen_formula_match":True,
              "gen1_prospective_support":support,
              "gen1_prospective_realized_edge":positive,
            }
            mean_net=stats["mean_net_after_2pct"]
            lower=stats["lower_bound_net_after_2pct"]
            z={
              "generation":1,
              "family_id":c.get("family_id"),
              "model_basis":"ORIGINAL_FROZEN_OPD031_GEN1",
              "gen1_formula":formula,
              "gen1_target":c.get("target"),
              "gen1_original_activation_epoch":freeze.get("activation_epoch"),
              "state":dict(st),
              "asset":base.get("asset"),
              "horizon_seconds":h,
              "age_seconds":base.get("age_seconds"),
              "comparable_cases":stats["n"],
              "unique_tickers":stats["unique_tickers"],
              "mean_similarity":1.0,
              "direction":direction,
              "predicted_probability":None,
              "expected_return":None if mean_net is None else mean_net+HURDLE,
              "net_edge_after_2pct":lower,
              "expected_mfe":None,"expected_mae":None,
              "evidence_votes":{"GEN1":{"cases":stats["n"],"direction":direction,
                 "mean_return":None if mean_net is None else mean_net+HURDLE}},
              "evidence_agreement":1.0,
              "contract_close_epoch":base.get("contract_close_epoch"),
              "contract_remaining_seconds":base.get("contract_remaining_seconds"),
              "horizon_eligible":horizon_ok,
              "prospective_realized_edge":stats,
              "checks":checks,
              "passed":all(checks.values()),
            }
            z["state"]["state_id"]="GEN1:"+str(c.get("family_id"))+":"+str(st.get("state_id"))
            out.append(z)
    return out

def _run_single_contract(root=None,now=None,anchor=None):
    root=Path(root or Path.cwd()).resolve();now=float(time.time() if now is None else now);rt=root/"runtime"/"predictive_data"
    history=_rows(rt/"opd_032_prospective_state_ledger.jsonl")
    outcomes={x.get("state_id"):x for x in _rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
    print("="*112);print("ORACLE LIVE FULL-EVIDENCE FUSION PREDICTOR — FRESH CANONICAL CUTOVER");print("="*112)
    anchor=anchor or latest_live_anchor(root)
    if not anchor:
        print("LIVE_PREDICTION=ABSTAIN");print("REASON=NO_LIVE_CANONICAL_CRYPTO_ANCHOR");print("EXECUTION_AUTHORITY=FALSE");return None
    print("LIVE_ANCHOR_TICKER=",anchor["ticker"]);print("LIVE_ANCHOR_SEQUENCE=",anchor.get("anchor_sequence_boundary"))
    print("LIVE_ANCHOR_AGE_SECONDS=",max(0.0,now-float(anchor["observed_epoch"])))
    print("CONTRACT_CLOSE_EPOCH=",anchor.get("contract_close_epoch"))
    print("CONTRACT_CLOSE_BASIS=",anchor.get("contract_close_basis"))
    print("CONTRACT_CLOSE_METADATA_SEQUENCE=",anchor.get("contract_close_metadata_sequence"))
    current,extra=materialize_current_states(anchor,root)
    print("LIVE_EVIDENCE_COINBASE_WINDOWS=",sorted(extra["coinbase_hf_state"].keys()))
    print("LIVE_EVIDENCE_CONDITION_METRICS=",len(extra["crypto_condition_state"]));print("LIVE_EVIDENCE_LEARNED=",bool(extra["learned_state"]));print("LIVE_EVIDENCE_EXOGENOUS_SOURCES=",len(extra.get("exogenous_evidence_state") or {}))
    scores=[_score_state(x,history,outcomes,now) for x in current]
    for _z in scores:
        _z.setdefault("generation",2)
        _z.setdefault("model_basis","FULL_EVIDENCE_CURRENT_MODEL")
    gen1_scores=_gen1_challenger_scores(root,scores,now)
    scores.extend(gen1_scores)
    if gen1_scores:
        print("[GEN1 CHALLENGER] exact_formula_matches=",len(gen1_scores),
              "actionable=",sum(1 for x in gen1_scores if x.get("passed")),
              "original_freeze=OPD-031")
    ledger=_freeze_predictions(root,anchor,scores,now)
    print("[PREDICTION LEDGER] frozen=",ledger["frozen"],"duplicates=",ledger["duplicates"],"path=",ledger["path"])
    for z in scores:
        print("-"*112);print("GENERATION=",z.get("generation",2),"MODEL_BASIS=",z.get("model_basis"));print("TICKER=",z["state"]["ticker"],"HORIZON=",z["horizon_seconds"],"AGE_SECONDS=",round(z["age_seconds"],3))
        print("EVIDENCE_TOKENS=",len(z["state"].get("tokens") or []),"K/CB/CC/L=",{k:len(_cats(z["state"].get("tokens") or [])[k]) for k in CATEGORIES})
        print("COMPARABLE_CASES=",z["comparable_cases"],"UNIQUE_TICKERS=",z["unique_tickers"],"MEAN_SIMILARITY=",round(z["mean_similarity"],6))
        print("EVIDENCE_VOTES=",json.dumps(z["evidence_votes"],sort_keys=True,separators=(",",":")));print("EVIDENCE_AGREEMENT=",z["evidence_agreement"])
        print("DIRECTION=",z["direction"],"PREDICTED_PROBABILITY=",z["predicted_probability"]);print("EXPECTED_RETURN=",z["expected_return"],"NET_EDGE_AFTER_2PCT=",z["net_edge_after_2pct"])
        print("CONTRACT_REMAINING_SECONDS=",z["contract_remaining_seconds"],"HORIZON_ELIGIBLE=",z["horizon_eligible"])
        failed=[k for k,v in z["checks"].items() if not v];print("DECISION="+(z["direction"] if z["passed"] else "ABSTAIN"),"FAILED_GATES="+("NONE" if not failed else ",".join(failed)))
    passed=[z for z in scores if z["passed"]];print("="*112)
    if passed:
        best=max(passed,key=lambda z:(float(z["net_edge_after_2pct"]),float(z["predicted_probability"])))
        print("LIVE_PREDICTION=",best["direction"]);print("TICKER=",best["state"]["ticker"]);print("HORIZON_SECONDS=",best["horizon_seconds"])
        print("PREDICTED_PROBABILITY=",best["predicted_probability"]);print("EXPECTED_RETURN=",best["expected_return"]);print("NET_EXPECTED_EDGE_AFTER_2PCT=",best["net_edge_after_2pct"])
        print("COMPARABLE_CASES=",best["comparable_cases"]);print("UNIQUE_TICKERS=",best["unique_tickers"]);print("EVIDENCE_AGREEMENT=",best["evidence_agreement"]);print("PROFITABILITY_STATUS=LIVE_CANDIDATE_UNPROVEN")
    else:
        print("LIVE_PREDICTION=ABSTAIN");print("REASON=NO_HORIZON_PASSES_FULL_EVIDENCE_LIVE_DECISION_GATES")
    print("CERTIFIED=FALSE");print("PUBLICATION_ALLOWED=FALSE");print("EXECUTION_AUTHORITY=FALSE");return scores

EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_REVISION="EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1"
MAX_FAMILY_CONTRACTS=12
FAMILY_SOURCE_SCAN_ROWS=2048

def _market_spec_from_payload(payload):
    if not isinstance(payload,dict):
        return {}
    return {
      "market_title":payload.get("market_title") or payload.get("title"),
      "market_subtitle":payload.get("subtitle"),
      "yes_sub_title":payload.get("yes_sub_title"),
      "no_sub_title":payload.get("no_sub_title"),
      "floor_strike":payload.get("floor_strike"),
      "cap_strike":payload.get("cap_strike"),
      "functional_strike":payload.get("functional_strike"),
      "source_close_time":payload.get("source_close_time"),
    }

def _canonical_exact_market_spec(root,ticker):
    sql=f"""SELECT COALESCE(
      canonical_observation_json->'raw_observation'->'payload',
      canonical_observation_json->'payload','{{}}'::jsonb)
      FROM public.oracle_canonical_observations
      WHERE observation_type='market_snapshot'
        AND ({MARKET_ID_EXPRESSION})=%s
      ORDER BY sequence_number DESC LIMIT 1"""
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute(sql,(str(ticker),))
                row=q.fetchone()
            c.rollback()
        if row and isinstance(row[0],dict):
            spec=_market_spec_from_payload(row[0])
            spec["market_spec_basis"]="INDEXED_CANONICAL_MARKET_SNAPSHOT"
            return spec
    except Exception:
        pass
    return {}

def _public_exact_market_specs(tickers):
    tickers=tuple(dict.fromkeys(str(x) for x in tickers if x))
    if not tickers:
        return {}
    try:
        from datetime import datetime,timezone
        from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
            OracleKalshiPublicMarketShadowSourceAdapter,
        )
        adapter=OracleKalshiPublicMarketShadowSourceAdapter(
            market_status="open",
            market_tickers=tickers,
            page_limit=max(1,min(1000,len(tickers))),
            max_pages=1,
            timeout_seconds=20,
        )
        observations=adapter.acquire(acquired_at=datetime.now(timezone.utc))
        out={}
        for obs in observations:
            payload=dict(obs.payload)
            ticker=str(payload.get("source_market_id") or "")
            if not ticker:
                continue
            spec=_market_spec_from_payload(payload)
            spec["market_spec_basis"]="LIVE_PUBLIC_KALSHI_EXACT_TICKER"
            out[ticker]=spec
        return out
    except Exception:
        return {}

def _yes_semantic(spec):
    text=" ".join(str(spec.get(k) or "") for k in (
        "market_title","market_subtitle","yes_sub_title","no_sub_title"
    )).lower()
    high=("above","over ","greater than","at least","or more","higher than")
    low=("below","under ","less than","at most","or less","lower than")
    if any(x in text for x in high):
        return "YES_MEANS_UNDERLYING_HIGHER"
    if any(x in text for x in low):
        return "YES_MEANS_UNDERLYING_LOWER"
    if "price up" in text or "be up" in text or "go up" in text:
        return "YES_MEANS_UNDERLYING_HIGHER"
    if "price down" in text or "be down" in text or "go down" in text:
        return "YES_MEANS_UNDERLYING_LOWER"
    return "UNRESOLVED_EXACT_CONTRACT_SEMANTICS"

def _underlying_view(contract_direction,yes_semantic):
    d=str(contract_direction or "").upper()
    if d not in ("UP","DOWN"):
        return "UNRESOLVED"
    if yes_semantic=="YES_MEANS_UNDERLYING_HIGHER":
        return "BULLISH" if d=="UP" else "BEARISH"
    if yes_semantic=="YES_MEANS_UNDERLYING_LOWER":
        return "BEARISH" if d=="UP" else "BULLISH"
    return "CONTRACT_SPECIFIC_UNRESOLVED"

REALTIME_FAMILY_ANCHOR_ROOT_REVISION="REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1"
REALTIME_FAMILY_MAX_AGE_SECONDS=120.0
REALTIME_FAMILY_SPOOL_TAIL_BYTES=8388608

def _tail_realtime_anchor_spool(root):
    p=Path(root)/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl"
    if not p.exists(): return []
    try:
        size=p.stat().st_size
        with p.open("rb") as f:
            start=max(0,size-REALTIME_FAMILY_SPOOL_TAIL_BYTES); f.seek(start); data=f.read()
        if start:
            k=data.find(b"\n"); data=data[k+1:] if k>=0 else b""
        out=[]
        for raw in data.splitlines():
            try:
                row=json.loads(raw.decode("utf-8"))
                if isinstance(row,dict) and row.get("schema_version")=="OPD-061": out.append(row)
            except Exception: pass
        return out
    except Exception: return []

def _validated_realtime_anchor(row,now=None):
    if not isinstance(row,dict): return None
    ticker=str(row.get("ticker") or "").strip(); asset=_asset(ticker)
    if not asset or str(row.get("asset") or "").upper()!=asset: return None
    try: observed=float(row["observed_epoch"]); price=float(row["anchor_price"]); seq=int(row["anchor_sequence_boundary"])
    except Exception: return None
    if not (0.0<=price<=1.0) or seq<0: return None
    now=float(time.time() if now is None else now)
    if max(0.0,now-observed)>REALTIME_FAMILY_MAX_AGE_SECONDS: return None
    a=dict(row); a["asset"]=asset; a["ticker"]=ticker; a["observed_epoch"]=observed; a["anchor_price"]=price
    a["anchor_sequence_boundary"]=seq; a["anchor_sequence_basis"]=row.get("anchor_sequence_basis") or "CANONICAL_HIGHWATER_AT_FREEZE"
    a["realtime_anchor_basis"]="OPD061_REALTIME_TRADE_TICKER_SPOOL"
    return a

def _latest_realtime_spool_anchor(root,now=None):
    best=None
    for row in _tail_realtime_anchor_spool(root):
        a=_validated_realtime_anchor(row,now)
        if a is not None and (best is None or a["observed_epoch"]>best["observed_epoch"]): best=a
    return best

def _recent_asset_anchor_universe(root,asset,lead,now=None):
    asset=str(asset or "").upper(); now=float(time.time() if now is None else now); anchors=[]; seen=set()
    realtime=[]
    for row in _tail_realtime_anchor_spool(root):
        a=_validated_realtime_anchor(row,now)
        if a is not None and a.get("asset")==asset: realtime.append(a)
    realtime.sort(key=lambda x:float(x.get("observed_epoch") or 0),reverse=True)
    for a in realtime:
        ticker=str(a.get("ticker"))
        if ticker in seen: continue
        meta=_contract_close_metadata(root,ticker)
        a["contract_close_epoch"]=meta.get("close_epoch"); a["contract_close_metadata_sequence"]=meta.get("metadata_sequence"); a["contract_close_basis"]=meta.get("basis")
        anchors.append(a); seen.add(ticker)
        if len(anchors)>=MAX_FAMILY_CONTRACTS: return anchors
    like="%"+asset+"%"
    sql="SELECT sequence_number,observation_id,EXTRACT(EPOCH FROM observed_at),canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND (canonical_observation_json->'payload'->>'source_market_id') ILIKE %s ORDER BY sequence_number DESC LIMIT %s"
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='7000ms'"); q.execute(sql,(SOURCE,like,int(FAMILY_SOURCE_SCAN_ROWS))); rows=q.fetchall() or []
            c.rollback()
    except Exception: rows=[]
    for row in rows:
        a=_anchor_from_row(row)
        if not a or _asset(a.get("ticker"))!=asset: continue
        ticker=str(a.get("ticker"))
        if ticker in seen: continue
        try: age=max(0.0,now-float(a.get("observed_epoch")))
        except Exception: age=999999.0
        if age>REALTIME_FAMILY_MAX_AGE_SECONDS: continue
        meta=_contract_close_metadata(root,ticker)
        a["contract_close_epoch"]=meta.get("close_epoch"); a["contract_close_metadata_sequence"]=meta.get("metadata_sequence"); a["contract_close_basis"]=meta.get("basis"); a["realtime_anchor_basis"]="CANONICAL_FALLBACK"
        anchors.append(a); seen.add(ticker)
        if len(anchors)>=MAX_FAMILY_CONTRACTS: break
    return anchors


def _enrich_anchor_contract_specs(root,anchors):
    canonical={}
    need_public=[]
    for a in anchors:
        ticker=str(a.get("ticker"))
        spec=_canonical_exact_market_spec(root,ticker)
        canonical[ticker]=spec
        if not spec.get("market_title") and not spec.get("yes_sub_title"):
            need_public.append(ticker)

    public=_public_exact_market_specs(need_public)
    for a in anchors:
        ticker=str(a.get("ticker"))
        spec=dict(canonical.get(ticker) or {})
        if ticker in public:
            for k,v in public[ticker].items():
                if v is not None:
                    spec[k]=v
        for k in (
            "market_title","market_subtitle","yes_sub_title","no_sub_title",
            "floor_strike","cap_strike","functional_strike","market_spec_basis",
        ):
            a[k]=spec.get(k)
        a["yes_semantic"]=_yes_semantic(spec)

        if a.get("contract_close_epoch") is None and spec.get("source_close_time"):
            epoch=_iso_epoch(spec.get("source_close_time"))
            if epoch is not None:
                a["contract_close_epoch"]=epoch
                a["contract_close_basis"]="EXACT_MARKET_SPEC_SOURCE_CLOSE_TIME"
    return anchors

def _print_contract_identity(anchor):
    print("[EXACT CONTRACT]")
    print("TICKER=",anchor.get("ticker"))
    print("ASSET=",anchor.get("asset"))
    print("MARKET_TITLE=",anchor.get("market_title"))
    print("MARKET_SUBTITLE=",anchor.get("market_subtitle"))
    print("YES_SUB_TITLE=",anchor.get("yes_sub_title"))
    print("NO_SUB_TITLE=",anchor.get("no_sub_title"))
    print("FLOOR_STRIKE=",anchor.get("floor_strike"),
          "CAP_STRIKE=",anchor.get("cap_strike"),
          "FUNCTIONAL_STRIKE=",anchor.get("functional_strike"))
    print("YES_SEMANTIC=",anchor.get("yes_semantic"))
    print("MARKET_SPEC_BASIS=",anchor.get("market_spec_basis"))

def run(root=None,now=None,anchor=None):
    root=Path(root or Path.cwd()).resolve()
    now=float(time.time() if now is None else now)

    if anchor is not None:
        spec_anchor=_enrich_anchor_contract_specs(root,[dict(anchor)])[0]
        _print_contract_identity(spec_anchor)
        return _run_single_contract(root=root,now=now,anchor=spec_anchor)

    lead=_latest_realtime_spool_anchor(root,now) or latest_live_anchor(root)
    if not lead:
        print("LIVE_PREDICTION=ABSTAIN")
        print("REASON=NO_LIVE_CANONICAL_CRYPTO_ANCHOR")
        print("EXECUTION_AUTHORITY=FALSE")
        return None

    asset=lead.get("asset") or _asset(lead.get("ticker"))
    anchors=_recent_asset_anchor_universe(root,asset,lead,now)
    anchors=_enrich_anchor_contract_specs(root,anchors)

    print("="*112)
    print("ORACLE EXACT CONTRACT FAMILY ROOT CUTOVER")
    print("ASSET_FAMILY=",asset)
    print("CONTRACTS_WITH_EXACT_CANONICAL_PRICE_ANCHORS=",len(anchors))
    print("FAMILY_REVISION=",EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_REVISION)
    print("="*112)

    family_scores=[]
    for i,a in enumerate(anchors,1):
        print("#"*112)
        print("CONTRACT_FAMILY_MEMBER=",i,"OF",len(anchors))
        _print_contract_identity(a)
        scores=_run_single_contract(root=root,now=now,anchor=a) or []
        for z in scores:
            z["market_title"]=a.get("market_title")
            z["market_subtitle"]=a.get("market_subtitle")
            z["yes_sub_title"]=a.get("yes_sub_title")
            z["no_sub_title"]=a.get("no_sub_title")
            z["floor_strike"]=a.get("floor_strike")
            z["cap_strike"]=a.get("cap_strike")
            z["functional_strike"]=a.get("functional_strike")
            z["yes_semantic"]=a.get("yes_semantic")
            z["underlying_view"]=_underlying_view(z.get("direction"),a.get("yes_semantic"))
            family_scores.append(z)

    passed=[z for z in family_scores if z.get("passed")]
    passed.sort(key=lambda z:(
        float(z.get("net_edge_after_2pct") or -999),
        float(z.get("predicted_probability") or 0),
    ),reverse=True)

    print("="*112)
    print("EXACT CONTRACT FAMILY RANKING")
    print("ASSET=",asset)
    print("ACTIONABLE_CONTRACT_HORIZONS=",len(passed))
    for rank,z in enumerate(passed[:20],1):
        st=z["state"]
        print("-"*112)
        print("RANK=",rank)
        print("TICKER=",st.get("ticker"))
        print("MARKET_TITLE=",z.get("market_title"))
        print("YES_SUB_TITLE=",z.get("yes_sub_title"))
        print("NO_SUB_TITLE=",z.get("no_sub_title"))
        print("STRIKE_FLOOR/CAP/FUNCTIONAL=",
              z.get("floor_strike"),z.get("cap_strike"),z.get("functional_strike"))
        print("HORIZON_SECONDS=",z.get("horizon_seconds"))
        print("CONTRACT_YES_PRICE_VIEW=",z.get("direction"))
        print("UNDERLYING_"+str(asset)+"_VIEW=",z.get("underlying_view"))
        print("PREDICTED_PROBABILITY=",z.get("predicted_probability"))
        print("NET_EXPECTED_EDGE_AFTER_2PCT=",z.get("net_edge_after_2pct"))
        print("EVIDENCE_AGREEMENT=",z.get("evidence_agreement"))

    if passed:
        best=passed[0]
        print("="*112)
        print("FAMILY_BEST_TICKER=",best["state"].get("ticker"))
        print("FAMILY_BEST_MARKET_TITLE=",best.get("market_title"))
        print("FAMILY_BEST_HORIZON_SECONDS=",best.get("horizon_seconds"))
        print("FAMILY_BEST_CONTRACT_YES_PRICE_VIEW=",best.get("direction"))
        print("FAMILY_BEST_UNDERLYING_"+str(asset)+"_VIEW=",best.get("underlying_view"))
        print("FAMILY_BEST_PREDICTED_PROBABILITY=",best.get("predicted_probability"))
        print("FAMILY_BEST_NET_EDGE_AFTER_2PCT=",best.get("net_edge_after_2pct"))
    else:
        print("FAMILY_BEST=ABSTAIN")

    print("PROFITABILITY_STATUS=LIVE_CANDIDATE_UNPROVEN")
    print("CERTIFIED=FALSE")
    print("PUBLICATION_ALLOWED=FALSE")
    print("EXECUTION_AUTHORITY=FALSE")
    return family_scores

if __name__=="__main__":
    run()
