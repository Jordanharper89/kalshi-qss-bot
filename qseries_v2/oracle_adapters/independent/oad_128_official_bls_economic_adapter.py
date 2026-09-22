from __future__ import annotations
import json
from urllib.request import Request,urlopen
from .oad_127_authoritative_economic_source_foundation import build_economic_observation,utcnow_iso,validate_economic_observation

PROVIDER="api.bls.gov"
BASE="https://api.bls.gov/publicAPI/v2/timeseries/data"
SERIES=(
    ("CUUR0000SA0","inflation","Consumer Price Index for All Urban Consumers"),
    ("LNS14000000","labor","Civilian Unemployment Rate"),
    ("CES0000000001","labor","Total Nonfarm Payroll Employment"),
)

def _latest(series_id,timeout_seconds):
    url=f"{BASE}/{series_id}?latest=true"
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    if data.get("status")!="REQUEST_SUCCEEDED": raise RuntimeError("BLS request failed")
    rows=((data.get("Results") or {}).get("series") or [])
    if not rows or not rows[0].get("data"): return None,url
    return rows[0]["data"][0],url

def acquire_bls_latest_economic_observations(timeout_seconds=20):
    out=[]
    for series_id,family,label in SERIES:
        row,url=_latest(series_id,timeout_seconds)
        if row is None: continue
        period=str(row.get("period",""))
        year=str(row.get("year",""))
        value=str(row.get("value",""))
        payload={"series_id":series_id,"label":label,"year":year,"period":period,"period_name":row.get("periodName"),"value":value,"footnotes":row.get("footnotes") or []}
        o=build_economic_observation(
            source_id=f"bls:{series_id}:{year}:{period}",provider=PROVIDER,economic_family=family,
            observation_type="official_economic_release",subject=f"{label}: {value}",
            observed_at=utcnow_iso(),source_url=url,payload=payload)
        if not validate_economic_observation(o): raise RuntimeError("BLS provenance validation failed")
        out.append(o)
    return tuple(out)
