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
    except Exception:
        return None

def _mints(tx):
    out=set()
    meta=(tx or {}).get("meta") or {}
    for k in ("preTokenBalances","postTokenBalances"):
        for b in meta.get(k) or []:
            m=b.get("mint")
            if m and m not in EXCLUDE:out.add(str(m))
    return sorted(out)

async def _capture(seconds=4,max_rows=1200):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    return await capture(seconds=seconds,max_rows=max_rows)

class BurstRadar:
    def __init__(self,root:Path,state_rel=Path("runtime_state/qseries/solana_burst_radar")):
        self.root=Path(root).resolve();self.state=self.root/state_rel
        self.seen_path=self.state/"seen_signatures.json";self.state.mkdir(parents=True,exist_ok=True)
        try:self.seen=deque(json.loads(self.seen_path.read_text()),maxlen=4000)
        except Exception:self.seen=deque(maxlen=4000)

    def scan(self,seconds=4,max_hydrate=8):
        ret=asyncio.run(_capture(seconds=seconds))
        rows=list(ret.get("rows") or [])
        sigs=[];family_by_sig={}
        for r in rows:
            sig=r.get("signature");fam=str(r.get("venue") or "UNKNOWN")
            if not sig or sig in self.seen or sig in family_by_sig:continue
            family_by_sig[sig]=fam;sigs.append(sig)
        sigs=sigs[:max_hydrate]
        mint_counts=Counter();family_counts=Counter();hydrated=0
        for sig in sigs:
            tx=_rpc_tx(sig)
            self.seen.append(sig)
            if not isinstance(tx,dict):continue
            hydrated+=1;fam=family_by_sig[sig];family_counts[fam]+=1
            for m in _mints(tx):mint_counts[m]+=1
        self.seen_path.write_text(json.dumps(list(self.seen)),encoding="utf-8")
        hot=[{"mint":m,"signature_hits":n} for m,n in mint_counts.most_common(16)]
        out={"raw_rows":len(rows),"new_signatures":len(sigs),"hydrated":hydrated,
             "family_counts":dict(family_counts),"hot_mints":hot,"captured_unix":time.time()}
        (self.state/"latest.json").write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
        return out

def expand_hot_mints(hot,timeout=8.0):
    from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
    now=time.time();rows=[];errors=[]
    for item in hot[:12]:
        mint=item["mint"]
        try:
            x=expand_live_solana_token_pools(token_address=mint,timeout_seconds=timeout)
            pools=list((x.payload or {}).get("pools") or [])
        except Exception as e:
            errors.append({"mint":mint,"error":type(e).__name__});continue
        ranked=[]
        for p in pools:
            try:px=float(p.get("price_usd"))
            except Exception:continue
            try:liq=float(p.get("liquidity_usd") or 0)
            except Exception:liq=0
            try:vol=float(p.get("volume_h24") or 0)
            except Exception:vol=0
            if px<=0 or liq<1000:continue
            ranked.append((liq,vol,p))
        ranked.sort(key=lambda z:(z[0],z[1]),reverse=True)
        for _,__,p in ranked[:3]:
            rows.append({"market_address":str(p.get("pair_address") or ""),"token_mint":mint,
                "family":str(p.get("dex_id") or "UNKNOWN").upper(),"last_price":float(p["price_usd"]),
                "observed_unix":now,"liquidity_usd":p.get("liquidity_usd"),"volume_usd":p.get("volume_h24"),
                "buy_count":p.get("buys_h24"),"sell_count":p.get("sells_h24"),
                "burst_signature_hits":item["signature_hits"],"source":"QSB010_ONCHAIN_BURST_RADAR"})
    return rows,errors
