from pathlib import Path

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

M=S/"qarb_048b_raydium_live_bridge_contract_capture.py"
T=R/"test_qarb_048b_raydium_live_bridge_contract_capture.py"
U=R/"run_qarb_048b_raydium_live_bridge_contract_capture.py"

M.write_text(r'''from __future__ import annotations
import importlib,inspect,json
from pathlib import Path

TARGETS=[
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_011_raydium_cpmm_live_binding",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_012_raydium_clmm_live_binding",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.merged_live_runtime",
]

def capture():
    out={}
    for name in TARGETS:
        print("[MODULE]",name)
        try:m=importlib.import_module(name)
        except Exception as e:
            print("[IMPORT_FAIL]",type(e).__name__,str(e));continue
        rows={}
        for n,o in vars(m).items():
            if inspect.isfunction(o) and o.__module__==m.__name__:
                try:sig=str(inspect.signature(o))
                except Exception:sig="?"
                rows[n]={"kind":"function","signature":sig}
                print("[FUNCTION]",n,sig)
            elif inspect.isclass(o) and o.__module__==m.__name__:
                rows[n]={"kind":"class"}
                print("[CLASS]",n)
        out[name]=rows
        for n in ("discover","hydrate","registry","update","quote","prepare","capability",
                  "_cpmm_ep","evaluate_token"):
            o=getattr(m,n,None)
            if callable(o):
                print("\\n[SOURCE]",name,n)
                try:print(inspect.getsource(o))
                except Exception as e:print("[SOURCE_FAIL]",repr(e))
    p=Path("runtime_state/qseries/qarb_clean_bot/raydium_live_bridge_contract_capture.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print("[REPORT]",p)
    print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")
    return out

def main():capture()

if __name__=="__main__":main()
''',encoding="utf-8")

T.write_text(r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048b_raydium_live_bridge_contract_capture as q

class T(unittest.TestCase):
    def test_targets(self):
        self.assertEqual(len(q.TARGETS),3)
        self.assertTrue(any("qarb_011" in x for x in q.TARGETS))
        self.assertTrue(any("merged_live_runtime" in x for x in q.TARGETS))

if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

U.write_text(
"from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_048b_raydium_live_bridge_contract_capture import main\n"
"if __name__=='__main__':main()\n",encoding="utf-8")

print("[PASS] QARB-048B Raydium live bridge contract capture installed")
print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")