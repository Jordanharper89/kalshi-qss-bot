from __future__ import annotations
import argparse,ast,hashlib,json,re,unittest
from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
SOURCE=PKG/'oracle_051_original_scanner_alt_and_size_gate.py'
BRIDGE=PKG/'oracle_054_reverse_native_handoff.py'
REPORT=ROOT/'runtime_state/oracle/oracle_live_execution/oracle_059_compiler_truth.json'

def contracts():
    s=SOURCE.read_text(encoding='utf-8')
    b=BRIDGE.read_text(encoding='utf-8')
    ast.parse(s);ast.parse(b)
    return {
      'compiler_has_venue_leg_check':'programs.count(core.PUMP) != 1 or programs.count(core.DLMM) != 1' in s,
      'compiler_has_size_guard':'len(raw) > LIMIT' in s,
      'compiler_has_unsigned_guard':'raw[1:65] != bytes(64)' in s,
      'compiler_has_v0_guard':'raw[65] != 128' in s,
      'compiler_has_010_floor':'MIN_LAMPORTS = 10_000_000' in s,
      'compiler_has_full_failure_detail':'ORACLE059_NATIVE_COMPILE_TRUTH' in s,
      'bridge_has_reverse_native_route':'native_reverse_route(' in b,
      'bridge_has_session_lifetime_gate':'if self.native_compiles or self.unsigned_simulations:' in b,
      'compiler_source_sha256':hashlib.sha256(s.encode()).hexdigest()[:16],
      'bridge_source_sha256':hashlib.sha256(b.encode()).hexdigest()[:16]
    }

def classify(attempts):
    reasons=[]
    for a in attempts:
        if not isinstance(a,dict):continue
        error=str(a.get('error') or '')
        detail=str(a.get('detail') or '')
        alt=str(a.get('alt_check') or '')
        if 'TOO_LARGE' in (error+detail) or 'NONCANONICAL_UNSIGNED_V0_PACKET' in detail:
            reasons.append('SIZE_OR_PACKET')
        elif 'LOOKUP' in (alt+error+detail) or 'ALT_' in (alt+error+detail):
            reasons.append('ALT_OR_ACCOUNT_COVERAGE')
        elif 'VENUE_LEG' in (error+detail):
            reasons.append('MISSING_VENUE_LEG')
        elif error or detail:
            reasons.append('NATIVE_BUILDER_ERROR')
    return sorted(set(reasons)) or ['NO_ATTEMPT_EVIDENCE']

def audit():
    c=contracts()
    missing=[k for k,v in c.items() if k.startswith('compiler_has_') and not v]
    output={'build':'ORACLE-059','mode':'OFFLINE_NATIVE_COMPILER_CONTRACT',
            'contracts':c,'holds':missing,
            'next_compiler_evidence':'ORACLE059_COMPILE_ATTEMPT printed by live existing compile hook',
            'scanner_started':False,'rpc_calls':0,'signing':False,'broadcast':False,
            'profitable_atomic_simulation':False,'realized_pnl_lamports':0}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(output,indent=2,sort_keys=True),encoding='utf-8')
    for k,v in c.items():print('[ORACLE059_CONTRACT]',k,v)
    print('[REPORT]',REPORT)
    print('[MONEY] compile truth installed; no atomic simulation or live profit certified')
    return 1 if missing else 0

class Tests(unittest.TestCase):
    def test_contracts(self):
        self.assertTrue(all(v for k,v in contracts().items() if k.startswith('compiler_has_')))
    def test_size(self):self.assertEqual(classify([{'error':'ATOMIC_TX_TOO_LARGE:1400'}]),['SIZE_OR_PACKET'])
    def test_alt(self):self.assertEqual(classify([{'alt_check':'ALT_INSUFFICIENT_INSTRUCTION_COVERAGE'}]),['ALT_OR_ACCOUNT_COVERAGE'])
    def test_venue(self):self.assertEqual(classify([{'error':'HOLD_MISSING_OR_DUPLICATE_VENUE_LEG'}]),['MISSING_VENUE_LEG'])
    def test_other(self):self.assertEqual(classify([{'error':'RuntimeError','detail':'InvalidAccountData'}]),['NATIVE_BUILDER_ERROR'])
    def test_empty(self):self.assertEqual(classify([]),['NO_ATTEMPT_EVIDENCE'])
    def test_no_rpc_or_signer(self):
        self.assertNotIn('simulateTransaction',audit.__code__.co_names)
        self.assertNotIn('sendTransaction',audit.__code__.co_names)

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.test:
        r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if r.wasSuccessful() else 1
    if a.audit:return audit()
    p.print_help();return 0
if __name__=='__main__':raise SystemExit(main())
