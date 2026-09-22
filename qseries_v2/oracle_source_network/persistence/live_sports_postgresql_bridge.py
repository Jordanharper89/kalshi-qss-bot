
from dataclasses import dataclass, asdict
from pathlib import Path
import json, uuid

from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (
    canonicalize, submit, await_commit, exact_readback, readback_count
)

ADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")
STATE_REL="qseries_v2/oracle_source_network/state/osn081_live_sports_persistence_bridge.json"

@dataclass(frozen=True)
class PersistedSportsObservation:
    league:str
    provider_event_id:str
    observation_id:str
    request_id:str
    write_action:str
    readback_count:int
    execution_authority:bool=False

def _field(value,*names):
    if isinstance(value,dict):
        for n in names:
            if n in value and value[n] not in (None,""):
                return value[n]
    for n in names:
        if hasattr(value,n):
            v=getattr(value,n)
            if v not in (None,""):
                return v
    return None

def _observation_id(value):
    oid=_field(value,"observation_id","id","canonical_observation_id")
    if oid is None:
        raise RuntimeError(f"canonicalized observation exposes no observation id: type={type(value).__name__}")
    return str(oid)

def _request_id(submission):
    rid=getattr(submission,"request_id",None)
    if rid in (None,""):
        if isinstance(submission,str) and submission:
            return submission
        raise RuntimeError(
            "OPH-019 submit result exposes no request_id; "
            f"type={type(submission).__name__}"
        )
    return str(rid)

def persist_event(league,event,root=None,batch_id=None,timeout_seconds=45.0):
    base=Path(root or Path.cwd()).resolve()
    batch_id=batch_id or f"osn081-{league.lower()}-{uuid.uuid4().hex}"
    canonical=canonicalize(event,batch_id=batch_id)
    oid=_observation_id(canonical)

    before=exact_readback(oid,root=base)
    before_count=readback_count(before)
    if before_count > 0:
        return PersistedSportsObservation(
            league=league,
            provider_event_id=str(_field(event,"provider_event_id") or ""),
            observation_id=oid,
            request_id="",
            write_action="READ_BEFORE_WRITE_HIT",
            readback_count=before_count,
        )

    submission=submit((canonical,),root=base)
    rid=_request_id(submission)
    await_commit(rid,root=base,timeout_seconds=timeout_seconds)

    after=exact_readback(oid,root=base)
    after_count=readback_count(after)
    if after_count < 1:
        raise RuntimeError(
            f"{league} request {rid} reached terminal commit but exact PostgreSQL "
            f"readback is empty for {oid}"
        )

    return PersistedSportsObservation(
        league=league,
        provider_event_id=str(_field(event,"provider_event_id") or ""),
        observation_id=oid,
        request_id=rid,
        write_action="SUBMITTED_COMMITTED_READBACK_VERIFIED",
        readback_count=after_count,
    )

def acquire_and_persist_one_per_league(root=None,timeout=15,commit_timeout_seconds=45.0):
    base=Path(root or Path.cwd()).resolve()
    rows=[]
    for league in ADMITTED:
        result=acquire_canonical_events(league,timeout=timeout,root=base)
        if not result.events:
            raise RuntimeError(f"{league} returned zero canonical events")
        row=persist_event(
            league,result.events[0],root=base,
            batch_id=f"osn081-{league.lower()}",
            timeout_seconds=commit_timeout_seconds,
        )
        rows.append(row)
        print("[PERSIST]",row)

    state=base/STATE_REL
    state.parent.mkdir(parents=True,exist_ok=True)
    state.write_text(json.dumps({
        "rows":[asdict(x) for x in rows],
        "single_writer":"OPH-019",
        "writer_id":"oracle.osn.sports",
        "canonicalizer":"OAD-261 via sports_single_writer_boundary",
        "exact_readback":"OAD-068 via sports_single_writer_boundary",
        "request_lifecycle":"submit -> submission.request_id -> await_request -> exact_readback",
        "execution_authority":False,
    },indent=2),encoding="utf-8")
    return tuple(rows),state
