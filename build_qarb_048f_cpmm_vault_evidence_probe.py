from pathlib import Path

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

M=S/"qarb_048f_cpmm_vault_evidence_probe.py"
T=R/"test_qarb_048f_cpmm_vault_evidence_probe.py"
U=R/"run_qarb_048f_cpmm_vault_evidence_probe.py"

M.write_text(r'''from pathlib import Path
import json

P=Path("runtime_state/solana_opportunities/universal_trade_tape")
POOLS=P/"raydium_exact_instruction_pool_roles.json"
ORIENT=P/"raydium_exact_pair_orientation.json"

def rows(x):
    if isinstance(x,list): return x
    for k in ("rows","swaps","records"):
        if isinstance(x.get(k),list): return x[k]
    return []

def pk(x):
    return x if isinstance(x,str) else x.get("pubkey") if isinstance(x,dict) else None

def main():
    rr=rows(json.loads(POOLS.read_text(encoding="utf-8")))
    oo=rows(json.loads(ORIENT.read_text(encoding="utf-8")))
    om={x.get("pool"):x for x in oo if x.get("venue")=="RAYDIUM_CPMM"}

    for r in rr:
        if r.get("venue")!="RAYDIUM_CPMM": continue
        print("\n[POOL]",r.get("pool"))
        o=om.get(r.get("pool"))
        print("[ORIENTATION]",None if not o else {
            "input_mint":o.get("input_mint"),
            "output_mint":o.get("output_mint"),
            "token_address":o.get("token_address"),
            "quote_mint":o.get("quote_mint"),
            "decoder_state":o.get("decoder_state")})

        tx=r.get("transaction") or {}
        keys=[pk(x) for x in (((tx.get("transaction") or {}).get("message") or {}).get("accountKeys") or [])]
        inst=[pk(x) for x in (r.get("accounts") or [])]
        print("[USER_SOURCE]",r.get("user_source_token_account"))
        print("[USER_DEST]",r.get("user_destination_token_account"))
        print("[INSTRUCTION_ACCOUNTS]",inst)

        meta=tx.get("meta") or {}
        bal={}
        for side in ("preTokenBalances","postTokenBalances"):
            for b in meta.get(side) or []:
                i=int(b["accountIndex"])
                x=bal.setdefault(i,{"mint":b.get("mint"),"owner":b.get("owner")})
                x[side]=((b.get("uiTokenAmount") or {}).get("amount"))
        for i,b in sorted(bal.items()):
            addr=keys[i] if i<len(keys) else None
            print("[TOKEN_ACCOUNT] idx=%d in_instruction=%s addr=%s mint=%s owner=%s pre=%s post=%s"%
                  (i,addr in inst,addr,b.get("mint"),b.get("owner"),
                   b.get("preTokenBalances"),b.get("postTokenBalances")))

    print("\n[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")

if __name__=="__main__": main()
''',encoding="utf-8")

T.write_text(r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048f_cpmm_vault_evidence_probe as q
class T(unittest.TestCase):
    def test_sources(self):
        self.assertIn("raydium_exact_instruction_pool_roles",str(q.POOLS))
        self.assertIn("raydium_exact_pair_orientation",str(q.ORIENT))
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

U.write_text(
"from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_048f_cpmm_vault_evidence_probe import main\n"
"if __name__=='__main__':main()\n",encoding="utf-8")

print("[PASS] QARB-048F CPMM vault evidence probe installed")
print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")