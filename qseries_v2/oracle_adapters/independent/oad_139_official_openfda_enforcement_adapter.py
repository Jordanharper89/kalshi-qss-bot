from __future__ import annotations
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from .oad_137_authoritative_public_health_source_foundation import build_public_health_observation,utcnow_iso,validate_public_health_observation

PROVIDER="api.fda.gov"
BASES=(
    ("drug","https://api.fda.gov/drug/enforcement.json"),
    ("device","https://api.fda.gov/device/enforcement.json"),
    ("food","https://api.fda.gov/food/enforcement.json"),
)

def _latest(kind,url,timeout_seconds,limit=5):
    q=url+"?"+urlencode({"sort":"report_date:desc","limit":limit})
    req=Request(q,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    return tuple(data.get("results") or ()),q

def acquire_openfda_enforcement_observations(timeout_seconds=20.0,limit_per_family=5):
    out=[]
    for kind,url in BASES:
        rows,q=_latest(kind,url,timeout_seconds,limit_per_family)
        for row in rows:
            recall=str(row.get("recall_number") or row.get("event_id") or "")
            report_date=str(row.get("report_date") or "")
            if not recall: continue
            subject=str(row.get("product_description") or row.get("reason_for_recall") or f"FDA {kind} enforcement report")
            payload={
                "kind":kind,
                "recall_number":recall,
                "report_date":report_date,
                "classification":row.get("classification"),
                "status":row.get("status"),
                "recalling_firm":row.get("recalling_firm"),
                "reason_for_recall":row.get("reason_for_recall"),
                "product_description":row.get("product_description"),
                "distribution_pattern":row.get("distribution_pattern"),
            }
            o=build_public_health_observation(
                source_id=f"fda:{kind}:enforcement:{recall}:{report_date}",
                provider=PROVIDER,health_family="regulatory_health",
                observation_type="official_fda_enforcement_report",subject=subject,
                observed_at=utcnow_iso(),source_url=q,payload=payload)
            if not validate_public_health_observation(o): raise RuntimeError("FDA provenance validation failed")
            out.append(o)
    return tuple(out)
