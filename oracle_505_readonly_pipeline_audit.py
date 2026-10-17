
"""Read-only live scanner/event-bus audit. Never signs, broadcasts, or changes runtime."""
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path('runtime_state')
MODULES = Path('qseries_v2/oracle_execution/solana_atomic_executor')
SIGNALS = ('epoch', 'heartbeat', 'websocket', 'ws_', 'price', 'pricing', 'quote',
           'hydrate', 'replenish', 'candidate', 'publish', 'positive', 'event',
           'snapshot', 'update', 'subscription', 'pair', 'reject')
FORBIDDEN = ('secret', 'private', 'password', 'credential', 'api_key', 'auth', 'seed')


def collect(obj, prefix='', depth=0):
    out = {}
    if depth > 5 or not isinstance(obj, dict):
        return out
    for key, val in list(obj.items())[:150]:
        name = str(key).lower()
        if any(s in name for s in FORBIDDEN):
            continue
        path = (prefix + '.' + str(key)).strip('.')
        if isinstance(val, dict):
            out.update(collect(val, path, depth + 1))
        elif type(val) in (int, float, bool) and any(s in name for s in SIGNALS):
            out[path] = val
    return out


def files():
    dbs, telemetry = [], []
    if not ROOT.exists():
        return dbs, telemetry
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() in ('.sqlite', '.sqlite3', '.db'):
            dbs.append(path)
        elif path.suffix.lower() == '.json' and any(s in str(path).lower()
            for s in ('scanner', 'oracle_500', 'oracle_344', 'oracle_322',
                      'final_boss', 'pricing', 'oracle_504', 'v16')):
            telemetry.append(path)
    dbs.sort(key=lambda p: (
        any(w in str(p).lower() for w in
            ('344', 'scanner', 'bus', 'final_boss')),
        p.stat().st_mtime), reverse=True)
    telemetry.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dbs[:8], telemetry[:10]


def db_snapshot(path):
    try:
        conn = sqlite3.connect(
            path.resolve().as_uri() + '?mode=ro',
            uri=True, timeout=2)
        conn.execute('PRAGMA query_only=ON')
        names = [r[0] for r in conn.execute(
            'SELECT name FROM sqlite_master WHERE type=?', ('table',))]
        result = {}
        for name in names:
            if not any(w in name.lower() for w in
                       ('event', 'candidate', 'heart',
                        'scanner', 'producer', 'opportun')):
                continue
            escaped = '"' + name.replace('"', '""') + '"'
            cols = [r[1] for r in conn.execute(
                'PRAGMA table_info(' + escaped + ')')]
            ident = next((c for c in
                          ('id', 'event_id', 'sequence', 'seq')
                          if c in cols), None)
            metric = next((c for c in
                           ('epoch', 'heartbeat_epoch', 'updated_at',
                            'created_at', 'timestamp', 'event_ts', 'ts')
                           if c in cols), None)
            stats = {'rows': conn.execute(
                'SELECT COUNT(*) FROM ' + escaped).fetchone()[0]}
            for label, col in (('last_id', ident),
                               ('last_marker', metric)):
                if col:
                    v = conn.execute(
                        'SELECT MAX("' + col + '") FROM ' + escaped
                    ).fetchone()[0]
                    if isinstance(v, (int, float)) or (
                        isinstance(v, str) and len(v) <= 40):
                        stats[label] = v
            result[name] = {'columns': cols[:22], 'stats': stats}
        conn.close()
        return result
    except (sqlite3.Error, OSError) as e:
        return {'READ_ERROR': type(e).__name__}


def take(dbs, telemetry):
    out = {'db': {}, 'metrics': {}}
    for p in dbs:
        out['db'][str(p)] = db_snapshot(p)
    for p in telemetry:
        try:
            if p.stat().st_size > 2_000_000:
                continue
            obj = json.loads(p.read_text(encoding='utf-8'))
            out['metrics'][str(p)] = collect(obj)
        except (OSError, ValueError, UnicodeError):
            pass
    return out


def main():
    print('[MODE] READ_ONLY; SCANNER_UNCHANGED; NO_KEY_ACCESS; NO_SIGNING; NO_BROADCAST')
    print('[SOURCE]', [
        (k, sorted(p.name for p in
                   MODULES.glob('oracle_' + k + '*.py'))[:5])
        for k in ('344', '500', '503', '504')])
    dbs, telemetry = files()
    now = time.time()
    print('[DATABASES]', [
        (str(p), round(now - p.stat().st_mtime, 1)) for p in dbs])
    print('[TELEMETRY_FILES]', [
        (str(p), round(now - p.stat().st_mtime, 1))
        for p in telemetry])
    first = take(dbs, telemetry)
    print('[BASELINE_BUS]', json.dumps(first['db'], default=str))
    print('[BASELINE_COUNTERS]',
          json.dumps(first['metrics'], default=str)[:6500])
    print('[SAMPLE] 20 seconds; leave existing scanner and executor untouched')
    time.sleep(20)
    dbs2, telemetry2 = files()
    second = take(dbs2, telemetry2)
    print('[NEW_TELEMETRY]', [
        str(p) for p in telemetry2 if p not in telemetry])
    print('[LATEST_BUS]', json.dumps(second['db'], default=str))
    print('[LATEST_COUNTERS]',
          json.dumps(second['metrics'], default=str)[:6500])
    for name, new in second['metrics'].items():
        old = first['metrics'].get(name, {})
        diff = {
            k: round(v - old[k], 4)
            for k, v in new.items()
            if k in old and type(v) in (int, float)
            and type(old[k]) in (int, float) and v != old[k]
        }
        if diff:
            print('[CHANGED_COUNTERS]', name, diff)
    for name, tables in second['db'].items():
        prev = first['db'].get(name, {})
        for table, new in tables.items():
            if not isinstance(new, dict) or 'stats' not in new:
                continue
            before = prev.get(table, {}).get('stats', {})
            diff = {
                k: new['stats'][k] - before[k]
                for k in ('rows', 'last_id')
                if isinstance(new['stats'].get(k), int)
                and isinstance(before.get(k), int)
            }
            print('[BUS_DELTA]', name, table, diff)
    print('[INTERPRETATION] Positive event delta zero alone does NOT prove pricing is broken.')


if __name__ == '__main__':
    main()
