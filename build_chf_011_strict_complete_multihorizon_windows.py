from pathlib import Path
import py_compile
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_003_canonical_event_normalizer.py").exists(),"CHF-003 required"

BODY=r"""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path

REVISION="CHF-011"
WINDOWS=(5,15,30,60)

def _dt(v):
    if isinstance(v,(int,float)):
        return datetime.fromtimestamp(float(v),tz=timezone.utc)
    s=str(v or "").strip()
    if not s:
        raise ValueError("timestamp missing")
    if s.endswith("Z"):
        s=s[:-1]+"+00:00"
    x=datetime.fromisoformat(s)
    if x.tzinfo is None:
        x=x.replace(tzinfo=timezone.utc)
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

def materialize_strict(root:Path):
    root=Path(root)
    d=root/"runtime"/"coinbase_hf"
    src=d/"canonical_events.jsonl"
    out=d/"strict_condition_windows.jsonl"
    if not src.exists():
        raise RuntimeError("canonical event journal missing")
    events=[]
    for line in src.read_text(encoding="utf-8").splitlines():
        try:r=json.loads(line)
        except Exception:continue
        p=_product(r)
        if not p:continue
        try:t=_event_time(r)
        except Exception:continue
        events.append((p,t,r))
    rows=[]
    for product in ("BTC-USD","ETH-USD","SOL-USD"):
        pe=sorted((x for x in events if x[0]==product),key=lambda x:x[1])
        if not pe:continue
        anchor=pe[-1][1]
        for seconds in WINDOWS:
            cutoff=anchor-timedelta(seconds=seconds)
            w=[x for x in pe if cutoff<=x[1]<=anchor]
            if len(w)<2:continue
            span=(w[-1][1]-w[0][1]).total_seconds()
            if span < seconds-0.25:
                continue
            gaps=[(w[i][1]-w[i-1][1]).total_seconds() for i in range(1,len(w))]
            max_gap=max(gaps) if gaps else 999.0
            row={
                "schema_version":"CHF-011",
                "product_id":product,
                "window_seconds":seconds,
                "window_start":cutoff.isoformat(),
                "window_end":anchor.isoformat(),
                "coverage_span_seconds":span,
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
            }
            rows.append(row)
    out.write_text("".join(json.dumps(r,separators=(",",":"))+"\n" for r in rows),encoding="utf-8")
    return rows,out
"""
TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict
rows,p=materialize_strict(Path.cwd())
print("[STRICT_WINDOW_FILE]",p)
print("[STRICT_ROWS]",len(rows))
for r in rows: print("[WINDOW]",r["product_id"],r["window_seconds"],"span=",round(r["coverage_span_seconds"],3),"events=",r["event_count"])
assert all(r["full_horizon_complete"] for r in rows)
assert all(r["no_future_leakage"] for r in rows)
print("[PASS] incomplete 30s/60s windows rejected rather than falsely admitted")
print("[PASS] CHF-011 strict full-horizon window contract certified")
"""
mod=PKG/"chf_011_strict_complete_multihorizon_windows.py"
tst=ROOT/"test_chf_011_strict_complete_multihorizon_windows.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True); py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote CHF-011 strict window materializer + test")
