from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-066 UNIVERSAL SPORTS RUNTIME SCHEDULER INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/certification/pre_persistence_sports_event_certification.py',)
FILES = {'qseries_v2/oracle_source_network/runtime/sports_runtime_scheduler.py': 'from dataclasses import dataclass\nfrom datetime import datetime, timezone\nimport threading\nimport time\n\nADMITTED = ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nHELD = ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")\nBLOCKED = ("UCL",)\n\nDEFAULT_CADENCE_SECONDS = {\n    "NFL": 30.0,\n    "NCAAF": 30.0,\n    "NBA": 30.0,\n    "NHL": 30.0,\n    "MLS": 30.0,\n    "EPL": 30.0,\n}\n\n\n@dataclass(frozen=True)\nclass RuntimePlan:\n    admitted: tuple\n    held: tuple\n    blocked: tuple\n    cadence_seconds: dict\n    terminal_dependency: str\n    execution_authority: bool = False\n\n\n@dataclass(frozen=True)\nclass RuntimeCycle:\n    started_at: str\n    finished_at: str\n    leagues_attempted: tuple\n    successes: tuple\n    failures: tuple\n    execution_authority: bool = False\n\n\ndef build_runtime_plan():\n    return RuntimePlan(\n        admitted=ADMITTED,\n        held=HELD,\n        blocked=BLOCKED,\n        cadence_seconds=dict(DEFAULT_CADENCE_SECONDS),\n        terminal_dependency="NONE",\n    )\n\n\ndef run_cycle(acquire_one):\n    started = datetime.now(timezone.utc).isoformat()\n    successes = []\n    failures = []\n    for league in ADMITTED:\n        try:\n            result = acquire_one(league)\n            if result is False:\n                failures.append((league, "CALLBACK_FALSE"))\n            else:\n                successes.append(league)\n        except Exception as exc:\n            failures.append((league, type(exc).__name__))\n    finished = datetime.now(timezone.utc).isoformat()\n    return RuntimeCycle(\n        started_at=started,\n        finished_at=finished,\n        leagues_attempted=ADMITTED,\n        successes=tuple(successes),\n        failures=tuple(failures),\n    )\n\n\ndef run_forever(acquire_one, stop_event=None, sleep_seconds=30.0):\n    stop = stop_event or threading.Event()\n    cycles = 0\n    while not stop.is_set():\n        run_cycle(acquire_one)\n        cycles += 1\n        stop.wait(max(0.05, float(sleep_seconds)))\n    return cycles\n', 'test_osn_066_universal_sports_runtime_scheduler.py': 'import threading\nfrom qseries_v2.oracle_source_network.runtime.sports_runtime_scheduler import (\n    build_runtime_plan,\n    run_cycle,\n    run_forever,\n)\n\nplan = build_runtime_plan()\nprint("[RUNTIME_PLAN]", plan)\nassert plan.admitted == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")\nassert "NCAAB" in plan.held\nassert "UCL" in plan.blocked\nassert plan.terminal_dependency == "NONE"\nassert plan.execution_authority is False\n\nseen = []\ncycle = run_cycle(lambda league: seen.append(league) or True)\nprint("[RUNTIME_CYCLE]", cycle)\nassert tuple(seen) == plan.admitted\nassert cycle.successes == plan.admitted\nassert cycle.failures == ()\n\nstop = threading.Event()\ncalls = []\ndef bounded(league):\n    calls.append(league)\n    if len(calls) >= len(plan.admitted):\n        stop.set()\n    return True\n\ncycles = run_forever(bounded, stop_event=stop, sleep_seconds=0.05)\nassert cycles == 1\nassert tuple(calls) == plan.admitted\n\nprint("[PASS] six admitted leagues scheduled by one venue-neutral worker")\nprint("[PASS] held/blocked leagues cannot enter active schedule")\nprint("[PASS] bounded continuous-loop contract certified")\nprint("[PASS] terminal_dependency=NONE")\nprint("[PASS] OSN-066 sports runtime scheduler certified")\n'}

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