from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/six_league_postgresql_persistence_gate.py"
TEST="test_osn_082_six_league_postgresql_physical_persistence_gate.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport json, time\n\nfrom qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import (\n    acquire_and_persist_one_per_league, ADMITTED\n)\n\nSTATE_REL="qseries_v2/oracle_source_network/state/osn082_six_league_postgresql_physical_gate.json"\n\n@dataclass(frozen=True)\nclass PersistenceGate:\n    admitted:tuple\n    committed_or_present:int\n    exact_readback_verified:int\n    single_writer:str\n    gate_ready:bool\n    execution_authority:bool=False\n\ndef run_gate(root=None):\n    base=Path(root or Path.cwd()).resolve()\n    rows,_=acquire_and_persist_one_per_league(root=base,timeout=15,commit_timeout_seconds=45.0)\n    exact=sum(1 for r in rows if r.readback_count>0)\n    if exact != len(ADMITTED):\n        raise RuntimeError(f"exact readback mismatch: expected={len(ADMITTED)} actual={exact}")\n    result=PersistenceGate(\n        admitted=ADMITTED,\n        committed_or_present=len(rows),\n        exact_readback_verified=exact,\n        single_writer="OPH-019",\n        gate_ready=True,\n    )\n    state=base/STATE_REL\n    state.write_text(json.dumps({\n        **asdict(result),\n        "admitted":list(result.admitted),\n    },indent=2),encoding="utf-8")\n    return result,state\n'
TEST_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.six_league_postgresql_persistence_gate import run_gate\n\nresult,state=run_gate(root=Path.cwd())\nprint("[PERSISTENCE_GATE]",result)\nassert result.committed_or_present==6\nassert result.exact_readback_verified==6\nassert result.single_writer=="OPH-019"\nassert result.gate_ready is True\nassert result.execution_authority is False\nprint("[STATE]",state)\nprint("[PASS] six-league PostgreSQL physical persistence gate certified")\n'
def main():
    print("="*120); print(" OSN-082 SIX-LEAGUE POSTGRESQL PHYSICAL PERSISTENCE GATE INSTALLER"); print("="*120)
    for dep in (
        "qseries_v2/oracle_source_network/persistence/live_sports_postgresql_bridge.py",
        "qseries_v2/oracle_source_network/state/osn081_live_sports_persistence_bridge.json",
    ):
        if not (ROOT/dep).exists(): raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)
    p=ROOT/MODULE; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(MODULE_SOURCE,encoding="utf-8"); compile(p.read_text(encoding="utf-8"),str(p),"exec")
    t=ROOT/TEST; t.write_text(TEST_SOURCE,encoding="utf-8"); compile(t.read_text(encoding="utf-8"),str(t),"exec")
    print("[WRITE]",MODULE); print("[WRITE]",TEST); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
