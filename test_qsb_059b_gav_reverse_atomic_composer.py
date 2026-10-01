import base64,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q

class T(unittest.TestCase):
    def test_reverse_ix_direction_token_x_is_wsol(self):
        c=q.c
        old={k:getattr(c,k) for k in ("account","ata","pda","dlmm_arrays")}
        c.account=lambda a:(b"x","TP")
        c.ata=lambda owner,mint,tp:"ATA_"+mint
        c.pda=lambda seeds,program:"PDA"
        c.dlmm_arrays=lambda pool:[(1,"BIN1",b"x"),(2,"BIN2",b"x"),(3,"BIN3",b"x")]
        try:
            meta={"address":"11111111111111111111111111111111","token_x":c.WSOL,"token_y":c.DLMM}
            ix=q.dlmm_reverse_ix("USER",meta,123,{"raw_out":456,"swap_for_y":False,"bins_crossed":1})
            ac=[x["pubkey"] for x in ix["accounts"]]
            self.assertEqual(ac[4],"ATA_"+c.DLMM)
            self.assertEqual(ac[5],"ATA_"+c.WSOL)
        finally:
            for k,v in old.items():setattr(c,k,v)
        print("[PASS] reverse DLMM instruction sources TOKEN and receives WSOL")

    def test_atomic_order_pump_then_meteora(self):
        c=q.c
        old={k:getattr(c,k) for k in ("discover_dlmm","pump_tx","dlmm_quote","resolve_pump_instructions")}
        old_ix=q.dlmm_reverse_ix
        c.discover_dlmm=lambda token:{"address":"M","token_x":c.WSOL,"token_y":token}
        c.pump_tx=lambda user,i,o,a:("TX",1000)
        c.dlmm_quote=lambda meta,a,m:{"raw_out":1100,"swap_for_y":False,"bins_crossed":1}
        c.resolve_pump_instructions=lambda tx:([
          {"programId":"PRE","accounts":[],"data":""},
          {"programId":c.PUMP,"accounts":[],"data":""},
          {"programId":"POST","accounts":[],"data":""},
        ],[])
        q.dlmm_reverse_ix=lambda *a,**k:{"programId":c.DLMM,"accounts":[],"data":""}
        try:
            x=q.compose_reverse_atomic("U","T","P","M",0.000001)
            programs=[i["programId"] for i in x["instructions"]]
            self.assertEqual(programs,["PRE",c.PUMP,c.DLMM,"POST"])
            self.assertGreater(x["pre_sim_net_lamports"],0)
        finally:
            for k,v in old.items():setattr(c,k,v)
            q.dlmm_reverse_ix=old_ix
        print("[PASS] atomic route order is PumpSwap BUY then Meteora SELL")

    def test_no_broadcast(self):
        src=open(q.__file__,encoding="utf-8").read()
        self.assertNotIn("send(raw)",src)
        self.assertNotIn("LIVE_BUY_SELL",src)
        print("[PASS] QSB-059 cannot broadcast; exact simulation only")

if __name__=="__main__":
    unittest.main(verbosity=2)
