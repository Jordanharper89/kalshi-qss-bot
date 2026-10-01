from __future__ import annotations
import importlib,inspect,json
from pathlib import Path

OUT=Path("runtime_state/qseries/qarb_clean_bot/existing_quote_contract_capture.json")
MODULES=[
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.live_account_stream",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.merged_live_runtime",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.raydium_cpmm_hot_adapter",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.raydium_cpmm_live_binding",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.raydium_clmm_hot_adapter",
"qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.raydium_clmm_live_binding",
]

def capture():
    rows=[]
    for name in MODULES:
        try:m=importlib.import_module(name)
        except Exception as e:
            rows.append({"module":name,"import_error":type(e).__name__+":"+str(e)});continue
        funcs=[];classes=[]
        for n,o in vars(m).items():
            if inspect.isfunction(o) and getattr(o,"__module__",None)==m.__name__:
                try:sig=str(inspect.signature(o))
                except Exception:sig="?"
                funcs.append({"name":n,"signature":sig})
            elif inspect.isclass(o) and getattr(o,"__module__",None)==m.__name__:
                try:sig=str(inspect.signature(o))
                except Exception:sig="?"
                methods=[]
                for mn,mo in vars(o).items():
                    if inspect.isfunction(mo):
                        try:ms=str(inspect.signature(mo))
                        except Exception:ms="?"
                        methods.append({"name":mn,"signature":ms})
                classes.append({"name":n,"signature":sig,"methods":methods})
        rows.append({"module":name,"file":getattr(m,"__file__",None),"functions":funcs,"classes":classes})
    payload={"modules":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-034] EXISTING LIVE QUOTE CONTRACT CAPTURE")
    r=capture()
    for m in r["modules"]:
        if m.get("import_error"):
            print("[MODULE_MISSING]",m["module"],m["import_error"]);continue
        print("[MODULE]",m["module"])
        for f in m["functions"]:print("  [FUNCTION]",f["name"],f["signature"])
        for c in m["classes"]:
            print("  [CLASS]",c["name"],c["signature"])
            for x in c["methods"]:print("    [METHOD]",x["name"],x["signature"])
    print("[REPORT]",OUT);print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")
