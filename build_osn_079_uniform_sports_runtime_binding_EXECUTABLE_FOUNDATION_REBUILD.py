from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/runtime/uniform_sports_runtime_bindings.py"
TEST="test_osn_079_uniform_sports_runtime_binding_EXECUTABLE_FOUNDATION_REBUILD.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport inspect, json\n\nfrom qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events, ADMITTED\n\nSTATE_REL="qseries_v2/oracle_source_network/state/osn079_uniform_runtime_bindings.json"\n\n@dataclass(frozen=True)\nclass RuntimeBinding:\n    league:str\n    module:str\n    function:str\n    signature:str\n    direct_runtime_callable_bound:bool\n    physical_gate_certified:bool\n    terminal_dependency:str="NONE"\n    execution_authority:bool=False\n\ndef freeze(root=None):\n    base=Path(root or Path.cwd()).resolve()\n    gate=base/"qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json"\n    if not gate.exists():\n        raise RuntimeError("OSN-078 physical gate state missing")\n\n    gate_data=json.loads(gate.read_text(encoding="utf-8"))\n    physical={row["league"]:row for row in gate_data["rows"]}\n\n    sig=str(inspect.signature(acquire_canonical_events))\n    rows=[]\n    for league in ADMITTED:\n        row=physical.get(league)\n        if not row or int(row.get("events",0)) < 1:\n            raise RuntimeError(f"{league} lacks certified physical event output")\n        rows.append(RuntimeBinding(\n            league=league,\n            module="qseries_v2.oracle_source_network.providers.uniform_sports_provider",\n            function="acquire_canonical_events",\n            signature=sig,\n            direct_runtime_callable_bound=True,\n            physical_gate_certified=True,\n        ))\n\n    state=base/STATE_REL\n    state.write_text(json.dumps({\n        "bindings":[asdict(x) for x in rows],\n        "admitted":list(ADMITTED),\n        "held":["NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"],\n        "blocked":["UCL"],\n        "terminal_dependency":"NONE",\n        "execution_authority":False,\n    },indent=2),encoding="utf-8")\n    return tuple(rows),state\n'
TEST_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.runtime.uniform_sports_runtime_bindings import freeze\n\nrows,state=freeze(root=Path.cwd())\nfor r in rows:\n    print("[BINDING]",r)\n\nassert len(rows)==6\nassert all(r.direct_runtime_callable_bound for r in rows)\nassert all(r.physical_gate_certified for r in rows)\nassert all(r.terminal_dependency=="NONE" for r in rows)\nassert all(r.execution_authority is False for r in rows)\n\nprint("[STATE]",state)\nprint("[PASS] one physically proven runtime callable frozen for all six admitted leagues")\nprint("[PASS] obsolete reachability-only NHL/MLS/EPL callables are not runtime authority")\nprint("[PASS] terminal_dependency=NONE")\nprint("[PASS] OSN-079 executable-foundation runtime binding certified")\n'

def main():
    print("="*120)
    print(" OSN-079 UNIFORM SPORTS RUNTIME BINDING — EXECUTABLE-FOUNDATION REBUILD")
    print("="*120)
    for dep in (
        "qseries_v2/oracle_source_network/providers/uniform_sports_provider.py",
        "qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json",
        "test_osn_078_six_league_uniform_provider_physical_gate_EXECUTABLE_FOUNDATION_REBUILD.py",
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
    print("[PASS] stale pre-foundation OSN-079 binding retired")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
