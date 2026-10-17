import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_055_parity_simulation_guard as m
class Tests(unittest.TestCase):
    def good(self):
        return {'size_sol':.010,'direction':'METEORA_TO_PUMP','venue_order':['METEORA','PUMPSWAP'],
                'source_fresh':True,'accounts_reconciled':True,'sim_err':None,'sim_units':1000,
                'fees_complete':True,'residue_raw':0,'net_lamports':100,'atomic_two_legs':True,
                'state_parity_verified':True}
    def row(self):
        return {'token':'t','direction':'METEORA_TO_PUMP','size_sol':.010,'pump_pool':'p',
                'meteora_pool':'m','bps':99,'state_sha256':'a'}
    def test_01_source_lock(self): self.assertTrue(m.unchanged_source())
    def test_02_child_seconds_integer(self): self.assertEqual(m.child_argv(86400)[3],'86400')
    def test_03_fractional_child_rejected(self):
        with self.assertRaises(ValueError): m.child_argv(86400.0)
    def test_04_child_one_scanner(self): self.assertEqual(m.child_argv(86400)[-2:],['--cycles','1'])
    def test_05_state_hash_reproducible(self):
        s=dict(token='t',pump_pool='p',pump_base_reserve=3,pump_quote_reserve=4,
               meteora={'address':'m'},lb_bytes=b'a',arrays_raw=((1,2,b'b'),))
        self.assertEqual(m.state_digest(s),m.state_digest(dict(reversed(list(s.items())))))
    def test_06_missing_state_unknown(self): self.assertIsNone(m.state_digest({'token':'t'}))
    def test_07_state_change(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,state_sha256='b')),'STATE_CHANGED_NOT_PRICE_PARITY_PROOF')
    def test_08_same_state_divergence(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,bps=-10)),'SAME_STATE_PRICE_DIVERGENCE')
    def test_09_same_state_parity(self):
        a=self.row();self.assertEqual(m.compare_quote(a,dict(a,bps=99.01)),'SAME_STATE_PRICER_PARITY')
    def test_10_minimum_canary(self):
        r=self.good();r['size_sol']=.005;self.assertEqual(m.atomic_gate(r),'HOLD_BELOW_010_CANARY_MINIMUM')
    def test_11_reverse_order(self):
        r=self.good();r['venue_order']=['PUMPSWAP','METEORA'];self.assertEqual(m.atomic_gate(r),'HOLD_REVERSED_NATIVE_LEG_ORDER')
    def test_12_sim_rejected(self):
        r=self.good();r['sim_units']=0;r['sim_err']={'InstructionError':[0,1]}
        self.assertEqual(m.atomic_gate(r),'HOLD_FAILED_ATOMIC_SIMULATION')
    def test_13_fee_and_residue(self):
        r=self.good();r['residue_raw']=1;self.assertEqual(m.atomic_gate(r),'HOLD_INTERMEDIATE_TOKEN_RESIDUE')
        r=self.good();r['fees_complete']=False;self.assertEqual(m.atomic_gate(r),'HOLD_INCOMPLETE_ATOMIC_PROOF')
    def test_14_unsigned_only(self):
        self.assertEqual(m.atomic_gate(self.good()),'UNSIGNED_SIMULATION_EVIDENCE_ONLY_NO_BROADCAST')
        self.assertFalse(m.EXECUTION_AUTHORITY or m.BROADCAST or m.SIGNING)
    def test_15_redaction(self): self.assertNotIn('SUPERSECRET',m.safe('https://x/?api-key=SUPERSECRET'))
    def test_16_sim_envelope(self):
        self.assertFalse(m.simulation_diagnostic({'value':{'err':'InstructionError','unitsConsumed':0}})['verified'])
    def test_17_source_drift(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_text('changed');self.assertFalse(m.unchanged_source(p,'deadbeef'))
    def test_18_no_evidence(self): self.assertTrue(m.atomic_gate({}).startswith('HOLD_MISSING_'))
if __name__=='__main__': unittest.main(verbosity=2)
