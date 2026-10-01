
import json,os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena,TARGET

class T(unittest.TestCase):
    def _arena(self,td):
        return ChampionChallengerArena(Path(td)/"workspace",physical_root=Path(td))

    def test_exact_pump_signal_and_nonpump_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"
            p.parent.mkdir(parents=True)
            now=time.time()
            rows=[]
            for i in range(8):
                rows.append({"token_address":"T","market_address":"M","effective_price":1+i*.01,
                    "observed_unix":now-8+i,"side":"BUY" if i>=2 else "SELL",
                    "quote_amount":10+i*5,"trader":"W"+str(i),"birth_age_seconds":20+i})
            p.write_text(json.dumps({"rows":rows}),encoding="utf-8")
            a=self._arena(td);sig=a._exact_signals()
            self.assertGreaterEqual(len(sig),1)
            self.assertEqual(sig[0]["strategy"],TARGET)
            self.assertEqual(sig[0]["family"],"PUMP_FUN")
            self.assertGreater(sig[0]["unique_buyers10"],1)

    def test_independent_book_not_blocked_by_legacy_open(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            a.positions={"positions":[{"status":"OPEN","strategy":"OTHER","token":"X"+str(i)} for i in range(7)]}
            s={"strategy":TARGET,"market":"M","token":"T","family":"PUMP_FUN","price":1.0,"score":.9,
               "base_score":.9,"flow5":.8,"pressure_accel":2.0,"unique_buyers10":5,
               "sell_ratio10":.2,"momentum10":.05,"birth_age_seconds":20}
            a._enter_pump(s)
            self.assertEqual(len(a._pump_open()),1)
            self.assertEqual(len(a._open()),7)

    def test_winner_loser_learning_changes_gate(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            trades=[]
            for i in range(6):
                trades.append({"net_pnl_usdc":1.0,"mfe":.20,"mae":-.03,"signal":{
                    "flow5":.82,"pressure_accel":2.5,"unique_buyers10":7,"sell_ratio10":.18,
                    "momentum10":.06,"birth_age_seconds":25,"base_score":.85}})
            for i in range(2):
                trades.append({"net_pnl_usdc":-.5,"mfe":.03,"mae":-.12,"signal":{
                    "flow5":.58,"pressure_accel":.9,"unique_buyers10":2,"sell_ratio10":.48,
                    "momentum10":.005,"birth_age_seconds":160,"base_score":.55}})
            a.pump_ledger={"trades":trades}
            L=a._learning()
            self.assertGreaterEqual(len(L["promoted"]),1)
            self.assertLessEqual(L["admission_score"],a.base_admission)
            winner_like={"base_score":.70,"flow5":.84,"pressure_accel":2.8,"unique_buyers10":8,
                         "sell_ratio10":.15,"momentum10":.07,"birth_age_seconds":20}
            self.assertGreater(a._adaptive_score(winner_like,L),.70)

    def test_ten_win_positive_net_milestone_math(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            a.pump_ledger={"trades":[{"net_pnl_usdc":.25,"signal":{}} for _ in range(10)]}
            s=a.stats()[TARGET]
            self.assertEqual(s["wins"],10)
            self.assertGreater(s["net"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
