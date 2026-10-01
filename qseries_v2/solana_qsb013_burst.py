from __future__ import annotations
import asyncio, json, time
from collections import Counter, deque
from pathlib import Path

WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
EXCLUDE={WSOL,USDC}

def _rpc_tx(sig):
    try:
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        return _rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":1}],12.0)
    except Exception:return None

def _mints(tx):
    out=set();meta=(tx or {}).get("meta") or {}
    for k in ("preTokenBalances","postTokenBalances"):
        for b in meta.get(k) or []:
            m=b.get("mint")
            if m and m not in EXCLUDE:out.add(str(m))
    return sorted(out)

async def _capture(seconds=4,max_rows=1200):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    return await capture(seconds=seconds,max_rows=max_rows)

class BurstRadar:
    def __init__(self,root:Path,state_rel=Path("runtime_state/qseries/qsb013_burst")):
        self.root=Path(root).resolve();self.state=self.root/state_rel;self.state.mkdir(parents=True,exist_ok=True)
        self.seen_path=self.state/"seen_signatures.json"
        try:self.seen=deque(json.loads(self.seen_path.read_text()),maxlen=4000)
        except Exception:self.seen=deque(maxlen=4000)
    def scan(self,seconds=4,max_hydrate=8):
        ret=asyncio.run(_capture(seconds,max_rows=1200));rows=list(ret.get("rows") or [])
        sigs=[];fam={}
        for r in rows:
            s=r.get("signature")
            if not s or s in self.seen or s in fam:continue
            fam[s]=str(r.get("venue") or "UNKNOWN");sigs.append(s)
        sigs=sigs[:max_hydrate];mc=Counter();fc=Counter();hydrated=0
        for s in sigs:
            tx=_rpc_tx(s);self.seen.append(s)
            if not isinstance(tx,dict):continue
            hydrated+=1;fc[fam[s]]+=1
            for m in _mints(tx):mc[m]+=1
        try:self.seen_path.write_text(json.dumps(list(self.seen)),encoding="utf-8")
        except Exception:pass
        return {"raw_rows":len(rows),"new_signatures":len(sigs),"hydrated":hydrated,
                "family_counts":dict(fc),"hot_mints":[{"mint":m,"signature_hits":n} for m,n in mc.most_common(16)]}

def expand_hot_mints(hot,timeout=8):
    from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
    rows=[];now=time.time()
    for item in hot[:12]:
        try:x=expand_live_solana_token_pools(token_address=item["mint"],timeout_seconds=timeout)
        except Exception:continue
        for p in list((x.payload or {}).get("pools") or [])[:3]:
            try:px=float(p.get("price_usd"))
            except Exception:continue
            if px<=0:continue
            rows.append({"market_address":str(p.get("pair_address") or ""),"token_mint":item["mint"],
                "family":str(p.get("dex_id") or "UNKNOWN").upper(),"last_price":px,"observed_unix":now,
                "liquidity_usd":p.get("liquidity_usd"),"volume_usd":p.get("volume_h24"),
                "buy_count":p.get("buys_h24"),"sell_count":p.get("sells_h24"),
                "source":"QSB013_BURST"})
    return rows
