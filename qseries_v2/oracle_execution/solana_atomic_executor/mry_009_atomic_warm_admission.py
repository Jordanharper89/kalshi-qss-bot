from __future__ import annotations
import threading

LOCK=threading.RLock()

def _register_pair(state,pair):
    token=str(pair.token)

    if any(
        str(x.token)==token
        for x in state.get("pairs",[])
    ):
        return False

    pairs=state.setdefault("pairs",[])
    index=len(pairs)
    pairs.append(pair)

    preg=state.setdefault("preg",{})
    preg[pair.pump_base_vault]=(index,"PUMP_BASE")
    preg[pair.pump_quote_vault]=(index,"PUMP_QUOTE")
    preg[pair.meteora_pool]=(index,"DLMM_POOL")

    for j,a in enumerate(pair.arrays):
        preg[a[1]]=(index,"DLMM_ARRAY_%d"%j)

    addresses=state.setdefault("addresses",[])

    for address in pair.watched_accounts():
        if address not in addresses:
            addresses.append(address)

    eps=state.get("eps")

    if eps is not None:
        try:
            from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as merged

            eps[token].extend(
                (
                    merged._pump_ep(pair),
                    merged._dlmm_ep(pair),
                )
            )

        except Exception:
            pass

    return True

def admit(rt,state,pair,readiness):
    token=str(pair.token)

    with LOCK:
        changed=_register_pair(
            state,
            pair,
        )

        rt.READY_TOKENS.add(
            token
        )

    print(
        "[MRIYA_WARM_ADMIT] "
        "token=%s changed=%s warm=%d "
        "addresses=%d forward=%s"
        %(
            token[:10],
            changed,
            len(rt.READY_TOKENS),
            len(state.get("addresses",[])),
            bool(readiness.get("forward")),
        ),
        flush=True,
    )

    return changed
