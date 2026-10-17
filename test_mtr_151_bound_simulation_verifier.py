import hashlib
import unittest
from dataclasses import replace
from decimal import Decimal
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_147_protected_economics_gate import ProtectedEvidence
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_151_bound_simulation_verifier import evaluate_bound

RAW = b'unit-test-only-unsigned-transaction'
DIGEST = hashlib.sha256(RAW).hexdigest()
BASE = ProtectedEvidence('r', 'PUMP_TO_METEORA', Decimal('0.010'), 9,
                         10000000, 10100000, 5000, 1000, 1000,
                         True, True, True, DIGEST)
SIM = {'err': None, 'units': 120000, 'logs': []}

def native(raw):
    assert raw == RAW
    return dict(route_id='r', direction='PUMP_TO_METEORA',
                size_sol=Decimal('0.010'), generation=9,
                atomic_two_leg=True, pump_bounds=True, dlmm_bounds=True,
                unsigned_simulation_only=True)

def economics(raw, tx, sim):
    return {k: getattr(BASE, k) for k in ('input_lamports',
         'minimum_final_lamports', 'network_fee_lamports',
         'priority_fee_lamports', 'rent_and_residue_lamports')}

def go(e=BASE, raw=RAW, sim=SIM, inspector=native, econ=economics):
    return evaluate_bound({'raw': raw}, sim, e, route_id='r', generation=9,
                          inspect_compiled=inspector, inspect_economics=econ)

class Tests(unittest.TestCase):
    def test_missing_native_inspector_holds(self):
        self.assertEqual(go(inspector=None)['status'], 'HOLD')
    def test_simulation_error_holds(self):
        self.assertEqual(go(sim={'err': {'InstructionError': [0, 'Failed']}, 'units': 3})['status'], 'HOLD')
    def test_missing_units_holds(self):
        self.assertEqual(go(sim={'err': None})['status'], 'HOLD')
    def test_digest_mismatch_holds(self):
        self.assertEqual(go(e=replace(BASE, verifier_receipt='wrong'))['status'], 'HOLD')
    def test_swapped_route_holds(self):
        self.assertEqual(go(e=replace(BASE, route_id='other'))['status'], 'HOLD')
    def test_wrong_economics_holds(self):
        def bad(*args):
            return dict(economics(*args), minimum_final_lamports=9900000)
        self.assertEqual(go(econ=bad)['status'], 'HOLD')
    def test_native_inspector_cannot_claim_one_leg(self):
        def one_leg(raw):
            return dict(native(raw), atomic_two_leg=False)
        self.assertEqual(go(inspector=one_leg)['status'], 'HOLD')
    def test_fixture_positive_not_execution(self):
        r = go()
        self.assertEqual(r['status'], 'REVALIDATION_CANDIDATE')
        self.assertEqual(r['net_lamports'], 93000)
        self.assertFalse(r['signing_authorized'])
        self.assertFalse(r['broadcast_authorized'])
    def test_not_profitable_holds(self):
        low = replace(BASE, minimum_final_lamports=10000000)
        def econ_low(*args):
            return dict(economics(*args), minimum_final_lamports=10000000)
        self.assertEqual(go(e=low, econ=econ_low)['reason'], 'NOT_PROTECTED_POSITIVE')

if __name__ == '__main__':
    unittest.main(verbosity=2)
