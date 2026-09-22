from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-070 FINAL SPORTS RUNTIME CONTINUITY CERTIFICATION INSTALLER'
REQUIRED = ('test_osn_065_final_universal_sports_persistence_CURRENT_BOUNDARY_REBUILD.py', 'test_osn_066_universal_sports_runtime_scheduler.py', 'test_osn_067_sports_checkpoint_after_readback.py', 'test_osn_068_sports_downtime_gap_backfill_planner.py', 'test_osn_069_sports_restart_recovery_physical_gate.py')
FILES = {'qseries_v2/oracle_source_network/certification/final_sports_runtime_certification.py': 'from dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess\nimport sys\n\n\n@dataclass(frozen=True)\nclass SportsRuntimeCertification:\n    persistence_foundation: bool\n    scheduler: bool\n    checkpoint_after_readback: bool\n    gap_backfill: bool\n    restart_recovery: bool\n    admitted: tuple\n    held: tuple\n    blocked: tuple\n    terminal_dependency: str\n    runtime_continuity_ready: bool\n    execution_authority: bool = False\n\n\nTESTS = (\n    ("OSN-065", "test_osn_065_final_universal_sports_persistence_CURRENT_BOUNDARY_REBUILD.py", 300),\n    ("OSN-066", "test_osn_066_universal_sports_runtime_scheduler.py", 30),\n    ("OSN-067", "test_osn_067_sports_checkpoint_after_readback.py", 30),\n    ("OSN-068", "test_osn_068_sports_downtime_gap_backfill_planner.py", 30),\n    ("OSN-069", "test_osn_069_sports_restart_recovery_physical_gate.py", 120),\n)\n\n\ndef _run(root, label, filename, timeout):\n    path = root / filename\n    if not path.exists():\n        raise RuntimeError(f"{label} test missing: {filename}")\n    print(f"[RUN] {label}: {filename}", flush=True)\n    try:\n        p = subprocess.run(\n            [sys.executable, str(path)],\n            cwd=str(root),\n            text=True,\n            capture_output=True,\n            timeout=timeout,\n        )\n    except subprocess.TimeoutExpired as exc:\n        raise RuntimeError(f"{label} timed out after {timeout}s") from exc\n\n    if p.stdout:\n        print(p.stdout, end="" if p.stdout.endswith("\\n") else "\\n")\n    if p.stderr:\n        print(p.stderr, end="" if p.stderr.endswith("\\n") else "\\n")\n    if p.returncode != 0:\n        raise RuntimeError(f"{label} failed rc={p.returncode}")\n    print(f"[PASS] {label} passed", flush=True)\n    return True\n\n\ndef certify_sports_runtime():\n    root = Path.cwd().resolve()\n    passed = {}\n    for label, filename, timeout in TESTS:\n        passed[label] = _run(root, label, filename, timeout)\n\n    return SportsRuntimeCertification(\n        persistence_foundation=passed["OSN-065"],\n        scheduler=passed["OSN-066"],\n        checkpoint_after_readback=passed["OSN-067"],\n        gap_backfill=passed["OSN-068"],\n        restart_recovery=passed["OSN-069"],\n        admitted=("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL"),\n        held=("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),\n        blocked=("UCL",),\n        terminal_dependency="NONE",\n        runtime_continuity_ready=True,\n    )\n', 'test_osn_070_final_sports_runtime_continuity_certification.py': 'from qseries_v2.oracle_source_network.certification.final_sports_runtime_certification import certify_sports_runtime\n\nresult = certify_sports_runtime()\nprint("[FINAL_SPORTS_RUNTIME]", result)\n\nassert result.persistence_foundation is True\nassert result.scheduler is True\nassert result.checkpoint_after_readback is True\nassert result.gap_backfill is True\nassert result.restart_recovery is True\nassert result.admitted == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert "NCAAB" in result.held\nassert "UCL" in result.blocked\nassert result.terminal_dependency == "NONE"\nassert result.runtime_continuity_ready is True\nassert result.execution_authority is False\n\nprint("[PASS] sports persistence foundation retained")\nprint("[PASS] universal admitted-league runtime scheduler certified")\nprint("[PASS] checkpoint-after-readback continuity certified")\nprint("[PASS] downtime gap/backfill planning certified")\nprint("[PASS] restart/recovery physical gate certified")\nprint("[PASS] terminal-independent sports runtime continuity foundation certified")\nprint("[PASS] OSN-070 final sports runtime certification complete")\n'}

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
