from __future__ import annotations
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from . import mry_006_rpc_governor as gov

def _token_amount(raw):
    return pd._token_amount_from_raw(raw)

def hydrate_candidate(root,row,attempts=4):
    token=str(row["token"])
    pump_pool=str(row["pump_pool"])
    last=None

    for attempt in range(1,int(attempts)+1):
        try:
            meta=row.get("meteora_meta") or c.discover_dlmm(token)
            pump_raw,_=c.account(pump_pool)
            pp=c.decode_pump_pool(pump_raw)

            if pp["quote_mint"]!=c.WSOL:
                raise RuntimeError("PUMP_NOT_WSOL")

            base_raw,_=c.account(pp["base_vault"])
            quote_raw,_=c.account(pp["quote_vault"])
            lb_raw,_=c.account(meta["address"])
            arrays=list(c.dlmm_arrays(meta["address"]))

            pair=pd.PairState(
                token=token,
                pump_pool=pump_pool,
                meteora_pool=meta["address"],
                token_x=meta["token_x"],
                token_y=meta["token_y"],
                decimals_x=int(meta["decimals_x"]),
                decimals_y=int(meta["decimals_y"]),
                pump_base_vault=pp["base_vault"],
                pump_quote_vault=pp["quote_vault"],
                pump_base_reserve=_token_amount(base_raw),
                pump_quote_reserve=_token_amount(quote_raw),
                lb_bytes=lb_raw,
                arrays=arrays,
                dlmm_state=None,
            )

            pair.dlmm_state=pd._build_dlmm_state(pair)

            print(
                "[MRIYA_HYDRATE_READY] token=%s arrays=%d attempt=%d"
                %(token[:10],len(arrays),attempt),
                flush=True,
            )

            return pair

        except Exception as exc:
            last=exc

            if not gov.is_rate_limited(exc) or attempt>=attempts:
                break

            delay=min(12.0,1.5*(2**(attempt-1)))

            print(
                "[MRIYA_HYDRATE_429] token=%s attempt=%d sleep=%.1f"
                %(token[:10],attempt,delay),
                flush=True,
            )

            time.sleep(delay)

    raise RuntimeError(
        "MRIYA_HYDRATE_FAIL:%s:%s"
        %(type(last).__name__,last)
    )
