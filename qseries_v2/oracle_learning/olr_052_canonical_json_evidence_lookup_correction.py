from __future__ import annotations
from pathlib import Path
import json

OLR_052_BUILD_ID="OLR-052"
OLR_052_REVISION="OLR_052_CANONICAL_JSON_EVIDENCE_LOOKUP_CORRECTION_V2"

def _connect(root=None):
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    return connect(root)

def outcome_identity(outcome):
    if hasattr(outcome,"get"):
        ticker=str(outcome.get("ticker") or outcome.get("market_ticker") or "").strip()
        market_id=str(outcome.get("market_id") or ticker).strip()
        observation_id=str(outcome.get("observation_id") or "").strip() or None
    else:
        ticker=str(getattr(outcome,"ticker","") or getattr(outcome,"market_ticker","")).strip()
        market_id=str(getattr(outcome,"market_id","") or ticker).strip()
        observation_id=str(getattr(outcome,"observation_id","") or "").strip() or None
    return ticker,market_id,observation_id

def json_load(value):
    if value is None:
        return {}
    if isinstance(value,dict):
        return value
    if isinstance(value,(bytes,bytearray,memoryview)):
        value=bytes(value).decode("utf-8","ignore")
    if isinstance(value,str):
        try:
            parsed=json.loads(value)
            return parsed if isinstance(parsed,dict) else {}
        except Exception:
            return {}
    return {}

def extract_identity(payload,source_observation_id=None):
    payload=payload or {}

    ticker=""
    market_id=""

    direct_ticker_keys=("ticker","market_ticker","marketTicker","symbol")
    direct_market_keys=("market_id","marketId","market","market_ticker","ticker")

    for key in direct_ticker_keys:
        value=payload.get(key)
        if value not in (None,""):
            ticker=str(value).strip()
            if ticker:
                break

    for key in direct_market_keys:
        value=payload.get(key)
        if value not in (None,"") and not isinstance(value,dict):
            market_id=str(value).strip()
            if market_id:
                break

    nested_candidates=(
        payload.get("market"),
        payload.get("data"),
        payload.get("payload"),
        payload.get("observation"),
        payload.get("metadata"),
    )

    for nested in nested_candidates:
        if not isinstance(nested,dict):
            continue

        if not ticker:
            for key in direct_ticker_keys:
                value=nested.get(key)
                if value not in (None,""):
                    ticker=str(value).strip()
                    if ticker:
                        break

        if not market_id:
            for key in direct_market_keys:
                value=nested.get(key)
                if value not in (None,"") and not isinstance(value,dict):
                    market_id=str(value).strip()
                    if market_id:
                        break

        if ticker and market_id:
            break

    source_id=str(source_observation_id or "").strip()

    if not ticker and source_id:
        ticker=source_id
    if not market_id and source_id:
        market_id=source_id
    if not market_id:
        market_id=ticker
    if not ticker:
        ticker=market_id

    return ticker,market_id

def lookup_market_evidence(outcome,root=None,limit=200):
    root=Path(root or Path.cwd()).resolve()
    ticker,market_id,observation_id=outcome_identity(outcome)

    if not ticker and not market_id and not observation_id:
        return ()

    scan_limit=max(int(limit)*50,5000)

    sql="""
        SELECT
            observation_id,
            source_observation_id,
            sequence_number,
            observed_at,
            canonical_observation_json
        FROM public.oracle_canonical_observations
        ORDER BY sequence_number DESC
        LIMIT %s
    """

    candidates=[]

    with _connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(scan_limit,))
            rows=cur.fetchall()

    for row in rows:
        obs_id=row[0]
        source_obs_id=row[1]
        sequence_number=row[2]
        observed_at=row[3]
        payload=json_load(row[4])

        cand_ticker,cand_market=extract_identity(payload,source_obs_id)

        exact_obs=bool(observation_id and str(obs_id)==str(observation_id))
        ticker_match=bool(ticker and cand_ticker==ticker)
        market_match=bool(market_id and cand_market==market_id)

        if exact_obs or ticker_match or market_match:
            candidates.append({
                "observation_id":obs_id,
                "ticker":cand_ticker,
                "market_ticker":cand_ticker,
                "market_id":cand_market,
                "source_observation_id":source_obs_id,
                "sequence_number":sequence_number,
                "observed_at":observed_at,
                "canonical_observation_json":payload,
            })

            if len(candidates)>=int(limit):
                break

    return tuple(candidates)

def verify_olr_052_canonical_json_evidence_lookup_correction(root=None):
    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze
    ticker,market=extract_identity({"ticker":"KXTEST"},None)
    return (
        verify_olr_050_production_evidence_learning_activation_freeze(root)
        and OLR_052_BUILD_ID=="OLR-052"
        and ticker=="KXTEST"
        and market=="KXTEST"
        and callable(lookup_market_evidence)
    )
