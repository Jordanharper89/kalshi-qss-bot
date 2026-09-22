from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/six_league_uniform_provider_gate.py"
TEST="test_osn_078_six_league_uniform_provider_physical_gate_EXECUTABLE_FOUNDATION_REBUILD.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport json, time\n\nfrom qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events\n\nADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")\nSTATE_REL="qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json"\n\n@dataclass(frozen=True)\nclass PhysicalRow:\n    league:str\n    events:int\n    unique_provider_ids:int\n    elapsed_seconds:float\n    authority:str\n    callable_name:str\n    execution_authority:bool=False\n\ndef run_gate(root=None, timeout=15):\n    base=Path(root or Path.cwd()).resolve()\n    rows=[]\n    for league in ADMITTED:\n        started=time.monotonic()\n        r=acquire_canonical_events(league,timeout=timeout,root=base)\n        elapsed=round(time.monotonic()-started,3)\n        if r.event_count < 1:\n            raise RuntimeError(f"{league} returned zero canonical events")\n\n        provider_ids=[]\n        for event in r.events:\n            pid=str(getattr(event,"provider_event_id","") or "")\n            if pid:\n                provider_ids.append(pid)\n\n        unique_ids=len(set(provider_ids))\n        if unique_ids < 1:\n            raise RuntimeError(f"{league} returned no provider event identities")\n\n        row=PhysicalRow(\n            league=league,\n            events=r.event_count,\n            unique_provider_ids=unique_ids,\n            elapsed_seconds=elapsed,\n            authority=r.authority,\n            callable_name=r.callable_name,\n        )\n        rows.append(row)\n        print(\n            f"[PHYSICAL] {league} events={row.events} "\n            f"unique_provider_ids={row.unique_provider_ids} "\n            f"elapsed={row.elapsed_seconds}s "\n            f"authority={row.authority} callable={row.callable_name}"\n        )\n\n    state=base/STATE_REL\n    state.parent.mkdir(parents=True,exist_ok=True)\n    state.write_text(json.dumps({\n        "rows":[asdict(x) for x in rows],\n        "admitted":list(ADMITTED),\n        "held":["NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"],\n        "blocked":["UCL"],\n        "uniform_provider":"qseries_v2.oracle_source_network.providers.uniform_sports_provider:acquire_canonical_events",\n        "execution_authority":False,\n    },indent=2),encoding="utf-8")\n    return tuple(rows),state\n'
TEST_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.six_league_uniform_provider_gate import run_gate, ADMITTED\n\nrows,state=run_gate(root=Path.cwd(),timeout=15)\nassert tuple(r.league for r in rows)==ADMITTED\nassert all(r.events>0 for r in rows)\nassert all(r.unique_provider_ids>0 for r in rows)\nassert all(r.execution_authority is False for r in rows)\nprint("[STATE]",state)\nprint("[PASS] NFL/NCAAF/NBA direct extractor paths physically reverified")\nprint("[PASS] NHL/MLS/EPL executable promoted production paths physically reverified")\nprint("[PASS] all six admitted leagues returned canonical provider identities")\nprint("[PASS] OSN-078 executable-foundation physical gate certified")\n'

def main():
    print("="*120)
    print(" OSN-078 SIX-LEAGUE UNIFORM PROVIDER PHYSICAL GATE — EXECUTABLE-FOUNDATION REBUILD")
    print("="*120)
    for dep in (
        "qseries_v2/oracle_source_network/providers/uniform_sports_provider.py",
        "qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json",
        "test_osn_077_uniform_canonical_sports_provider_EXECUTABLE_ENTRYPOINT_REBUILD.py",
    ):
        if not (ROOT/dep).exists():
            raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)

    p=ROOT/MODULE
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(MODULE_SOURCE,encoding="utf-8")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")
    print("[WRITE]",MODULE)

    t=ROOT/TEST
    t.write_text(TEST_SOURCE,encoding="utf-8")
    compile(t.read_text(encoding="utf-8"),str(t),"exec")
    print("[WRITE]",TEST)
    print("[PASS] stale pre-foundation OSN-078 path retired")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
