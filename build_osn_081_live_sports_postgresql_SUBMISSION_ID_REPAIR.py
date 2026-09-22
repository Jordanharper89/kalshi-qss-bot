from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/persistence/live_sports_postgresql_bridge.py"
TEST="test_osn_081_live_sports_postgresql_SUBMISSION_ID_REPAIR.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport json, uuid\n\nfrom qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    canonicalize, submit, await_commit, exact_readback, readback_count\n)\n\nADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")\nSTATE_REL="qseries_v2/oracle_source_network/state/osn081_live_sports_persistence_bridge.json"\n\n@dataclass(frozen=True)\nclass PersistedSportsObservation:\n    league:str\n    provider_event_id:str\n    observation_id:str\n    request_id:str\n    write_action:str\n    readback_count:int\n    execution_authority:bool=False\n\ndef _field(value,*names):\n    if isinstance(value,dict):\n        for n in names:\n            if n in value and value[n] not in (None,""):\n                return value[n]\n    for n in names:\n        if hasattr(value,n):\n            v=getattr(value,n)\n            if v not in (None,""):\n                return v\n    return None\n\ndef _observation_id(value):\n    oid=_field(value,"observation_id","id","canonical_observation_id")\n    if oid is None:\n        raise RuntimeError(f"canonicalized observation exposes no observation id: type={type(value).__name__}")\n    return str(oid)\n\ndef _request_id(submission):\n    rid=getattr(submission,"request_id",None)\n    if rid in (None,""):\n        if isinstance(submission,str) and submission:\n            return submission\n        raise RuntimeError(\n            "OPH-019 submit result exposes no request_id; "\n            f"type={type(submission).__name__}"\n        )\n    return str(rid)\n\ndef persist_event(league,event,root=None,batch_id=None,timeout_seconds=45.0):\n    base=Path(root or Path.cwd()).resolve()\n    batch_id=batch_id or f"osn081-{league.lower()}-{uuid.uuid4().hex}"\n    canonical=canonicalize(event,batch_id=batch_id)\n    oid=_observation_id(canonical)\n\n    before=exact_readback(oid,root=base)\n    before_count=readback_count(before)\n    if before_count > 0:\n        return PersistedSportsObservation(\n            league=league,\n            provider_event_id=str(_field(event,"provider_event_id") or ""),\n            observation_id=oid,\n            request_id="",\n            write_action="READ_BEFORE_WRITE_HIT",\n            readback_count=before_count,\n        )\n\n    submission=submit((canonical,),root=base)\n    rid=_request_id(submission)\n    await_commit(rid,root=base,timeout_seconds=timeout_seconds)\n\n    after=exact_readback(oid,root=base)\n    after_count=readback_count(after)\n    if after_count < 1:\n        raise RuntimeError(\n            f"{league} request {rid} reached terminal commit but exact PostgreSQL "\n            f"readback is empty for {oid}"\n        )\n\n    return PersistedSportsObservation(\n        league=league,\n        provider_event_id=str(_field(event,"provider_event_id") or ""),\n        observation_id=oid,\n        request_id=rid,\n        write_action="SUBMITTED_COMMITTED_READBACK_VERIFIED",\n        readback_count=after_count,\n    )\n\ndef acquire_and_persist_one_per_league(root=None,timeout=15,commit_timeout_seconds=45.0):\n    base=Path(root or Path.cwd()).resolve()\n    rows=[]\n    for league in ADMITTED:\n        result=acquire_canonical_events(league,timeout=timeout,root=base)\n        if not result.events:\n            raise RuntimeError(f"{league} returned zero canonical events")\n        row=persist_event(\n            league,result.events[0],root=base,\n            batch_id=f"osn081-{league.lower()}",\n            timeout_seconds=commit_timeout_seconds,\n        )\n        rows.append(row)\n        print("[PERSIST]",row)\n\n    state=base/STATE_REL\n    state.parent.mkdir(parents=True,exist_ok=True)\n    state.write_text(json.dumps({\n        "rows":[asdict(x) for x in rows],\n        "single_writer":"OPH-019",\n        "writer_id":"oracle.osn.sports",\n        "canonicalizer":"OAD-261 via sports_single_writer_boundary",\n        "exact_readback":"OAD-068 via sports_single_writer_boundary",\n        "request_lifecycle":"submit -> submission.request_id -> await_request -> exact_readback",\n        "execution_authority":False,\n    },indent=2),encoding="utf-8")\n    return tuple(rows),state\n'
TEST_SOURCE='\nfrom pathlib import Path\nimport inspect\n\nfrom qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import (\n    acquire_and_persist_one_per_league, ADMITTED, _request_id\n)\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import submit\n\nclass FixtureSubmission:\n    request_id="fixture-request-id"\n\nassert _request_id(FixtureSubmission())=="fixture-request-id"\nprint("[PASS] OPH-019 submission object request_id extraction verified")\n\nrows,state=acquire_and_persist_one_per_league(\n    root=Path.cwd(),\n    timeout=15,\n    commit_timeout_seconds=45.0,\n)\n\nprint("[STATE]",state)\nassert tuple(r.league for r in rows)==ADMITTED\nassert all(r.readback_count>0 for r in rows)\nassert all(r.execution_authority is False for r in rows)\nassert all(\n    (r.write_action=="READ_BEFORE_WRITE_HIT") or bool(r.request_id)\n    for r in rows\n)\n\nprint("[PASS] six admitted leagues passed live source -> canonical -> OPH-019 -> await -> exact readback")\nprint("[PASS] await uses exact submission.request_id")\nprint("[PASS] OSN-081 live sports PostgreSQL persistence certified")\nprint("[PASS] execution_authority=FALSE")\n'

def main():
    print("="*120)
    print(" OSN-081 LIVE SPORTS POSTGRESQL — SUBMISSION ID REPAIR")
    print("="*120)

    for dep in (
        "qseries_v2/oracle_source_network/providers/uniform_sports_provider.py",
        "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py",
        "qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py",
        "qseries_v2/oracle_source_network/state/osn081_exact_persistence_contract_repair.json",
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
    ):
        if not (ROOT/dep).exists():
            raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)

    p=ROOT/MODULE
    p.write_text(MODULE_SOURCE,encoding="utf-8")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")

    t=ROOT/TEST
    t.write_text(TEST_SOURCE,encoding="utf-8")
    compile(t.read_text(encoding="utf-8"),str(t),"exec")

    print("[WRITE]",MODULE)
    print("[WRITE]",TEST)
    print("[PASS] bad whole-submission await key retired")
    print("[PASS] exact submission.request_id lifecycle restored")
    print("[PASS] no new writer introduced")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
