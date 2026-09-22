from __future__ import annotations
import json
from pathlib import Path

def build(root):
    base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
    prior=json.loads((base/"raydium_full_family_final_gate.json").read_text(encoding="utf-8"))
    ll=json.loads((base/"launchlab_universal_trade_rows.json").read_text(encoding="utf-8"))

    matrix=dict(prior["matrix"])
    matrix["RAYDIUM_LAUNCHLAB"]={
        **matrix["RAYDIUM_LAUNCHLAB"],
        "exact_universal_trade_rows":ll["exact_trade_count"],
        "status":"EXACT_LAUNCHLAB_BUY_TRADE_DECODER_CERTIFIED"
        if ll["exact_trade_count"]>=4 else "NOT_CERTIFIED"
    }

    strict=(
        matrix["RAYDIUM_V4"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_CPMM"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_CLMM"]["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
        and matrix["RAYDIUM_LAUNCHLAB"]["status"]=="EXACT_LAUNCHLAB_BUY_TRADE_DECODER_CERTIFIED"
    )

    return {
        "revision":"USLS_064B",
        "matrix":matrix,
        "strict_raydium_family_certified":strict,
        "raydium_family_boundary_closed":strict,
        "phase4_status":"IN_PROGRESS",
        "next_boundary":"METEORA_ORCA_SHARED_DECODER_PLUGINS"
        if strict else "CONTINUE_RAYDIUM_REPAIR",
        "profitability_claimed":False,
        "execution_authority":False,
        "read_only":True
    }

def write(root):
    d=build(root)
    p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_strict_full_family_certification.json"
    p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    return p,d
