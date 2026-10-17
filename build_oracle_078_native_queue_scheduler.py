"""ORACLE-078 full installer: replace native scheduling method, preserve original scanner."""
import ast
from collections import Counter, deque
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_050_original_scanner_executor_consolidation.py')
MARK = 'ORACLE078_FRESH_NATIVE_FIRST_JOURNAL_CERTIFIED'
METHOD = '''    def _consume(self):
        # ORACLE078_FRESH_NATIVE_FIRST_JOURNAL_CERTIFIED
        from collections import deque
        output = self.root / JOURNAL
        output.parent.mkdir(parents=True, exist_ok=True)
        journaled = set()
        history = deque(maxlen=1024)

        def key(row, stamp):
            return (row.get("token"), row.get("direction"),
                    row.get("start_lamports", row.get("start")), stamp)

        def persist(row):
            born = row.get("observed_ns")
            if type(born) is not int or born > self.clock() or self.clock() - born > MAX_AGE_NS:
                self.holds["HANDOFF_EXPIRED_BEFORE_CONSUMPTION"] += 1
                return False
            row["gate"] = "AWAITING_ATOMIC_SIMULATION_AND_ACTUAL_NET_PROFIT"
            try:
                with output.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\\n")
                self.ingress_written += 1
                k = key(row, born)
                if k not in journaled:
                    if len(history) == history.maxlen:
                        journaled.discard(history.popleft())
                    history.append(k)
                    journaled.add(k)
                return True
            except OSError:
                self.holds["HANDOFF_PERSISTENCE_FAILED"] += 1
                return False

        while not self.ingress_stop.is_set() or self.pending or self.native_pending:
            # A live WS feed can keep pending nonempty indefinitely.
            # Prioritize the freshest native entry, but persist its matching
            # inert handoff BEFORE attempting an unsigned simulation.
            if self.native_pending:
                item = self.native_pending.pop()
                snap, opportunity, born_ns = item
                if (type(born_ns) is not int or born_ns > self.clock()
                        or self.clock() - born_ns > MAX_AGE_NS):
                    self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_BUILD"] += 1
                    continue
                k = key(opportunity, born_ns)
                if k not in journaled:
                    match = next((r for r in tuple(self.pending)
                                  if key(r, r.get("observed_ns")) == k), None)
                    if match is None:
                        self.holds["NATIVE_JOURNAL_MATCH_MISSING"] += 1
                        continue
                    try:
                        self.pending.remove(match)
                    except ValueError:
                        self.holds["NATIVE_JOURNAL_MATCH_LOST"] += 1
                        continue
                    if not persist(match):
                        self.holds["NATIVE_JOURNAL_WRITE_HOLD"] += 1
                        continue
                if self.clock() - born_ns > MAX_AGE_NS:
                    self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_BUILD"] += 1
                    continue
                self._simulate_p2m_once(item)
                continue
            if self.pending:
                persist(self.pending.popleft())
                continue
            time.sleep(.02)
'''


def changed(original):
    tree = ast.parse(original)
    found = [(c, n) for c in tree.body if isinstance(c, ast.ClassDef)
             for n in c.body if isinstance(n, ast.FunctionDef) and n.name == '_consume']
    if len(found) != 1:
        raise RuntimeError('ORACLE078_CONSUMER_NOT_UNIQUE')
    _, node = found[0]
    if MARK in original:
        return original
    old = '\n'.join(original.splitlines()[node.lineno-1:node.end_lineno])
    if not all(x in old for x in ('self.native_pending', 'self.pending', 'self._simulate_p2m_once', 'JOURNAL')):
        raise RuntimeError('ORACLE078_SOURCE_CONTRACT_MISMATCH')
    lines = original.splitlines(keepends=True)
    updated = ''.join(lines[:node.lineno-1]) + METHOD + ''.join(lines[node.end_lineno:])
    ast.parse(updated)
    return updated


def test_scheduler():
    namespace = {'JOURNAL': Path('handoff.jsonl'), 'MAX_AGE_NS': 750_000_000,
                 'deque': deque, 'json': json, 'time': time}
    exec('class Worker:\n' + METHOD, namespace)
    Worker = namespace['Worker']
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        now = 1_000_000_000
        w = Worker()
        w.root = base
        w.ingress_stop = threading.Event()
        w.ingress_stop.set()
        w.holds = Counter()
        w.ingress_written = 0
        w.clock = lambda: now
        w.pending = deque([{'token': x, 'direction': 'PUMP_TO_METEORA',
                            'start_lamports': 10_000_000, 'observed_ns': now}
                           for x in ('old', 'new')])
        w.native_pending = deque([({'s': 1}, {'token': x, 'direction': 'PUMP_TO_METEORA',
                                             'start': 10_000_000}, now)
                                  for x in ('old', 'new')])
        seen = []
        def execute(item):
            lines = (base / 'handoff.jsonl').read_text().splitlines()
            token = item[1]['token']
            assert any(json.loads(x)['token'] == token for x in lines)
            seen.append(token)
        w._simulate_p2m_once = execute
        w._consume()
        assert seen == ['new', 'old'], seen
        assert w.ingress_written == 2 and not w.holds, w.holds
        w2 = Worker()
        w2.root = base
        w2.ingress_stop = threading.Event()
        w2.ingress_stop.set()
        w2.holds = Counter()
        w2.ingress_written = 0
        w2.clock = lambda: now
        w2.pending = deque()
        w2.native_pending = deque([({}, {'token': 'orphan', 'start': 10_000_000}, now)])
        w2._simulate_p2m_once = lambda item: (_ for _ in ()).throw(AssertionError('orphan executed'))
        w2._consume()
        assert w2.holds['NATIVE_JOURNAL_MATCH_MISSING'] == 1
    print('[PASS] ORACLE078_FRESH_FIRST_JOURNAL_BEFORE_NATIVE')
    print('[PASS] ORACLE078_ORPHAN_NATIVE_FAIL_CLOSED')


def install():
    test_scheduler()
    original = TARGET.read_text(encoding='utf-8')
    updated = changed(original)
    if original == updated:
        print('[PASS] ORACLE078_ALREADY_INSTALLED')
        return
    backup = TARGET.with_name(TARGET.stem + '.before_oracle078.py')
    if backup.exists() and backup.read_text(encoding='utf-8') != original:
        raise RuntimeError('ORACLE078_BACKUP_CONFLICT')
    if not backup.exists():
        shutil.copy2(TARGET, backup)
    temporary = TARGET.with_suffix('.oracle078.tmp')
    temporary.write_text(updated, encoding='utf-8')
    os.replace(temporary, TARGET)
    print('[PASS] ORACLE078_CANONICAL_NATIVE_SCHEDULER_INSTALLED')
    print('[BOUNDARY] ORIGINAL_WS_SCANNER_UNCHANGED_NO_RPC_NO_SIGNING_NO_BROADCAST')


if __name__ == '__main__':
    if '--test' in sys.argv:
        test_scheduler()
        if TARGET.is_file():
            ast.parse(TARGET.read_text(encoding='utf-8'))
            print('[PASS] ORACLE078_LOCAL_SOURCE_AST')
    else:
        install()