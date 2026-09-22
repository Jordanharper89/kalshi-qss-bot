import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_153_bitcoin_blockstream_chain_tip_block_acquisition as m
class T(unittest.TestCase):
    def test_mapping(self):
        def text(url,timeout):
            if url.endswith("/height"): return "900000"
            if url.endswith("/hash"): return "abc"
            raise AssertionError(url)
        block={"id":"abc","height":900000,"timestamp":1787970000,"tx_count":3000,"size":1500000,"weight":3990000,"merkle_root":"mr","previousblockhash":"prev","difficulty":100}
        with patch.object(m,"_get_text",side_effect=text),patch.object(m,"_get_json",return_value=block):
            r=m.acquire_bitcoin_blockstream_chain_observations()
        print("[OBSERVATIONS]",len(r)); print("[TIP_HEIGHT]",r[0].payload["height"]); print("[TX_COUNT]",r[1].payload["tx_count"])
        self.assertEqual(len(r),2); self.assertEqual(r[1].payload["tx_count"],3000)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-153 Bitcoin Blockstream chain-tip/block acquisition certified")
