from pathlib import Path

ROOT = Path.cwd()
TITLE = 'OSN-068 SPORTS DOWNTIME GAP/BACKFILL PLANNER INSTALLER'
REQUIRED = ('qseries_v2/oracle_source_network/persistence/sports_runtime_checkpoint.py',)
FILES = {'qseries_v2/oracle_source_network/runtime/sports_gap_backfill_plan.py': 'from dataclasses import dataclass\nfrom datetime import datetime, timedelta, timezone\n\n\n@dataclass(frozen=True)\nclass BackfillWindow:\n    league: str\n    start: str\n    end: str\n\n\n@dataclass(frozen=True)\nclass GapPlan:\n    league: str\n    checkpoint_time: str\n    current_time: str\n    gap_seconds: int\n    windows: tuple\n    continuity_status: str\n    execution_authority: bool = False\n\n\ndef _dt(value):\n    text = str(value).replace("Z", "+00:00")\n    value = datetime.fromisoformat(text)\n    if value.tzinfo is None:\n        value = value.replace(tzinfo=timezone.utc)\n    return value.astimezone(timezone.utc)\n\n\ndef plan_gap_backfill(league, checkpoint_time, current_time, max_window_seconds=300):\n    start = _dt(checkpoint_time)\n    end = _dt(current_time)\n    if end < start:\n        raise ValueError("current_time precedes checkpoint_time")\n\n    gap = int((end - start).total_seconds())\n    if gap == 0:\n        return GapPlan(\n            league=str(league),\n            checkpoint_time=start.isoformat(),\n            current_time=end.isoformat(),\n            gap_seconds=0,\n            windows=(),\n            continuity_status="CONTIGUOUS",\n        )\n\n    max_window = max(1, int(max_window_seconds))\n    windows = []\n    cursor = start\n    while cursor < end:\n        nxt = min(cursor + timedelta(seconds=max_window), end)\n        windows.append(\n            BackfillWindow(\n                league=str(league),\n                start=cursor.isoformat(),\n                end=nxt.isoformat(),\n            )\n        )\n        cursor = nxt\n\n    return GapPlan(\n        league=str(league),\n        checkpoint_time=start.isoformat(),\n        current_time=end.isoformat(),\n        gap_seconds=gap,\n        windows=tuple(windows),\n        continuity_status="BACKFILL_REQUIRED",\n    )\n', 'test_osn_068_sports_downtime_gap_backfill_planner.py': 'from qseries_v2.oracle_source_network.runtime.sports_gap_backfill_plan import plan_gap_backfill\n\nsame = plan_gap_backfill(\n    "NFL",\n    "2026-09-05T20:00:00+00:00",\n    "2026-09-05T20:00:00+00:00",\n)\nprint("[NO_GAP]", same)\nassert same.continuity_status == "CONTIGUOUS"\nassert same.windows == ()\n\ngap = plan_gap_backfill(\n    "NFL",\n    "2026-09-05T20:00:00+00:00",\n    "2026-09-05T20:17:00+00:00",\n    max_window_seconds=300,\n)\nprint("[GAP]", gap)\nassert gap.gap_seconds == 1020\nassert gap.continuity_status == "BACKFILL_REQUIRED"\nassert len(gap.windows) == 4\nassert gap.windows[0].start == "2026-09-05T20:00:00+00:00"\nassert gap.windows[-1].end == "2026-09-05T20:17:00+00:00"\nassert gap.execution_authority is False\n\nprint("[PASS] zero-gap continuity detected")\nprint("[PASS] downtime gap split into bounded backfill windows")\nprint("[PASS] no unrecoverable time silently discarded")\nprint("[PASS] OSN-068 sports gap/backfill planner certified")\n'}

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
