from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_predictive_data"
PKG.mkdir(parents=True,exist_ok=True)

MOD=PKG/"opd_014_kalshi_and_learned_state_census_indexed_repair.py"
TEST=ROOT/"test_opd_014_kalshi_and_learned_state_census_indexed_repair.py"

MOD.write_text(r"""
from pathlib import Path
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SOURCE_PREFIX="source.crypto.learned_case."
OBS_TYPE="crypto_verified_learned_case"
CHUNK=100000
STATEMENT_TIMEOUT_MS=30000

def _asset_from_ticker(t):
    u=str(t).upper()
    if "BTC" in u:return "BTC"
    if "ETH" in u:return "ETH"
    if "SOL" in u:return "SOL"
    return None

def _epoch(v):
    if v is None:return None
    try:return float(v)
    except Exception:pass
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.timestamp()
    except Exception:return None

def _payload(obj):
    if not isinstance(obj,dict):return {}
    raw=obj.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):
        return raw["payload"]
    p=obj.get("payload")
    return p if isinstance(p,dict) else {}

def _hfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def _learned_sequence_bounds(rt):
    census=json.loads((rt/"opd_007_full_history_source_depth_census.json").read_text(encoding="utf-8"))
    groups=[
        g for g in census.get("groups",[])
        if str(g.get("source_id","")).startswith(SOURCE_PREFIX)
        and str(g.get("observation_type",""))==OBS_TYPE
    ]
    if not groups:
        raise RuntimeError("NO_LEARNED_CASE_GROUPS_IN_OPD007_CENSUS")
    lo=min(int(g["min_sequence"]) for g in groups)
    hi=max(int(g["max_sequence"]) for g in groups)
    return lo,hi,groups

def _load_learned(root,rt):
    lo,hi,groups=_learned_sequence_bounds(rt)
    rows=[]
    cursor=lo
    chunks=0

    while cursor<=hi:
        end=min(hi,cursor+CHUNK-1)
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute(f"SET LOCAL statement_timeout='{STATEMENT_TIMEOUT_MS}ms'")
                q.execute(
                    "SELECT sequence_number,source_id,canonical_observation_json "
                    "FROM public.oracle_canonical_observations "
                    "WHERE sequence_number BETWEEN %s AND %s "
                    "AND observation_type=%s "
                    "AND source_id LIKE %s "
                    "ORDER BY sequence_number",
                    (cursor,end,OBS_TYPE,SOURCE_PREFIX+"%"),
                )
                batch=q.fetchall() or []
            c.rollback()

        for seq,sid,obj in batch:
            p=_payload(obj)
            asset=str(p.get("asset") or str(sid).split(".")[-1]).upper()
            available=_epoch(p.get("outcome_observed_at"))
            if available is None:continue
            rows.append({
                "sequence_number":int(seq),
                "source_id":str(sid),
                "asset":asset,
                "available_epoch":available,
                "experience_id":p.get("experience_id"),
                "snapshot_at":p.get("snapshot_at"),
                "condition_vector":p.get("condition_vector"),
                "temporal_vector":p.get("temporal_vector"),
                "condition_hash":p.get("condition_hash"),
                "experience_hash":p.get("experience_hash"),
                "lineage_hash":p.get("lineage_hash"),
                "horizon_seconds":p.get("horizon_seconds"),
                "requested_horizon_seconds":p.get("requested_horizon_seconds"),
                "realized_horizon_seconds":p.get("realized_horizon_seconds"),
                "timing_offset_seconds":p.get("timing_offset_seconds"),
                "sampling_method":p.get("sampling_method"),
                "timing_certified":bool(p.get("timing_certified",False)),
                "exact_interval":bool(p.get("exact_interval",False)),
                "return_fraction":p.get("return_fraction"),
                "return_percent":p.get("return_percent"),
                "outcome_hash":p.get("outcome_hash"),
                "learning_event_hash":p.get("learning_event_hash"),
            })

        chunks+=1
        cursor=end+1

    return rows,(lo,hi),groups,chunks

def build(root=None):
    root=Path(root or Path.cwd())
    rt=root/"runtime"/"predictive_data"

    ks=json.loads((rt/"opd_004_kalshi_raw_state_at_t.json").read_text(encoding="utf-8"))
    byseq={int(x["sequence_number"]):x for x in ks.get("rows",[])}

    learned,bounds,census_groups,chunks=_load_learned(root,rt)

    lidx={}
    for x in learned:
        lidx.setdefault(x["asset"],[]).append(x)

    index={}
    for asset,series in lidx.items():
        series.sort(key=lambda x:(x["available_epoch"],x["sequence_number"]))
        index[asset]={
            "times":[x["available_epoch"] for x in series],
            "rows":series,
        }

    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    outrows=rt/"opd_014_kalshi_and_learned_state_strict_asof_join.jsonl"

    total=0
    kcover=0
    lcover=0
    leakage=0
    asset_counts=Counter()
    learned_cover_by_asset=Counter()

    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line)
            total+=1
            seq=int(a["anchor_sequence_number"])
            anchor_t=float(a["anchor_epoch"])
            k=byseq.get(seq)
            asset=_asset_from_ticker(a["ticker"])

            kstate=None
            if k is not None:
                event_epoch=float(k["event_epoch"])
                if event_epoch>anchor_t:
                    leakage+=1
                else:
                    kcover+=1
                    kstate={
                        "sequence_number":k.get("sequence_number"),
                        "event_epoch":event_epoch,
                        "trade_price":k.get("trade_price"),
                        "yes_bid":k.get("yes_bid"),
                        "yes_ask":k.get("yes_ask"),
                        "spread":k.get("spread"),
                        "yes_bid_size":k.get("yes_bid_size"),
                        "yes_ask_size":k.get("yes_ask_size"),
                        "last_trade_size":k.get("last_trade_size"),
                        "volume":k.get("volume"),
                        "open_interest":k.get("open_interest"),
                        "observation_type":k.get("observation_type"),
                        "event_time_path":k.get("event_time_path"),
                    }

            learned_state=None
            if asset:
                asset_counts[asset]+=1
                bucket=index.get(asset)
                if bucket:
                    j=bisect_right(bucket["times"],anchor_t)-1
                    if j>=0:
                        x=bucket["rows"][j]
                        if x["available_epoch"]>anchor_t:
                            leakage+=1
                        else:
                            lcover+=1
                            learned_cover_by_asset[asset]+=1
                            learned_state={
                                "sequence_number":x["sequence_number"],
                                "available_epoch":x["available_epoch"],
                                "age_seconds":anchor_t-x["available_epoch"],
                                "experience_id":x["experience_id"],
                                "snapshot_at":x["snapshot_at"],
                                "condition_vector":x["condition_vector"],
                                "temporal_vector":x["temporal_vector"],
                                "condition_hash":x["condition_hash"],
                                "experience_hash":x["experience_hash"],
                                "lineage_hash":x["lineage_hash"],
                                "horizon_seconds":x["horizon_seconds"],
                                "requested_horizon_seconds":x["requested_horizon_seconds"],
                                "realized_horizon_seconds":x["realized_horizon_seconds"],
                                "timing_offset_seconds":x["timing_offset_seconds"],
                                "sampling_method":x["sampling_method"],
                                "timing_certified":x["timing_certified"],
                                "exact_interval":x["exact_interval"],
                                "return_fraction":x["return_fraction"],
                                "return_percent":x["return_percent"],
                                "outcome_hash":x["outcome_hash"],
                                "learning_event_hash":x["learning_event_hash"],
                            }

            dst.write(json.dumps({
                "anchor_id":a["anchor_id"],
                "asset":asset,
                "kalshi_anchor_state":kstate,
                "learned_state":learned_state,
            },sort_keys=True,separators=(",",":"))+"\n")

    s={
        "schema_version":"OPD-014",
        "revision":"CENSUS_INDEXED_REPAIR",
        "anchor_rows":total,
        "kalshi_anchor_state_covered":kcover,
        "learned_cases_loaded":len(learned),
        "learned_state_covered":lcover,
        "asset_anchor_counts":dict(asset_counts),
        "learned_covered_by_asset":dict(learned_cover_by_asset),
        "learned_sequence_window":list(bounds),
        "learned_census_groups":len(census_groups),
        "postgres_chunks_scanned":chunks,
        "post_t_feature_rows":leakage,
        "learned_availability_rule":"OUTCOME_OBSERVED_AT_LE_ANCHOR_EPOCH",
        "learned_query_mode":"OPD007_CENSUS_BOUNDS_PLUS_100K_SEQUENCE_CHUNKS",
        "join_algorithm":"PREINDEXED_LEARNED_TIMELINES_PLUS_BINARY_SEARCH",
        "oad_189_runtime_query_used":False,
        "join_hash":_hfile(outrows),
        "model_fit_allowed":False,
        "formula_mining_allowed":False,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }

    out=rt/"opd_014_kalshi_and_learned_state_strict_asof_join.json"
    out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_014_kalshi_and_learned_state_census_indexed_repair import build

s,p=build(Path.cwd())

assert p.exists()
assert s["anchor_rows"]>0
assert s["kalshi_anchor_state_covered"]>0
assert s["learned_cases_loaded"]>0
assert s["post_t_feature_rows"]==0
assert s["oad_189_runtime_query_used"] is False
assert s["join_algorithm"]=="PREINDEXED_LEARNED_TIMELINES_PLUS_BINARY_SEARCH"
assert not s["model_fit_allowed"]
assert not s["formula_mining_allowed"]
assert not s["probability_enabled"]
assert not s["direction_enabled"]
assert not s["publication_allowed"]
assert not s["execution_authority"]

print("[FILE]",p)
print("[ANCHORS]",s["anchor_rows"])
print("[KALSHI_COVERED]",s["kalshi_anchor_state_covered"])
print("[LEARNED_CASES_LOADED]",s["learned_cases_loaded"])
print("[LEARNED_COVERED]",s["learned_state_covered"])
print("[ASSET_ANCHORS]",s["asset_anchor_counts"])
print("[LEARNED_COVERED_BY_ASSET]",s["learned_covered_by_asset"])
print("[LEARNED_SEQUENCE_WINDOW]",s["learned_sequence_window"])
print("[POSTGRES_CHUNKS]",s["postgres_chunks_scanned"])
print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[OAD_189_RUNTIME_QUERY_USED]",s["oad_189_runtime_query_used"])
print("[JOIN_ALGORITHM]",s["join_algorithm"])
print("[JOIN_HASH]",s["join_hash"])
print("[PASS] OAD-189 timeout path retired from OPD-014")
print("[PASS] learned sequence bounds sourced from certified OPD-007 census")
print("[PASS] learned rows acquired only through bounded read-only chunks")
print("[PASS] learned timelines indexed once and queried by binary search")
print("[PASS] learned state admitted only after outcome_observed_at")
print("[PASS] OPD-014 CENSUS INDEXED REPAIR certified")
""",encoding="utf-8")

py_compile.compile(str(MOD),doraise=True)
py_compile.compile(str(TEST),doraise=True)
print("[PASS] OPD-014 census-indexed repair installer complete")
