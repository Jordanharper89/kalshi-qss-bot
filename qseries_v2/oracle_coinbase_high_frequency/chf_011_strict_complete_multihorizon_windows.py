import json
from datetime import datetime,timezone,timedelta
from pathlib import Path

REVISION="CHF-011-RECENT-COMPLETE-ANCHOR-REPAIR"
WINDOWS=(5,15,30,60)
PRODUCTS=("BTC-USD","ETH-USD","SOL-USD")
BOUNDARY_STALENESS_S=5.0
RECENT_ANCHOR_SEARCH_S=10.0

def _dt(v):
    if isinstance(v,(int,float)):
        return datetime.fromtimestamp(float(v),tz=timezone.utc)
    s=str(v or "").strip()
    if not s: raise ValueError("timestamp missing")
    if s.endswith("Z"): s=s[:-1]+"+00:00"
    x=datetime.fromisoformat(s)
    if x.tzinfo is None: x=x.replace(tzinfo=timezone.utc)
    return x.astimezone(timezone.utc)

def _event_time(row):
    for k in ("observed_at","event_time","timestamp","time","received_at"):
        if row.get(k) is not None:
            try:return _dt(row[k])
            except Exception:pass
    payload=row.get("payload")
    if isinstance(payload,dict):
        for k in ("observed_at","event_time","timestamp","time"):
            if payload.get(k) is not None:
                try:return _dt(payload[k])
                except Exception:pass
    raise ValueError("no usable canonical event timestamp")

def _product(row):
    for k in ("product_id","product","symbol"):
        if row.get(k): return str(row[k])
    payload=row.get("payload")
    if isinstance(payload,dict):
        for k in ("product_id","product","symbol"):
            if payload.get(k): return str(payload[k])
    return ""

def _best_complete_window(pe,seconds):
    newest=pe[-1][1]
    floor=newest-timedelta(seconds=RECENT_ANCHOR_SEARCH_S)
    for anchor_i in range(len(pe)-1,-1,-1):
        anchor=pe[anchor_i][1]
        if anchor<floor: break
        cutoff=anchor-timedelta(seconds=seconds)
        prior=None
        for i in range(anchor_i,-1,-1):
            if pe[i][1]<=cutoff:
                prior=pe[i]
                break
        if prior is None: continue
        boundary_age=(cutoff-prior[1]).total_seconds()
        if boundary_age>BOUNDARY_STALENESS_S: continue
        body=[x for x in pe if cutoff<x[1]<=anchor]
        w=[prior]+body
        if len(w)<2: continue
        gaps=[(w[i][1]-w[i-1][1]).total_seconds() for i in range(1,len(w))]
        return anchor,cutoff,w,boundary_age,max(gaps) if gaps else 0.0
    return None

def materialize_strict(root:Path):
    root=Path(root)
    d=root/"runtime"/"coinbase_hf"
    src=d/"canonical_events.jsonl"
    out=d/"strict_condition_windows.jsonl"
    if not src.exists(): raise RuntimeError("canonical event journal missing")
    events=[]
    for line in src.read_text(encoding="utf-8").splitlines():
        try:r=json.loads(line)
        except Exception:continue
        p=_product(r)
        if p not in PRODUCTS: continue
        try:t=_event_time(r)
        except Exception:continue
        events.append((p,t,r))
    rows=[]
    for product in PRODUCTS:
        pe=sorted((x for x in events if x[0]==product),key=lambda x:x[1])
        if not pe: continue
        for seconds in WINDOWS:
            hit=_best_complete_window(pe,seconds)
            if hit is None: continue
            anchor,cutoff,w,boundary_age,max_gap=hit
            rows.append({
                "schema_version":"CHF-011-REPAIR",
                "product_id":product,
                "window_seconds":seconds,
                "window_start":cutoff.isoformat(),
                "window_end":anchor.isoformat(),
                "coverage_span_seconds":seconds,
                "boundary_observation_age_seconds":boundary_age,
                "event_count":len(w),
                "max_event_gap_seconds":max_gap,
                "full_horizon_complete":True,
                "no_future_leakage":all(x[1]<=anchor for x in w),
                "upstream_source_class":"RAW_EXTERNAL",
                "source_class":"ORACLE_DERIVED",
                "probability_enabled":False,
                "direction_enabled":False,
                "publication_allowed":False,
                "execution_authority":False,
            })
    out.write_text("".join(json.dumps(r,separators=(",",":"))+"\n" for r in rows),encoding="utf-8")
    return rows,out
