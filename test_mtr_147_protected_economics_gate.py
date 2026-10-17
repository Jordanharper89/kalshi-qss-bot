import unittest
from decimal import Decimal
from dataclasses import replace
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_147_protected_economics_gate import ProtectedEvidence, ProtectedCandidateGate

class Tests(unittest.TestCase):
    def setUp(self):
        self.e=ProtectedEvidence('r','METEORA_TO_PUMP',Decimal('0.010'),7,
              10000000,10100000,5000,1000,1000,True,True,True,'sdk-atomic-proof')
    def go(self,e=None, verifier=None):
        return ProtectedCandidateGate(verifier).evaluate(e if e is not None else self.e,
                    expected_route='r', expected_generation=7)
    def test_indicative_numbers_not_promoted(self):
        self.assertEqual(self.go({'local_bps':500})['status'],'HOLD')
    def test_default_fail_closed(self):
        self.assertEqual(self.go()['reason'],'TRUSTED_OFFICIAL_VERIFIER_MISSING')
    def test_untrusted_verifier_refuses(self):
        self.assertEqual(self.go(verifier=lambda e: False)['status'],'HOLD')
    def test_verified_positive_is_only_revalidation_candidate(self):
        r=self.go(verifier=lambda e: True)
        self.assertEqual(r['status'],'REVALIDATION_CANDIDATE')
        self.assertEqual(r['net_lamports'],93000)
        self.assertFalse(r['signing_authorized'])
        self.assertFalse(r['broadcast_authorized'])
    def test_bounds_or_atomic_missing(self):
        for key in ('pump_bounds_checked','dlmm_bounds_checked','atomic_two_leg_verified'):
            with self.subTest(key=key):
                self.assertEqual(self.go(replace(self.e,**{key:False}),lambda e: True)['status'],'HOLD')
    def test_wrong_route_generation_size(self):
        for key,value in (('route_id','r2'),('generation',8),('size_sol',Decimal('0.001'))):
            with self.subTest(key=key):
                self.assertEqual(self.go(replace(self.e,**{key:value}),lambda e: True)['status'],'HOLD')
    def test_worst_case_costs_control_positive(self):
        e=replace(self.e,minimum_final_lamports=10001000)
        self.assertEqual(self.go(e,lambda e: True)['reason'],'NOT_PROTECTED_POSITIVE')
    def test_verifier_exceptions_fail_closed(self):
        def fail(e): raise RuntimeError('not verified')
        self.assertEqual(self.go(verifier=fail)['reason'],'VERIFIER_ERROR')

if __name__=='__main__':
    unittest.main(verbosity=2)
