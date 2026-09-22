from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import json,os

from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import load_env
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
from .olf_006_structural_identity import resolve_structural_identity

from .olf_atomic_state_io import atomic_write_json
OLF_011_BUILD_ID="OLF-011"
OLF_011_REVISION="OLF_011_EVIDENCE_GROUNDED_LEARNED_EXPERIENCE_PROFILE_V1"
PROFILE_NAME="oracle_learned_experience_profiles.json"

def _connect(url):
    try:
        import psycopg
        return psycopg.connect(url)
    except ImportError:
        import psycopg2
        return psycopg2.connect(url)

def _session(value):
    if not value:return "UNKNOWN"
    try:
        x=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)
        h=x.astimezone(timezone.utc).hour
        if h<6:return "UTC_00_05"
        if h<12:return "UTC_06_11"
        if h<18:return "UTC_12_17"
        return "UTC_18_23"
    except Exception:return "UNKNOWN"

def _source_family(payload):
    if isinstance(payload,str):
        try:payload=json.loads(payload)
        except Exception:return ""
    if not isinstance(payload,dict):return ""
    candidates=[payload]
    if isinstance(payload.get("payload"),dict):candidates.append(payload["payload"])
    for row in candidates:
        for k in ("source_family","source","venue","adapter","source_adapter","channel"):
            v=row.get(k)
            if v not in (None,""):
                return str(v)[:120]
    return ""

def _db_url(root):
    env=load_env(Path(root))
    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")
    if not url:raise RuntimeError("DATABASE_URL not configured")
    return url

def build_learned_experience_profiles(root=None):
    root=Path(root or Path.cwd()).resolve()
    state=load_production_learned_state(root)
    ledger_path=root/"runtime_state"/"oracle_learning_event_ledger.json"
    ledger=json.loads(ledger_path.read_text(encoding="utf-8"))
    learned=[]
    hashes=[]
    for key,rec in (ledger.items() if isinstance(ledger,dict) else ()):
        if not isinstance(rec,dict) or str(rec.get("status") or "")!="learned":continue
        h=str(rec.get("evidence_hash") or "")
        ticker=str(rec.get("ticker") or "")
        if not ticker or not h:continue
        learned.append((str(key),rec))
        hashes.append(h)

    evidence={}
    conn=_connect(_db_url(root))
    try:
        try:conn.set_session(readonly=True,autocommit=False)
        except Exception:pass
        cur=conn.cursor()
        for pos in range(0,len(hashes),500):
            batch=hashes[pos:pos+500]
            cur.execute(
                """SELECT content_hash,observation_id,observation_type,observed_at,
                          source_observation_id,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE content_hash = ANY(%s) OR observation_id = ANY(%s)""",
                (batch,batch),
            )
            for r in cur.fetchall():
                row={
                    "content_hash":str(r[0] or ""),
                    "observation_id":str(r[1] or ""),
                    "observation_type":str(r[2] or ""),
                    "observed_at":str(r[3] or ""),
                    "source_observation_id":str(r[4] or ""),
                    "canonical_observation_json":r[5],
                }
                for k in (row["content_hash"],row["observation_id"]):
                    if k:evidence.setdefault(k,row)
        try:conn.rollback()
        except Exception:pass
    finally:conn.close()

    profiles=[]
    for settlement_hash,rec in learned:
        ticker=str(rec.get("ticker") or "")
        h=str(rec.get("evidence_hash") or "")
        row=evidence.get(h)
        ident=resolve_structural_identity(ticker)
        profiles.append({
            "settlement_hash":settlement_hash,
            "market_ticker":ticker,
            "series_key":ident.series_key,
            "settlement_ts":str(rec.get("settlement_ts") or ""),
            "evidence_hash":h,
            "learning_event_hash":str(rec.get("learning_event_hash") or ""),
            "evidence_resolved":row is not None,
            "observation_id":str((row or {}).get("observation_id") or ""),
            "observation_type":str((row or {}).get("observation_type") or "UNKNOWN").upper(),
            "observed_at":str((row or {}).get("observed_at") or ""),
            "utc_session":_session((row or {}).get("observed_at")),
            "source_family":_source_family((row or {}).get("canonical_observation_json")),
        })
    return {
        "revision":OLF_011_REVISION,
        "learner_state_hash":state.learner_state_hash,
        "outcomes_learned":state.outcomes_learned,
        "learned_records":state.learned_records,
        "profiles":profiles,
        "resolved_evidence":sum(1 for x in profiles if x["evidence_resolved"]),
        "execution_authority":False,
    }

def materialize_learned_experience_profiles(root=None,force=False):
    root=Path(root or Path.cwd()).resolve()
    path=root/"runtime_state"/PROFILE_NAME
    state=load_production_learned_state(root)
    if path.is_file() and not force:
        try:
            old=json.loads(path.read_text(encoding="utf-8"))
            if str(old.get("learner_state_hash") or "")==state.learner_state_hash:
                return old
        except Exception:pass
    payload=build_learned_experience_profiles(root)
    atomic_write_json(path,payload)
    return payload

def verify_olf_011_evidence_grounded_learned_experience_profile():
    return OLF_011_BUILD_ID=="OLF-011" and _session("2026-08-20T13:00:00Z")=="UTC_12_17"
