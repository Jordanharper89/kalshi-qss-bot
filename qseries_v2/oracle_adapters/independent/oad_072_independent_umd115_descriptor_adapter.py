from __future__ import annotations
import json
from collections.abc import Mapping
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import (
    UMD_115_REVISION,
    ObservationDescriptor,
    OBSERVATION_FIELDS,
)
from qseries_v2.oracle_adapters.independent.oad_071_semantic_noise_rejection import (
    semantic_tokens,
    strong_phrases,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _thaw(value):
    if isinstance(value, Mapping):
        return {str(k):_thaw(v) for k,v in value.items()}
    if isinstance(value, tuple):
        # Frozen canonical mappings are represented as tuple-of-pairs.
        if all(isinstance(x,tuple) and len(x)==2 for x in value):
            try:
                return {str(k):_thaw(v) for k,v in value}
            except Exception:
                pass
        return tuple(_thaw(x) for x in value)
    if isinstance(value,list):
        return [_thaw(x) for x in value]
    return value

def _payload(obs):
    p=_thaw(getattr(obs,"payload",{}))
    return p if isinstance(p,dict) else {}

def _payload_text(obs):
    p=_payload(obs)
    source=_thaw(p.get("source_payload",{}))
    try:
        body=json.dumps(source,sort_keys=True,default=str)
    except Exception:
        body=str(source)
    return " ".join((str(p.get("subject","")),body))

def _facts_for(obs):
    p=_payload(obs)
    text=_payload_text(obs)
    phrases=strong_phrases(text)
    facts=set()
    source_id=str(getattr(obs,"source_id","") or p.get("source_id","")).lower()

    if "weather.gov" in source_id:
        for x in phrases:
            if any(k in x for k in (
                "warning","watch","storm","hurricane","tornado","flood",
                "snow","wind","heat","freeze","fire","thunderstorm"
            )):
                facts.add(("external_state",x))

    if "usgs.gov" in source_id:
        for x in phrases:
            if "earthquake" in x or "quake" in x:
                facts.add(("event",x))

    if "federalregister.gov" in source_id:
        for x in phrases:
            if any(k in x for k in (
                "rule","order","notice","regulation","tariff","sanction",
                "waiver","approval","prohibition"
            )):
                facts.add(("event",x))

    for x in phrases:
        if any(k in x for k in (
            "texas","california","florida","new-york","washington",
            "alaska","hawaii","gulf","atlantic","pacific"
        )):
            facts.add(("geography",x))

    return tuple(sorted(
        (kind,key)
        for kind,key in facts
        if kind in OBSERVATION_FIELDS and key and key!="new"
    ))

def descriptor_from_canonical(obs):
    oid=str(obs.observation_id)
    facts=_facts_for(obs)
    lineage=ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-115",
        revision=UMD_115_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=("oad://072/"+oid,),
        created_at=datetime.now(timezone.utc),
    )
    return ObservationDescriptor(oid,facts,lineage)

def descriptors_from_canonical(observations):
    return tuple(descriptor_from_canonical(x) for x in observations)

def verify_oad_072_immutable_payload_support():
    class X:
        observation_id="x"
        source_id="source.independent.weather.gov"
        payload=(("subject","Tornado Warning for Texas"),("source_payload",(("headline","Tornado Warning"),)))
    d=descriptor_from_canonical(X())
    return isinstance(d.facts,tuple)
