from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from decimal import Decimal
from .oad_264_solana_token_mint_authority_supply_intelligence import acquire_solana_token_mint_state
from .oad_252_crypto_independent_source_expansion_foundation import (
    build_independent_crypto_observation,
    verify_independent_crypto_observation,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OFFICIAL_RPC="https://api.mainnet.solana.com"
PUBLIC_INDEXED_RPC="https://rpc.solanatracker.io/public"

def _configured_indexed_endpoints():
    rows=[]
    explicit=str(os.getenv("SOLANA_INDEXED_RPC_URL") or "").strip()
    general=str(os.getenv("SOLANA_RPC_URL") or "").strip()
    if explicit:
        rows.append(("configured_indexed_rpc",explicit))
    if general and general != explicit:
        rows.append(("configured_rpc",general))
    rows.append(("solanatracker_public_rpc",PUBLIC_INDEXED_RPC))
    # Official endpoint remains last-resort only. It is known to throttle this
    # indexed method and is not treated as the preferred production provider.
    rows.append(("solana_public_rpc_last_resort",OFFICIAL_RPC))
    out=[]
    seen=set()
    for provider,url in rows:
        if url and url not in seen:
            seen.add(url); out.append((provider,url))
    return tuple(out)

def _post_rpc(url,method,params,timeout):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type":"application/json",
            "Accept":"application/json",
            "User-Agent":"Oracle-Q-Series/1.0",
        },
    )
    with urllib.request.urlopen(req,timeout=float(timeout)) as r:
        data=json.loads(r.read().decode())
    if data.get("error"):
        raise RuntimeError("RPC error: "+str(data["error"]))
    return data.get("result")

def _get_largest_accounts_with_failover(token_address,timeout_seconds=20.0):
    failures=[]
    for provider,url in _configured_indexed_endpoints():
        try:
            result=_post_rpc(
                url,
                "getTokenLargestAccounts",
                [token_address,{"commitment":"finalized"}],
                timeout_seconds,
            )
            rows=(result or {}).get("value") or []
            if rows:
                return provider,url,result,tuple(failures)
            failures.append((provider,"EMPTY_RESULT"))
        except urllib.error.HTTPError as exc:
            failures.append((provider,"HTTP_"+str(exc.code)))
            print("[PROVIDER_FAILOVER]",provider,"HTTP",exc.code)
        except Exception as exc:
            failures.append((provider,type(exc).__name__))
            print("[PROVIDER_FAILOVER]",provider,type(exc).__name__,str(exc)[:180])
    raise RuntimeError("all indexed Solana RPC providers failed: "+repr(tuple(failures)))

def acquire_solana_holder_concentration(token_address=None,timeout_seconds=20.0):
    # OAD-264 remains the frozen/certified source of finalized mint supply truth.
    mint=acquire_solana_token_mint_state(token_address,timeout_seconds)
    token_address=mint.payload["token_address"]
    supply=Decimal(str(mint.payload["supply_raw"]))
    if supply <= 0:
        raise RuntimeError("token supply is not positive")

    provider,rpc_url,result,failures=_get_largest_accounts_with_failover(
        token_address,
        timeout_seconds,
    )
    rows=(result or {}).get("value") or []
    amounts=[Decimal(str(x.get("amount") or "0")) for x in rows]
    top1=amounts[0]
    top5=sum(amounts[:5],Decimal(0))
    top20=sum(amounts[:20],Decimal(0))

    payload={
        "token_address":token_address,
        "slot":(result or {}).get("context",{}).get("slot"),
        "supply_raw":str(supply),
        "largest_account_count":len(rows),
        "top1_share":float(top1/supply),
        "top5_share":float(top5/supply),
        "top20_share":float(top20/supply),
        "largest_accounts":tuple(
            {
                "address":x.get("address"),
                "amount":x.get("amount"),
                "decimals":x.get("decimals"),
                "ui_amount_string":x.get("uiAmountString"),
            }
            for x in rows[:20]
        ),
        "indexed_rpc_provider":provider,
        "indexed_rpc_url":rpc_url,
        "provider_failures":failures,
        "commitment":"finalized",
        "method":"getTokenLargestAccounts",
    }

    observation=build_independent_crypto_observation(
        source_id="source.onchain.solana.holder_concentration."+token_address,
        provider=provider,
        source_class="holder_concentration",
        subject=token_address,
        observation_type="solana_token_holder_concentration",
        payload=payload,
    )
    if not verify_independent_crypto_observation(observation):
        raise RuntimeError("OAD-252 provenance verification failed")
    return observation
