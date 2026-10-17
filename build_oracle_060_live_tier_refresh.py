
from pathlib import Path
import ast
import shutil
import tempfile
import unittest

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_050_original_scanner_executor_consolidation.py')
MARK = 'ORACLE060_BACKGROUND_TIER_REFRESH'
METHOD = '''    # ORACLE060_BACKGROUND_TIER_REFRESH: filesystem reads stay off pricing thread.
    def _oracle060_tier_refresh_loop(self):
        while not self.ingress_stop.wait(2.0):
            try:
                fresh = latest_tiers(self.root)
                if not isinstance(fresh, dict):
                    continue
                created = fresh.get("created_epoch")
                if not isinstance(created, (int, float)):
                    continue
                now = time.time()
                if created > now + 30 or now - created > 600:
                    continue
                old = self.tiers if isinstance(self.tiers, dict) else {}
                if created >= old.get("created_epoch", -1):
                    self.tiers = fresh
            except (OSError, ValueError, TypeError):
                continue

'''

def transform(source):
    if MARK in source:
        return source, False
    anchor = '    def start_ingress(self):\n'
    guard = '        if self.ingress_thread is not None:\n            raise RuntimeError("INGRESS_ALREADY_RUNNING")\n'
    if source.count(anchor) != 1 or source.count(guard) != 1:
        raise RuntimeError('HOLD_SOURCE_CONTRACT_CHANGED')
    for required in ('self.ingress_stop = threading.Event()', 'def tier_for(', 'def eligible_quote(', 'SCREENING_FEE_RESERVE = 100_000', 'MAX_AGE_NS = 750_000_000', '"PUMP_TO_METEORA", "METEORA_TO_PUMP"'):
        if required not in source:
            raise RuntimeError('HOLD_MISSING_SAFETY_CONTRACT: ' + required)
    source = source.replace(anchor, METHOD + anchor, 1)
    replacement = guard + '''        self._oracle060_tier_thread = threading.Thread(
            target=self._oracle060_tier_refresh_loop,
            name="oracle060-tier-refresh", daemon=True)
        self._oracle060_tier_thread.start()
'''
    source = source.replace(guard, replacement, 1)
    ast.parse(source)
    return source, True

class Tests(unittest.TestCase):
    def test_idempotent(self):
        s = TARGET.read_text(encoding='utf-8') if TARGET.exists() else ''
        if not s:
            self.skipTest('Target not available in test environment')
        out, changed = transform(s)
        self.assertEqual(transform(out), (out, False))
        self.assertIn(MARK, out)
        self.assertIn('self.ingress_stop.wait(2.0)', out)
        self.assertIn('daemon=True', out)
        self.assertIn('SCREENING_FEE_RESERVE = 100_000', out)
        self.assertIn('MAX_AGE_NS = 750_000_000', out)

    def test_no_trading_side_effects(self):
        self.assertNotIn('sendTransaction', METHOD)
        self.assertNotIn('QSB_SOLANA_PRIVATE_KEY', METHOD)
        self.assertNotIn('getAccountInfo', METHOD)

def main():
    if not TARGET.is_file():
        raise SystemExit('[HOLD] Original ORACLE-050 source missing; no files changed')
    original = TARGET.read_text(encoding='utf-8')
    patched, changed = transform(original)
    if not changed:
        print('[PASS] ORACLE-060 already installed; no changes')
    else:
        backup = TARGET.with_name(TARGET.stem + '.before_oracle060.py')
        if backup.exists():
            raise SystemExit('[HOLD] Backup already exists; refusing overwrite')
        shutil.copy2(TARGET, backup)
        try:
            TARGET.write_text(patched, encoding='utf-8')
            ast.parse(TARGET.read_text(encoding='utf-8'))
        except Exception:
            shutil.copy2(backup, TARGET)
            raise
        print('[BACKUP]', backup)
        print('[PASS] Background Mriya tier refresh installed')
    print('[BOUNDARY] No RPC, scanner, wallet, signing or broadcast during install')

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        main()
