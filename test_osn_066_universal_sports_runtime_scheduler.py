import threading
from qseries_v2.oracle_source_network.runtime.sports_runtime_scheduler import (
    build_runtime_plan,
    run_cycle,
    run_forever,
)

plan = build_runtime_plan()
print("[RUNTIME_PLAN]", plan)
assert plan.admitted == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")
assert "NCAAB" in plan.held
assert "UCL" in plan.blocked
assert plan.terminal_dependency == "NONE"
assert plan.execution_authority is False

seen = []
cycle = run_cycle(lambda league: seen.append(league) or True)
print("[RUNTIME_CYCLE]", cycle)
assert tuple(seen) == plan.admitted
assert cycle.successes == plan.admitted
assert cycle.failures == ()

stop = threading.Event()
calls = []
def bounded(league):
    calls.append(league)
    if len(calls) >= len(plan.admitted):
        stop.set()
    return True

cycles = run_forever(bounded, stop_event=stop, sleep_seconds=0.05)
assert cycles == 1
assert tuple(calls) == plan.admitted

print("[PASS] six admitted leagues scheduled by one venue-neutral worker")
print("[PASS] held/blocked leagues cannot enter active schedule")
print("[PASS] bounded continuous-loop contract certified")
print("[PASS] terminal_dependency=NONE")
print("[PASS] OSN-066 sports runtime scheduler certified")
