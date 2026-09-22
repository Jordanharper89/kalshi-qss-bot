from __future__ import annotations
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from .oad_137_authoritative_public_health_source_foundation import build_public_health_observation,utcnow_iso,validate_public_health_observation

PROVIDER="tools.cdc.gov"
BASE="https://tools.cdc.gov/api/v2/resources/media"
DEFAULT_QUERIES=("influenza","respiratory virus","public health emergency")

def _search(query,timeout_seconds,max_results=5):
    url=BASE+"?"+urlencode({"q":query,"max":max_results,"sort":"-dateModified"})
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    return tuple(data.get("results") or ()),url

def acquire_cdc_public_health_observations(timeout_seconds=20.0,queries=DEFAULT_QUERIES):
    out=[]
    seen=set()
    for query in tuple(queries):
        rows,url=_search(query,timeout_seconds)
        for row in rows:
            rid=str(row.get("id",""))
            if not rid or rid in seen: continue
            seen.add(rid)
            name=str(row.get("name") or row.get("title") or row.get("description") or "CDC public-health publication")
            payload={
                "id":rid,
                "name":row.get("name"),
                "description":row.get("description"),
                "sourceUrl":row.get("sourceUrl"),
                "datePublished":row.get("datePublished"),
                "dateModified":row.get("dateModified"),
                "query":query,
            }
            o=build_public_health_observation(
                source_id=f"cdc:media:{rid}",provider=PROVIDER,health_family="public_health",
                observation_type="official_health_publication",subject=name,
                observed_at=utcnow_iso(),source_url=url,payload=payload)
            if not validate_public_health_observation(o): raise RuntimeError("CDC provenance validation failed")
            out.append(o)
    return tuple(out)
