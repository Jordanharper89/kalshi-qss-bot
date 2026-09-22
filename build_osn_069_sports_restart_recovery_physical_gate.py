from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-069 SPORTS RESTART RECOVERY PHYSICAL GATE INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py', 'qseries_v2/oracle_source_network/persistence/sports_runtime_checkpoint.py', 'qseries_v2/oracle_source_network/runtime/sports_gap_backfill_plan.py')
FILES = {'qseries_v2/oracle_source_network/certification/sports_restart_recovery_gate.py': 'from dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import read_checkpoint\nfrom qseries_v2.oracle_source_network.runtime.sports_gap_backfill_plan import plan_gap_backfill\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import exact_readback, readback_count\n\n\n@dataclass(frozen=True)\nclass RestartRecovery:\n    league: str\n    checkpoint_found: bool\n    checkpoint_observation_durable: bool\n    replay_resubmitted: bool\n    gap_seconds: int\n    backfill_windows: int\n    recovery_status: str\n    execution_authority: bool = False\n\n\ndef recover_from_checkpoint(league, root=None, now=None):\n    base = Path(root or Path.cwd()).resolve()\n    checkpoint = read_checkpoint(league, root=base)\n    if checkpoint is None:\n        return RestartRecovery(\n            league=str(league),\n            checkpoint_found=False,\n            checkpoint_observation_durable=False,\n            replay_resubmitted=False,\n            gap_seconds=0,\n            backfill_windows=0,\n            recovery_status="NO_CHECKPOINT_FULL_DISCOVERY_REQUIRED",\n        )\n\n    readback = exact_readback(checkpoint.observation_id, root=base)\n    durable = readback_count(readback) >= 1\n    if not durable:\n        raise RuntimeError("checkpoint points to non-durable observation")\n\n    current = now or datetime.now(timezone.utc).isoformat()\n    gap = plan_gap_backfill(\n        league,\n        checkpoint.observed_at,\n        current,\n    )\n\n    return RestartRecovery(\n        league=str(league),\n        checkpoint_found=True,\n        checkpoint_observation_durable=True,\n        replay_resubmitted=False,\n        gap_seconds=gap.gap_seconds,\n        backfill_windows=len(gap.windows),\n        recovery_status="RECONCILE_BACKFILL_THEN_RESUME" if gap.windows else "RESUME_LIVE",\n    )\n', 'test_osn_069_sports_restart_recovery_physical_gate.py': 'from datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\nfrom qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import commit_checkpoint_after_readback\nfrom qseries_v2.oracle_source_network.certification.sports_restart_recovery_gate import recover_from_checkpoint\n\nphysical = persist_fixture(timeout_seconds=45.0)\nprint("[PHYSICAL]", physical)\nassert physical.exact_readback >= 1\n\nobserved = datetime.now(timezone.utc).isoformat()\ncheckpoint = commit_checkpoint_after_readback(\n    "NFL",\n    physical.observation_id,\n    observed,\n    physical.exact_readback,\n    root=Path.cwd(),\n)\nprint("[CHECKPOINT]", checkpoint)\n\nrecovery = recover_from_checkpoint(\n    "NFL",\n    root=Path.cwd(),\n    now=observed,\n)\nprint("[RESTART_RECOVERY]", recovery)\n\nassert recovery.checkpoint_found is True\nassert recovery.checkpoint_observation_durable is True\nassert recovery.replay_resubmitted is False\nassert recovery.gap_seconds == 0\nassert recovery.backfill_windows == 0\nassert recovery.recovery_status == "RESUME_LIVE"\nassert recovery.execution_authority is False\n\nprint("[PASS] restart reloaded durable sports checkpoint")\nprint("[PASS] checkpoint observation exact-readback verified before resume")\nprint("[PASS] already-durable observation not resubmitted")\nprint("[PASS] zero-gap restart resumes live safely")\nprint("[PASS] OSN-069 restart recovery physical gate certified")\n'}

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit('[FAIL] missing dependency: ' + rel)
    print('[PASS] dependency verified:', rel)
    return p

def write_compile(rel, source):
    compile(source, rel, 'exec')
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding='utf-8')
    compile(p.read_text(encoding='utf-8'), str(p), 'exec')
    print('[WRITE]', rel)
    print('[PASS] post-write compile verified:', rel)

def main():
    print('=' * 120)
    print(' ' + TITLE)
    print('=' * 120)
    for rel in REQUIRED:
        require(rel)
    for rel, source in FILES.items():
        write_compile(rel, source)
    print('[PASS] installer completed')
    print('[PASS] execution_authority=FALSE')

if __name__ == '__main__':
    main()
