from __future__ import annotations
from datetime import datetime,timezone
OIAR_034_BUILD_ID="OIAR-034"
OIAR_034_REVISION="OIAR_034_TEMPORAL_RELEVANCE_V1"
EXECUTION_AUTHORITY=False
TIME_KEYS=("event_start","event_start_at","start_time","close_time","close_at","expiration_time","expected_expiration_time")

def _parse(v):
    if not v:return None
    if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s=str(v).strip().replace("Z","+00:00")
    try:
        x=datetime.fromisoformat(s);return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except ValueError:return None

def temporal_relevance(market,now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
    event=None;source=""
    for key in TIME_KEYS:
        event=_parse(market.get(key))
        if event is not None:source=key;break
    if event is None:return {"label":"UNKNOWN","proven":False,"event_time":None,"source":"NO_SNAPSHOT_EVENT_TIME"}
    local_now=now.astimezone(event.tzinfo);delta=(event-local_now).total_seconds()
    if event.date()==local_now.date():label="TODAY"
    elif 0<delta<=36*3600:label="UPCOMING"
    elif delta<0:label="PAST_OR_STARTED"
    else:label="FUTURE"
    return {"label":label,"proven":True,"event_time":event.isoformat(),"source":source}
