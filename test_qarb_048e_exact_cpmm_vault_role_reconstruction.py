import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048e_exact_cpmm_vault_role_reconstruction as q

def fixture():
    keys=["payer","POOL","VA","VB","USERA","USERB"]
    tx={"transaction":{"message":{"accountKeys":keys}},"meta":{
        "preTokenBalances":[
            {"accountIndex":2,"mint":"MA","uiTokenAmount":{"amount":"1000"}},
            {"accountIndex":3,"mint":"MB","uiTokenAmount":{"amount":"2000"}},
            {"accountIndex":4,"mint":"MA","uiTokenAmount":{"amount":"100"}},
            {"accountIndex":5,"mint":"MB","uiTokenAmount":{"amount":"200"}}],
        "postTokenBalances":[
            {"accountIndex":2,"mint":"MA","uiTokenAmount":{"amount":"1100"}},
            {"accountIndex":3,"mint":"MB","uiTokenAmount":{"amount":"1900"}},
            {"accountIndex":4,"mint":"MA","uiTokenAmount":{"amount":"0"}},
            {"accountIndex":5,"mint":"MB","uiTokenAmount":{"amount":"300"}}]}}
    role={"venue":"RAYDIUM_CPMM","pool":"POOL","signature":"SIG","pool_role_state":"EXACT",
          "accounts":["POOL","VA","VB","USERA","USERB"],
          "user_source_token_account":"USERA","user_destination_token_account":"USERB","transaction":tx}
    orient={("POOL","SIG"):("MA","MB",{"decoder_state":"EXACT_QUOTE_ORIENTED_SWAP"})}
    return role,orient

class T(unittest.TestCase):
    def test_exact_vault_reconstruction(self):
        role,orient=fixture();r,e=q.reconstruct(role,orient)
        self.assertIsNone(e);self.assertEqual(r["vault_a"],"VA");self.assertEqual(r["vault_b"],"VB")
    def test_ambiguous_fails_closed(self):
        role,orient=fixture();role["accounts"].append("VA2")
        role["transaction"]["transaction"]["message"]["accountKeys"].append("VA2")
        role["transaction"]["meta"]["preTokenBalances"].append({"accountIndex":6,"mint":"MA","uiTokenAmount":{"amount":"1"}})
        role["transaction"]["meta"]["postTokenBalances"].append({"accountIndex":6,"mint":"MA","uiTokenAmount":{"amount":"2"}})
        r,e=q.reconstruct(role,orient);self.assertIsNone(r);self.assertTrue(e.startswith("AMBIGUOUS_VAULTS"))
    def test_read_only(self):
        self.assertTrue(q.READ_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":unittest.main(verbosity=2)
