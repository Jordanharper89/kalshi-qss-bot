from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_live as base

EXECUTION_AUTHORITY=False
READ_ONLY=True
CPMM_PROGRAM="CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
MRIYA_CAPTURE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")

# Certified Raydium CPMM SWAP_BASE_INPUT layout reused from upstream decoder:
# 3 pool, 4 user source, 5 user destination, 6/7 pool vaults, 10/11 pool mints.
POOL_I=3
VAULT_A_I=6
VAULT_B_I=7
MINT_A_I=10
MINT_B_I=11

LivePool=base.LivePool
PoolState=base.PoolState
hydrate=base.hydrate
update=base.update
quote=base.quote
token_amount=base.token_amount

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _pk(x):
    if isinstance(x,str): return x
    if isinstance(x,dict):
        return x.get("pubkey") or x.get("address") or x.get("key")
    return None

def _from_mriya_capture(root):
    p=Path(root)/MRIYA_CAPTURE
    if not p.is_file():
        return []
    try:
        obj=json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    found={}
    for r in _walk(obj):
        venue=str(r.get("venue") or r.get("family") or "").upper()
        pid=str(r.get("program_id") or "")
        if venue!="RAYDIUM_CPMM" and pid!=CPMM_PROGRAM:
            continue
        acc=[_pk(x) for x in (r.get("accounts") or [])]
        if len(acc)<=MINT_B_I:
            continue
        pool,va,vb,ma,mb=acc[POOL_I],acc[VAULT_A_I],acc[VAULT_B_I],acc[MINT_A_I],acc[MINT_B_I]
        if not all((pool,va,vb,ma,mb)):
            continue
        if len({pool,va,vb,ma,mb})<5:
            continue
        found[pool]=LivePool(pool,ma,mb,va,vb,25,10000)
    return list(found.values())

def discover(root):
    # Preserve the already-certified QARB-011 path first.
    found={x.pool:x for x in base.discover(root)}
    # Add exact current Mriya CPMM instruction identities from QARB-030.
    for x in _from_mriya_capture(root):
        found[x.pool]=x
    return list(found.values())

def evidence(root):
    rows=discover(root)
    return {
      "descriptors":len(rows),
      "wsol_pairs":sum(base.c.WSOL in (x.token_a,x.token_b) for x in rows) if hasattr(base,"c") else None,
      "pools":[{"pool":x.pool,"token_a":x.token_a,"token_b":x.token_b,
                "vault_a":x.vault_a,"vault_b":x.vault_b} for x in rows],
      "execution_authority":False
    }
