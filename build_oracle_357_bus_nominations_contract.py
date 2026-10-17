from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_352_scanner_bank_alignment.py'
GUARD = ROOT / 'oracle_357_bus_contract.py'
ANCHOR = 'for nom in old351.keep_latest(entries):'
REPLACEMENT = 'for nom in oracle357.keep_latest_valid(entries, counts):'
IMPORT = 'from qseries_v2.oracle_execution.solana_atomic_executor import oracle_357_bus_contract as oracle357\n'
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

def sha(data): return hashlib.sha256(data.encode('utf-8')).hexdigest()

def modified(original):
    if REPLACEMENT in original and IMPORT in original:
        return original
    if original.count(ANCHOR) != 1:
        raise RuntimeError('ORACLE357_ANCHOR_NOT_UNIQUE_STOP')
    if 'def main():' not in original or 'identity.vetted(nom,inv,hb)' not in original:
        raise RuntimeError('ORACLE357_UPSTREAM_CONTRACT_MISMATCH_STOP')
    if not all(k in original for k in ("nom['size_lamports']", "nom['created_ns']", 'scan.new_events(c,cursor)')):
        raise RuntimeError('ORACLE357_FRESHNESS_GATE_NOT_VERIFIED_STOP')
    base = original.replace(ANCHOR, REPLACEMENT, 1)
    if base.startswith('from __future__ import annotations\n'):
        output = base.replace('from __future__ import annotations\n', 'from __future__ import annotations\n'+IMPORT, 1)
    else:
        output = IMPORT + base
    ast.parse(output)
    return output

def install():
    if not TARGET.is_file():
        raise RuntimeError('ORACLE352_MISSING_STOP')
    before = TARGET.read_text(encoding='utf-8')
    after = modified(before)
    ast.parse(GUARD_SOURCE)
    # Only write after all source contracts are verified.
    if after != before:
        backup = TARGET.with_name('oracle_352_scanner_bank_alignment.oracle357_backup.py')
        if backup.exists() and backup.read_text(encoding='utf-8') != before:
            raise RuntimeError('BACKUP_CONFLICT_STOP')
        if not backup.exists(): backup.write_text(before, encoding='utf-8')
    GUARD.write_text(GUARD_SOURCE, encoding='utf-8')
    TARGET.write_text(after, encoding='utf-8')
    if TARGET.read_text(encoding='utf-8') != after:
        raise RuntimeError('WRITE_VERIFICATION_FAILED')
    print('[ORACLE357_INSTALL_PASS]', TARGET, 'source_sha256='+sha(after), 'guard_sha256='+sha(GUARD_SOURCE))
    print('[SCOPE] ORACLE322_FROZEN ORACLE352_BUS_VALIDATION_ONLY CANARY_010_ONLY NO_NEW_RPC_WS NO_SIGN_NO_BROADCAST')

def test():
    namespace={}
    exec(compile(GUARD_SOURCE,'oracle_357_bus_contract.py','exec'),namespace)
    validate=namespace['keep_latest_valid']
    row={'id':11,'token':'tokA','pump_pool':'pA','meteora_pool':'mA','direction':'PUMP_TO_METEORA','size_lamports':10_000_000,'created_ns':1234567}
    def check(rows):
        c={}
        # regular dict inadequate for accumulation, pass Counter
        from collections import Counter
        cnt=Counter()
        return validate(rows,cnt),cnt
    class Tests(unittest.TestCase):
        def test_valid(self): self.assertEqual(check([row])[0][0]['id'],11)
        def test_wrong_type(self): self.assertEqual(check(['x',None,(),1])[1]['bus_contract_NON_MAPPING'],4)
        def test_missing(self): self.assertEqual(check([{'id':1}])[1]['bus_contract_MISSING_FIELDS'],1)
        def test_bad_batch(self): self.assertEqual(check({'events':[row]})[1]['bus_contract_bad_batch'],1)
        def test_canonical_id(self): self.assertEqual(check([dict(row,id='11')])[0][0]['id'],'11')
        def test_float_reject(self): self.assertEqual(len(check([dict(row,id=11.0)])[0]),0)
        def test_bool_reject(self): self.assertEqual(len(check([dict(row,id=True)])[0]),0)
        def test_bounds(self): self.assertEqual(len(check([dict(row,size_lamports=9_999_999)])[0]),0)
        def test_maxsize(self): self.assertEqual(len(check([dict(row,size_lamports=100_000_000)])[0]),1)
        def test_direction(self): self.assertEqual(len(check([dict(row,direction='BOGUS')])[0]),0)
        def test_pool(self): self.assertEqual(len(check([dict(row,pump_pool='')])[0]),0)
        def test_created(self): self.assertEqual(len(check([dict(row,created_ns=-4)])[0]),0)
        def test_supersession(self):
            out,c=check([row,dict(row,id=12),dict(row,id=10)])
            self.assertEqual(out[0]['id'],12)
            self.assertEqual(c['bus_contract_superseded'],2)
        def test_distinct_size(self): self.assertEqual(len(check([row,dict(row,id=12,size_lamports=20_000_000)])[0]),2)
        def test_preserve_admission(self):
            s='def main():\n    pass\n# identity.vetted(nom,inv,hb)\n# scan.new_events(c,cursor)\n# nom[\'size_lamports\'] nom[\'created_ns\']\nfor nom in old351.keep_latest(entries):\n    pass\n'
            self.assertIn('identity.vetted(nom,inv,hb)',modified(s))
            self.assertIn(REPLACEMENT,modified(s))
        def test_idempotent(self):
            s='def main():\n    pass\n# identity.vetted(nom,inv,hb)\n# scan.new_events(c,cursor)\n# nom[\'size_lamports\'] nom[\'created_ns\']\nfor nom in old351.keep_latest(entries):\n    pass\n'
            self.assertEqual(modified(modified(s)),modified(s))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful(): return 1
    print('[ORACLE357_TEST_PASS]',result.testsRun)
    return 0

def audit():
    if not GUARD.exists() or not TARGET.exists():
        raise RuntimeError('INSTALL_FIRST')
    src=TARGET.read_text(encoding='utf-8')
    if REPLACEMENT not in src or IMPORT not in src or src.count(REPLACEMENT)!=1 or ANCHOR in src:
        raise RuntimeError('NOT_INTEGRATED')
    if GUARD.read_text(encoding='utf-8') != GUARD_SOURCE:
        raise RuntimeError('GUARD_SOURCE_CHANGED')
    if not all(k in src for k in ('identity.vetted(nom,inv,hb)',"nom['size_lamports']",'SCANNER_EPOCH_CHANGED_DURING_SETUP')):
        raise RuntimeError('ADMISSION_OR_EPOCH_GATE_MISSING')
    print('[ORACLE357_AUDIT_PASS] SCANNER322_FROZEN NO_NEW_RPC_WS SIZE_CAPPED_AT_010_BY_ORACLE352 NO_SIGN_NO_BROADCAST')

def main():
    p=argparse.ArgumentParser()
    for flag in ('install','test','audit'): p.add_argument('--'+flag, action='store_true')
    a=p.parse_args()
    if not any((a.install,a.test,a.audit)): p.error('SELECT_MODE')
    if a.test and test(): return 1
    if a.install: install()
    if a.audit: audit()
    return 0

if __name__=='__main__': sys.exit(main())
