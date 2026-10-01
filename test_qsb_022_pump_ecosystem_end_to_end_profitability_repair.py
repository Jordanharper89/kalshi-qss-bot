
import json,os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena,TARGET,TRADE_PATHS

class T(unittest.TestCase):
    def arena(self,td):
        return ChampionChallengerArena(Path(td)/"workspace",physical_root=Path(td),start_worker=False)

    def write(self,root,rel,obj):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj),encoding="utf-8")

    def test_join_pumpfun_and_pumpswap_exact_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);now=time.time()
            fun=[]
            for i in range(5):
                fun.append({"venue":"PUMP_FUN","token_address":"Tfun","market_address":"Mfun",
                    "effective_price":1+i*.02,"observed_unix":now-5+i,"side":"BUY" if i>=1 else "SELL",
                    "quote_amount":2+i,"trader":"WF"+str(i),"trade_id":"F"+str(i)})
            swap=[]
            for i in range(5):
                swap.append({"venue":"PUMP_SWAP","token_address":"Tswap","market_address":"Mswap",
                    "effective_price":2+i*.03,"observed_unix":now-5+i,"side":"BUY" if i>=1 else "SELL",
                    "quote_amount":3+i,"trader":"WS"+str(i),"trade_id":"S"+str(i)})
            self.write(root,"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json",{"rows":fun})
            self.write(root,"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json",{"rows":swap})
            a=self.arena(td);rows,counts=a._ecosystem_rows()
            self.assertEqual(len(rows),10)
            self.assertEqual({x["family"] for x in rows},{"PUMP_FUN","PUMP_SWAP"})
            self.assertGreaterEqual(len(counts),2)

    def test_exact_signal_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);now=time.time();rows=[]
            for i in range(7):
                rows.append({"venue":"PUMP_FUN","token_address":"T","market_address":"M",
                    "effective_price":1+i*.015,"observed_unix":now-7+i,"side":"BUY" if i>=1 else "SELL",
                    "quote_amount":5+i*3,"trader":"W"+str(i),"trade_id":"X"+str(i)})
            self.write(root,"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json",{"rows":rows})
            a=self.arena(td);eco,_=a._ecosystem_rows();s=a._exact_signals(eco,{}, {})
            self.assertGreaterEqual(len(s),1)
            self.assertEqual(s[0]["source_file"],"QSB022_JOINED_PUMP_ECOSYSTEM")

    def test_source_disconnect_truth(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.arena(td)
            c=a._coverage([],{},0,{"PUMP_FUN":3})
            self.assertTrue(c["source_disconnect"])
            self.assertFalse(c["source_connected"])

    def test_independent_book_not_blocked_by_other_strategies(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.arena(td)
            a.positions={"positions":[{"status":"OPEN","strategy":"OTHER","token":"X"+str(i)} for i in range(12)]}
            s={"strategy":TARGET,"market":"M","token":"T","family":"PUMP_FUN","price":1.0,"score":.9,
               "base_score":.9,"flow3":.8,"flow8":.75,"pressure_accel":2.0,"unique_buyers8":5,
               "largest_buyer_share":.25,"sell_ratio8":.2,"momentum8":.05,
               "birth_age_seconds":12,"wallet_quality":.5,"early_buyers":["W1","W2"]}
            a._enter_pump(s)
            self.assertEqual(len(a._pump_open()),1)
            self.assertEqual(len(a._open()),12)

    def test_winner_learning_and_wallet_memory(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.arena(td)
            base={"flow3":.8,"flow8":.76,"pressure_accel":2.2,"unique_buyers8":6,
                  "largest_buyer_share":.25,"sell_ratio8":.18,"momentum8":.05,
                  "birth_age_seconds":20,"wallet_quality":.6,"base_score":.8,
                  "early_buyers":["WA","WB"]}
            losses={"flow3":.55,"flow8":.53,"pressure_accel":.8,"unique_buyers8":2,
                    "largest_buyer_share":.75,"sell_ratio8":.45,"momentum8":-.005,
                    "birth_age_seconds":150,"wallet_quality":.4,"base_score":.5,
                    "early_buyers":["WL"]}
            a.pump_ledger={"trades":[{"net_pnl_usdc":.5,"mfe":.18,"mae":-.02,"signal":base} for _ in range(6)]
                          +[{"net_pnl_usdc":-.4,"mfe":.02,"mae":-.11,"signal":losses} for _ in range(2)]}
            L=a._learning();self.assertGreaterEqual(len(L["promoted"]),1)
            trade={"net_pnl_usdc":.7,"signal":{"early_buyers":["WA","WB"]}}
            a._update_wallet_learning(trade)
            self.assertEqual(a.wallet_learning["wallets"]["WA"]["wins"],1)

    def test_ten_win_positive_net_gate(self):
        with tempfile.TemporaryDirectory() as td:
            a=self.arena(td);a.pump_ledger={"trades":[{"net_pnl_usdc":.2,"signal":{}} for _ in range(10)]}
            s=a.stats()[TARGET]
            self.assertEqual(s["wins"],10);self.assertGreater(s["net"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
