from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import PROGRAM

def build(root):
    base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
    src=json.loads((base/"launchlab_exact_account_economics.json").read_text(encoding="utf-8"))
    rows=[]
    for n,x in enumerate(src["rows"]):
        if x["decoder_state"]!="EXACT_LAUNCHLAB_BUY_ECONOMICS":
            continue
        rows.append({
            "trade_id":f'RAYDIUM_LAUNCHLAB:{x["signature"]}:{n}',
            "signature":x["signature"],
            "venue":"RAYDIUM_LAUNCHLAB",
            "program_id":PROGRAM,
            "market_address":x["pool"],
            "token_address":x["base_mint"],
            "quote_mint":x["quote_mint"],
            "side":"BUY",
            "trader":x["trader"],
            "base_amount":x["base_amount"],
            "quote_amount":x["quote_amount"],
            "effective_price":x["effective_price"],
            "decoder_state":"EXACT_ECONOMIC_TRADE",
            "source_lineage":{
                "contract":"USLS_060",
                "census":"USLS_061",
                "economics":"USLS_062C"
            },
            "execution_authority":False
        })
    return {
        "revision":"USLS_063B",
        "exact_trade_count":len(rows),
        "rows":rows,
        "profitability_claimed":False,
        "execution_authority":False,
        "read_only":True
    }

def write(root):
    d=build(root)
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_universal_trade_rows.json"
    p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    return p,d
