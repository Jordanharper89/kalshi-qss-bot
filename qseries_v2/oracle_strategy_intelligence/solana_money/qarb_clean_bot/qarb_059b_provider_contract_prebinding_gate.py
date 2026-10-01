from __future__ import annotations
import inspect,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_clmm as rc
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import orca_whirlpool as ow

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
CLMM=Path("runtime_state/qseries/qarb_clean_bot/qarb_058a_clmm_local_swap_math.json")
ORCA=Path("runtime_state/qseries/qarb_clean_bot/qarb_058b_orca_local_swap_math.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_059b_provider_contract_prebinding_gate.json")

def sig(x):
    try:return str(inspect.signature(x))
    except Exception:return None

def build(root):
    root=Path(root)
    cl=json.loads((root/CLMM).read_text(encoding="utf-8"))
    oc=json.loads((root/ORCA).read_text(encoding="utf-8"))
    rows={
      "RAYDIUM_CLMM":{"poolstate":sig(rc.PoolState),"bind_local_quoter":sig(rc.bind_local_quoter),
                      "quote_exact_in":sig(rc.quote_exact_in),"math_bound_pools":cl.get("math_bound_pools",0),
                      "probe_complete_pools":cl.get("probe_complete_pools",0)},
      "ORCA_WHIRLPOOL":{"poolstate":sig(ow.PoolState),"bind_local_quoter":sig(ow.bind_local_quoter),
                        "quote_exact_in":sig(ow.quote_exact_in),"math_bound_pools":oc.get("math_bound_pools",0),
                        "probe_complete_pools":oc.get("probe_complete_pools",0)}
    }
    for x in rows.values():
        x["contract_ready"]=bool(x["poolstate"] and x["bind_local_quoter"] and x["quote_exact_in"]
                                 and x["math_bound_pools"]>0 and x["probe_complete_pools"]>0)
    payload={"revision":"QARB_059B","venues":rows,
             "provider_contract_ready":all(x["contract_ready"] for x in rows.values()),
             "provider_bound_live":False,
             "next":"LIVE_SHADOW_VALIDATE_THEN_BIND_EXISTING_PROVIDER_CONTRACTS",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-059B] PROVIDER CONTRACT PREBINDING GATE")
    for k,v in p["venues"].items():
        print("[%s] contract_ready=%s math_bound=%d probe_complete=%d PoolState=%s bind=%s"%(
            k,v["contract_ready"],v["math_bound_pools"],v["probe_complete_pools"],v["poolstate"],v["bind_local_quoter"]))
    print("[PROVIDER_CONTRACT_READY]",p["provider_contract_ready"])
    print("[PROVIDER_BOUND_LIVE]",p["provider_bound_live"])
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
