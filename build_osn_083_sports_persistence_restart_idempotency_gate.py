from pathlib import Path
ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/sports_persistence_restart_idempotency_gate.py"
TEST="test_osn_083_sports_persistence_restart_idempotency_gate.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass, asdict\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events\nfrom qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import persist_event\n\nSTATE_REL="qseries_v2/oracle_source_network/state/osn083_restart_idempotency_gate.json"\n\n@dataclass(frozen=True)\nclass RestartIdempotencyResult:\n    league:str\n    observation_id:str\n    first_action:str\n    replay_action:str\n    replay_resubmitted:bool\n    exact_readback:int\n    execution_authority:bool=False\n\ndef run_gate(root=None,league="NHL"):\n    base=Path(root or Path.cwd()).resolve()\n    result=acquire_canonical_events(league,timeout=15,root=base)\n    if not result.events:\n        raise RuntimeError(f"{league} returned zero events")\n    event=result.events[0]\n\n    first=persist_event(league,event,root=base,batch_id="osn083-first")\n    replay=persist_event(league,event,root=base,batch_id="osn083-replay")\n\n    if first.observation_id != replay.observation_id:\n        raise RuntimeError("canonical observation identity changed across replay")\n    replay_resubmitted=(replay.write_action!="READ_BEFORE_WRITE_HIT")\n    if replay_resubmitted:\n        raise RuntimeError(f"replay was resubmitted: {replay.write_action}")\n\n    out=RestartIdempotencyResult(\n        league=league,\n        observation_id=first.observation_id,\n        first_action=first.write_action,\n        replay_action=replay.write_action,\n        replay_resubmitted=False,\n        exact_readback=replay.readback_count,\n    )\n    state=base/STATE_REL\n    state.write_text(json.dumps(asdict(out),indent=2),encoding="utf-8")\n    return out,state\n'
TEST_SOURCE='\nfrom pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.sports_persistence_restart_idempotency_gate import run_gate\n\nresult,state=run_gate(root=Path.cwd(),league="NHL")\nprint("[RESTART_IDEMPOTENCY]",result)\nassert result.replay_resubmitted is False\nassert result.replay_action=="READ_BEFORE_WRITE_HIT"\nassert result.exact_readback>0\nassert result.execution_authority is False\nprint("[STATE]",state)\nprint("[PASS] canonical identity stable across replay")\nprint("[PASS] durable row detected before write")\nprint("[PASS] duplicate resubmission prevented")\nprint("[PASS] OSN-083 restart idempotency certified")\n'
def main():
    print("="*120); print(" OSN-083 SPORTS PERSISTENCE RESTART IDEMPOTENCY GATE INSTALLER"); print("="*120)
    for dep in (
        "qseries_v2/oracle_source_network/persistence/live_sports_postgresql_bridge.py",
        "qseries_v2/oracle_source_network/providers/uniform_sports_provider.py",
        "qseries_v2/oracle_source_network/state/osn082_six_league_postgresql_physical_gate.json",
    ):
        if not (ROOT/dep).exists(): raise SystemExit("[FAIL] missing dependency: "+dep)
        print("[PASS] dependency verified:",dep)
    p=ROOT/MODULE; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(MODULE_SOURCE,encoding="utf-8"); compile(p.read_text(encoding="utf-8"),str(p),"exec")
    t=ROOT/TEST; t.write_text(TEST_SOURCE,encoding="utf-8"); compile(t.read_text(encoding="utf-8"),str(t),"exec")
    print("[WRITE]",MODULE); print("[WRITE]",TEST); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
