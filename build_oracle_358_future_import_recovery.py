from __future__ import annotations
"""ORACLE-358 full replacement installer: repair ORACLE-357 import placement."""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import py_compile
import re
import sys
import tempfile
import unittest

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_352_scanner_bank_alignment.py'
GUARD = ROOT / 'oracle_357_bus_contract.py'
IMPORT = 'from qseries_v2.oracle_execution.solana_atomic_executor import oracle_357_bus_contract as oracle357'
OLD_LOOP = 'for nom in old351.keep_latest(entries):'
NEW_LOOP = 'for nom in oracle357.keep_latest_valid(entries, counts):'

GUARD_SOURCE = '''"""ORACLE-357: strict, local, no-RPC nomination validation/coalescing."""
from collections.abc import Mapping

FIELDS = ('id', 'token', 'pump_pool', 'meteora_pool', 'direction', 'size_lamports', 'created_ns')
DIRECTIONS = frozenset(('PUMP_TO_METEORA', 'METEORA_TO_PUMP'))
MIN_SIZE = 10_000_000
MAX_SIZE = 100_000_000

def _valid(n):
    if not isinstance(n, Mapping):
        return None, 'NON_MAPPING'
    if any(f not in n for f in FIELDS):
        return None, 'MISSING_FIELDS'
    if not all(isinstance(n[f], str) and n[f].strip() for f in ('token', 'pump_pool', 'meteora_pool')):
        return None, 'INVALID_IDENTITY'
    if n['direction'] not in DIRECTIONS:
        return None, 'INVALID_DIRECTION'
    try:
        ident = int(n['id'])
        size = int(n['size_lamports'])
        created = int(n['created_ns'])
    except (ValueError, TypeError, OverflowError):
        return None, 'INVALID_NUMERIC'
    if ident <= 0 or created <= 0 or size < MIN_SIZE or size > MAX_SIZE:
        return None, 'INVALID_BOUNDS'
    # Accept only genuinely integral numeric fields; no floats/booleans as IDs/sizes.
    for k, value in (('id', ident), ('size_lamports', size), ('created_ns', created)):
        raw = n[k]
        if isinstance(raw, bool) or isinstance(raw, float) or str(raw) != str(value):
            return None, 'NON_CANONICAL_NUMERIC'
    return dict(n), None

def keep_latest_valid(rows, counts):
    # No speculative decoding: scanner.new_events must return a list/tuple of nominations.
    if not isinstance(rows, (list, tuple)):
        counts['bus_contract_bad_batch'] += 1
        return []
    latest = {}
    for row in rows:
        n, reason = _valid(row)
        if reason:
            counts['bus_contract_' + reason] += 1
            continue
        key = (n['token'], n['pump_pool'], n['meteora_pool'], n['direction'], int(n['size_lamports']))
        ident = int(n['id'])
        if key not in latest or ident > int(latest[key]['id']):
            if key in latest:
                counts['bus_contract_superseded'] += 1
            latest[key] = n
        else:
            counts['bus_contract_superseded'] += 1
    return sorted(latest.values(), key=lambda n: int(n['id']))
'''

def digest(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def repair(s):
    # Must recognize the precise ORACLE-357 modification. Stop on anything unexpected.
    if s.count(IMPORT) > 1:
        raise RuntimeError('DUPLICATE_GUARD_IMPORT_STOP')
    if NEW_LOOP not in s and OLD_LOOP not in s:
        raise RuntimeError('BUS_LOOP_NOT_FOUND_STOP')
    if not all(x in s for x in ('def main():', 'identity.vetted(nom,inv,hb)', 'scan.new_events(c,cursor)',
                                "nom['size_lamports']", "nom['created_ns']")):
        raise RuntimeError('ORACLE352_CONTRACT_MISMATCH_STOP')
    if s.count(NEW_LOOP) > 1 or s.count(OLD_LOOP) > 1:
        raise RuntimeError('DUPLICATE_BUS_LOOP_STOP')
    # Strip ONLY the known exact added import, regardless of where 357 placed it.
    lines = s.splitlines(keepends=True)
    lines = [line for line in lines if line.strip() != IMPORT]
    s = ''.join(lines)
    if OLD_LOOP in s:
        s = s.replace(OLD_LOOP, NEW_LOOP, 1)
    # Parse the unmodified future header location without attempting to execute anything.
    future = re.findall(r'(?m)^from __future__ import annotations\s*$', s)
    if len(future) != 1:
        raise RuntimeError('FUTURE_HEADER_NOT_UNIQUE_STOP')
    s = re.sub(r'(?m)^(from __future__ import annotations)\s*$',
               lambda m: m.group(1) + '\n' + IMPORT, s, count=1)
    compile(s, str(TARGET), "exec")
    return s


def guard_source():
    # Self-contained installer: no need to re-run broken ORACLE-357 installer.
    ast.parse(GUARD_SOURCE)
    return GUARD_SOURCE


def install():
    if not TARGET.is_file():
        raise RuntimeError('ORACLE352_NOT_FOUND_STOP')
    current = TARGET.read_text(encoding='utf-8')
    fixed = repair(current)
    expected_guard = guard_source()
    if GUARD.exists() and GUARD.read_text(encoding='utf-8') != expected_guard:
        raise RuntimeError('ORACLE357_GUARD_CHANGED_STOP')
    # Unique, immutable original-state backup prior to modifying target.
    backup = TARGET.with_name('oracle_352_pre358_' + digest(current)[:16] + '.bak')
    if not backup.exists():
        backup.write_text(current, encoding='utf-8')
    if backup.read_text(encoding='utf-8') != current:
        raise RuntimeError('BACKUP_VERIFY_FAILED_STOP')
    tmp = TARGET.with_name(TARGET.name + '.oracle358.tmp')
    tmp.write_text(fixed, encoding='utf-8')
    py_compile.compile(str(tmp), doraise=True)
    if tmp.read_text(encoding='utf-8') != fixed:
        raise RuntimeError('STAGED_WRITE_VERIFY_FAILED_STOP')
    # Atomic replacement on the same volume. No scanner modifications.
    os.replace(tmp, TARGET)
    GUARD.write_text(expected_guard, encoding='utf-8')
    py_compile.compile(str(TARGET), doraise=True)
    py_compile.compile(str(GUARD), doraise=True)
    print('[ORACLE358_INSTALL_PASS]', TARGET, 'sha256=' + digest(fixed))
    print('[ORACLE358_GUARD_PASS]', GUARD, 'sha256=' + digest(expected_guard))
    print('[SCOPE] ORACLE322_FROZEN ORACLE352_HEADER_REPAIRED NO_RPC_WS NO_SIGN_NO_BROADCAST')


def audit():
    src = TARGET.read_text(encoding='utf-8')
    assert repair(src) == src, 'HEADER_NOT_CANONICAL'
    assert src.count(IMPORT) == 1 and src.count(NEW_LOOP) == 1, 'GUARD_NOT_INTEGRATED'
    assert OLD_LOOP not in src, 'UNSAFE_LOOP_PRESENT'
    assert GUARD.read_text(encoding='utf-8') == guard_source(), 'GUARD_CHANGED'
    py_compile.compile(str(TARGET), doraise=True)
    py_compile.compile(str(GUARD), doraise=True)
    print('[ORACLE358_AUDIT_PASS] ORACLE352_COMPILED ORACLE357_GUARD_RETAINED ORACLE322_FROZEN')


def test():
    broken = (IMPORT + '\nfrom __future__ import annotations\n'
              'def main(): pass\n'
              '# identity.vetted(nom,inv,hb) scan.new_events(c,cursor) '
              "nom['size_lamports'] nom['created_ns']\n"
              'for nom in old351.keep_latest(entries): pass\n')
    class Tests(unittest.TestCase):
        def test_broken_future(self):
            with self.assertRaises(SyntaxError): compile(broken, "broken.py", "exec")
        def test_repaired_parses(self): compile(repair(broken), "fixed.py", "exec")
        def test_future_first(self):
            self.assertTrue(repair(broken).startswith('from __future__ import annotations\n'+IMPORT))
        def test_guard_once(self): self.assertEqual(repair(broken).count(IMPORT), 1)
        def test_loop_replaced(self): self.assertIn(NEW_LOOP,repair(broken))
        def test_idempotent(self): self.assertEqual(repair(repair(broken)),repair(broken))
        def test_duplicate_import_stop(self):
            with self.assertRaisesRegex(RuntimeError,'DUPLICATE'):
                repair(broken+IMPORT+'\n')
        def test_unknown_source_stop(self):
            with self.assertRaisesRegex(RuntimeError,'BUS_LOOP'):
                repair('from __future__ import annotations\n')
        def test_future_missing_stop(self):
            with self.assertRaisesRegex(RuntimeError,'FUTURE_HEADER'):
                repair(broken.replace('from __future__ import annotations',''))
        def test_guard_compiles(self): ast.parse(guard_source())
        def test_no_network_signing(self):
            self.assertNotIn('sendTransaction',GUARD_SOURCE)
            self.assertNotIn('websockets',GUARD_SOURCE)
    r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not r.wasSuccessful(): return 1
    print('[ORACLE358_TEST_PASS]',r.testsRun)
    return 0


def main():
    p=argparse.ArgumentParser()
    for mode in ('test','install','audit'): p.add_argument('--'+mode, action='store_true')
    a=p.parse_args()
    if not (a.test or a.install or a.audit): p.error('SELECT_MODE')
    if a.test and test(): return 1
    if a.install: install()
    if a.audit: audit()
    return 0

if __name__=='__main__': sys.exit(main())
