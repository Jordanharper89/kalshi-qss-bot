import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_162_native_instruction_producer_contract as m
class Tests(unittest.TestCase):
    def test_sources_present(self):
        for path in m.SOURCES.values():self.assertTrue((m.ROOT/path).is_file(),path)
    def test_real_core_builders(self):
        names={f['name'] for f in m.inspect(m.ROOT/m.SOURCES['native_core'])}
        self.assertTrue({'merge_native','dlmm_ix','compile_v0'}.issubset(names),names)
    def test_signer_boundary_visible(self):
        names={f['name'] for f in m.inspect(m.ROOT/m.SOURCES['native_core'])}
        self.assertIn('signed_tx',names)
    def test_no_execution_claim(self):
        r=m.run()
        for key in ('instructions_produced','scanner_modified','private_key_used','signing','broadcast'):
            self.assertFalse(r[key],key)
if __name__=='__main__':unittest.main(verbosity=2)
