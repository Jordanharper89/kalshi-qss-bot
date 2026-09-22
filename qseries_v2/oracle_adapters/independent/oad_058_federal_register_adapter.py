from __future__ import annotations
import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from .oad_056_independent_source_provenance import build_independent_observation
OAD_058_BUILD_ID="OAD-058"; OAD_058_REVISION="OAD_058_FEDERAL_REGISTER_ADAPTER_V1"
READ_ONLY=True; EXECUTION_AUTHORITY=False
BASE="https://www.federalregister.gov/api/v1/documents.json"
def acquire_federal_register_documents(limit=20, timeout=20):
    url=BASE+"?"+urllib.parse.urlencode({"per_page":max(1,min(int(limit),100)),"order":"newest"})
    req=urllib.request.Request(url,headers={"User-Agent":"QSeries-Oracle/1.0 read-only"})
    with urllib.request.urlopen(req,timeout=timeout) as r: data=json.load(r)
    rows=[]
    for d in data.get("results",[])[:limit]:
        rows.append(build_independent_observation(source_id="federalregister.gov",source_class="authoritative_real_world",
            observation_type="federal_register_document",subject=d.get("title") or "Federal Register document",
            observed_at=(d.get("publication_date") or datetime.now(timezone.utc).date().isoformat())+"T00:00:00Z",
            source_url=d.get("html_url") or d.get("pdf_url") or BASE,payload={"document_number":d.get("document_number"),
            "type":d.get("type"),"agencies":[a.get("name") for a in d.get("agencies",[]) if isinstance(a,dict)],
            "abstract":d.get("abstract")}))
    return tuple(rows)
def verify_oad_058_federal_register_adapter():
    rows=acquire_federal_register_documents(limit=3)
    return len(rows)>0 and all(x.source_id=="federalregister.gov" and not x.execution_authority for x in rows)
