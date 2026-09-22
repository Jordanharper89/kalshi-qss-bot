from __future__ import annotations
from dataclasses import dataclass
from statistics import mean

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoConditionMetric:
    asset:str
    source_family:str
    metric_name:str
    value:float
    unit:str
    observed_at:str|None
    independent_evidence:bool
    market_native_reference:bool

def _f(v):
    try:
        if v is None: return None
        return float(v)
    except Exception:
        return None

def _emit(out,asset,family,name,value,unit,o,independent,market_native):
    v=_f(value)
    if v is not None:
        out.append(CryptoConditionMetric(
            asset,family,name,v,unit,getattr(o,"observed_at",None),
            independent,market_native
        ))

def extract_crypto_condition_metrics(cohort):
    out=[]
    for family,o in tuple(cohort.observations):
        p=getattr(o,"payload",{}) or {}
        typ=str(getattr(o,"observation_type",""))
        if family=="coinbase":
            asset=str(p.get("base_currency") or str(getattr(o,"subject","")).split("-")[0]).upper()
            if asset not in ("BTC","ETH","SOL"): continue
            _emit(out,asset,family,"spot_price",p.get("price"),"quote_currency",o,False,True)
            _emit(out,asset,family,"spot_volume_24h",p.get("volume"),"base_currency",o,False,True)
            bid=_f(p.get("bid")); ask=_f(p.get("ask"))
            if bid is not None and ask is not None and bid>0 and ask>=bid:
                mid=(bid+ask)/2.0
                _emit(out,asset,family,"bid_ask_spread_bps",(ask-bid)/mid*10000.0,"bps",o,False,True)

        elif family=="bitcoin":
            if typ=="mempool_pressure":
                _emit(out,"BTC",family,"mempool_transaction_count",p.get("count"),"transactions",o,True,False)
                _emit(out,"BTC",family,"mempool_vsize",p.get("vsize"),"vbytes",o,True,False)
                fees=p.get("recommended_fees") or {}
                if isinstance(fees,dict):
                    _emit(out,"BTC",family,"fastest_fee_rate",fees.get("fastestFee"),"sat/vB",o,True,False)
                    _emit(out,"BTC",family,"half_hour_fee_rate",fees.get("halfHourFee"),"sat/vB",o,True,False)
            elif typ=="tip_block_activity":
                _emit(out,"BTC",family,"tip_block_tx_count",p.get("tx_count"),"transactions",o,True,False)
                _emit(out,"BTC",family,"tip_block_weight",p.get("weight"),"weight_units",o,True,False)
                _emit(out,"BTC",family,"tip_block_size",p.get("size"),"bytes",o,True,False)

        elif family=="ethereum":
            if typ=="execution_fee_pressure":
                _emit(out,"ETH",family,"gas_price_wei",p.get("gas_price_wei"),"wei",o,True,False)
                ratios=tuple(x for x in (p.get("gas_used_ratio") or ()) if _f(x) is not None)
                if ratios:
                    _emit(out,"ETH",family,"fee_history_mean_gas_used_ratio",mean(float(x) for x in ratios),"ratio",o,True,False)
            elif typ in ("latest_block_transaction_pressure","finalized_block_activity"):
                _emit(out,"ETH",family,"block_transaction_count",p.get("transaction_count"),"transactions",o,True,False)
                gas_used=_f(p.get("gas_used")); gas_limit=_f(p.get("gas_limit"))
                if gas_used is not None and gas_limit and gas_limit>0:
                    _emit(out,"ETH",family,"block_gas_utilization",gas_used/gas_limit,"ratio",o,True,False)

        elif family=="solana":
            if typ=="mainnet_chain_state":
                _emit(out,"SOL",family,"transaction_count",p.get("transaction_count"),"cumulative_transactions",o,True,False)
                _emit(out,"SOL",family,"slot",p.get("slot"),"slot",o,True,False)
                _emit(out,"SOL",family,"block_height",p.get("block_height"),"blocks",o,True,False)
            elif typ=="finalized_block_activity":
                _emit(out,"SOL",family,"finalized_block_signature_count",p.get("signature_count"),"signatures",o,True,False)
                _emit(out,"SOL",family,"finalized_slot",p.get("slot"),"slot",o,True,False)
    return tuple(out)
