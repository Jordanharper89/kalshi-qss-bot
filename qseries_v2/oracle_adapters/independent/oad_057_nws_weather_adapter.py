from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone
from .oad_056_independent_source_provenance import build_independent_observation

OAD_057_BUILD_ID="OAD-057"
OAD_057_REVISION="OAD_057_NWS_AUTHORITATIVE_WEATHER_ADAPTER_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False
ENDPOINT="https://api.weather.gov/alerts/active"

def acquire_nws_active_alerts(limit=25, timeout=20):
    limit=max(1,min(int(limit),100))
    req=urllib.request.Request(
        ENDPOINT,
        headers={
            "User-Agent":"QSeries-Oracle/1.0 (read-only research)",
            "Accept":"application/geo+json",
        },
    )
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=json.load(r)
    rows=[]
    for f in data.get("features",[])[:limit]:
        p=f.get("properties") or {}
        subject=p.get("headline") or p.get("event") or "NWS active alert"
        rows.append(build_independent_observation(
            source_id="weather.gov",
            source_class="authoritative_real_world",
            observation_type="weather_alert",
            subject=subject,
            observed_at=p.get("sent") or datetime.now(timezone.utc).isoformat(),
            source_url=p.get("@id") or f.get("id") or ENDPOINT,
            payload={
                "event":p.get("event"),
                "areaDesc":p.get("areaDesc"),
                "severity":p.get("severity"),
                "certainty":p.get("certainty"),
                "urgency":p.get("urgency"),
                "effective":p.get("effective"),
                "expires":p.get("expires"),
            },
        ))
    return tuple(rows)

def verify_oad_057_nws_authoritative_weather_adapter():
    rows=acquire_nws_active_alerts(limit=5)
    return isinstance(rows,tuple) and all(
        x.source_id=="weather.gov" and not x.execution_authority for x in rows
    )
