from __future__ import annotations
import json,time
from pathlib import Path
from .core import WSOL

def exact_provider_inventory(root):
    root=Path(root)
    checks={
      "meteora_dlmm_transfer_decoder":root/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape/usls_072_meteora_orca_exact_transfer_reconciler.py",
      "pumpswap_exact_economic_tape":root/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape/usls_101d_pumpswap_048b_direct_rematerialization_repair.py",
      "source_native_friction":root/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime/usls_124_phase7_source_native_friction_evidence.py",
    }
    return {k:v.is_file() for k,v in checks.items()}

def pretrade_quote_capability(root,template):
    inv=exact_provider_inventory(root)
    venues=tuple(template.get("venues") or ())
    missing=[]
    # Historical exact execution decoding is NOT the same as fresh pre-trade quote math.
    if "METEORA_DLMM" in venues:
        missing.append("METEORA_DLMM_FRESH_BIN_STATE_SWAPQUOTE_NOT_BOUND")
    if "PUMP_SWAP" in venues:
        missing.append("PUMP_SWAP_FRESH_POOL_STATE_FEE_AWARE_QUOTE_NOT_BOUND")
    return {"ready":not missing,"missing":missing,"inventory":inv,
            "truth":"EXACT_EXECUTION_DECODERS_EXIST_BUT_PRETRADE_QUOTE_BINDINGS_ARE_DISTINCT"}

class MockableQuoteProvider:
    def __init__(self,fn):self.fn=fn
    def quote(self,venue,input_asset,output_asset,input_amount):
        q=self.fn(venue,input_asset,output_asset,input_amount)
        if not isinstance(q,dict):return {"exact":False,"reason":"NO_QUOTE"}
        return q
