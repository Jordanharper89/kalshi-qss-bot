from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-056 core missing")

s=CORE.read_text(encoding="utf-8")

if "MRIYA_WALLET=" not in s:
    anchor='WSOL="So11111111111111111111111111111111111111112"\n'
    if anchor not in s:
        raise SystemExit("[FAIL] WSOL boundary missing")
    s=s.replace(anchor,anchor+'MRIYA_WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"\nPUMP_FUN="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"\nUSDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"\nUSDT="Es9vMFrzaCERmJfrF4H2FYD8gLtAZ57XqHq9P8rNw8w"\n',1)

if "def mriya_hot_tokens(" not in s:
    pos=s.find("def run(root):")
    if pos<0:
        raise SystemExit("[FAIL] run boundary missing")
    s=s[:pos]+'\ndef _hot_token_mints_from_tx(tx):\n    if not isinstance(tx,dict):\n        return []\n    meta=tx.get("meta") or {}\n    out=[];seen=set()\n    for key in ("preTokenBalances","postTokenBalances"):\n        for row in meta.get(key) or []:\n            mint=row.get("mint")\n            if not mint or mint in (WSOL,USDC,USDT) or mint in seen:\n                continue\n            seen.add(mint);out.append(mint)\n    return out\n\ndef mriya_hot_tokens(limit_signatures=24,max_transactions=12):\n    sigs=rpc("getSignaturesForAddress",[MRIYA_WALLET,{"limit":int(limit_signatures),"commitment":"processed"}]) or []\n    ranked={}\n    now=time.time()\n    for rank,row in enumerate(sigs[:max_transactions]):\n        sig=row.get("signature")\n        if not sig or row.get("err") is not None:\n            continue\n        try:\n            tx=rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"processed","maxSupportedTransactionVersion":0}])\n        except Exception:\n            continue\n        bt=float((tx or {}).get("blockTime") or 0)\n        age=max(0.0,now-bt) if bt else 999999.0\n        recency=max(0.0,120.0-age)\n        for mint in _hot_token_mints_from_tx(tx):\n            score=recency*1000.0+(max_transactions-rank)\n            if mint not in ranked or score>ranked[mint]["score"]:\n                ranked[mint]={"mint":mint,"score":score,"age":age,"signature":sig}\n    return sorted(ranked.values(),key=lambda x:x["score"],reverse=True)\n\ndef canonical_pump_pool(token):\n    from solders.pubkey import Pubkey\n    base=Pubkey.from_string(token)\n    quote=Pubkey.from_string(WSOL)\n    pump=Pubkey.from_string(PUMP_FUN)\n    amm=Pubkey.from_string(PUMP)\n    creator,_=Pubkey.find_program_address([b"pool-authority",bytes(base)],pump)\n    pool,_=Pubkey.find_program_address([b"pool",(0).to_bytes(2,"little"),bytes(creator),bytes(base),bytes(quote)],amm)\n    addr=str(pool)\n    try:\n        d,_=account(addr)\n        p=decode_pump_pool(d)\n        if p.get("base_mint")==token and p.get("quote_mint")==WSOL:\n            return addr\n    except Exception:\n        return None\n    return None\n\ndef mriya_first_candidates(root):\n    fallback=tape_candidates(root)\n    by_token={t:p for t,p in fallback}\n    out=[];seen=set()\n    for h in mriya_hot_tokens():\n        token=h["mint"]\n        pool=by_token.get(token) or canonical_pump_pool(token)\n        if not pool or token in seen:\n            continue\n        seen.add(token);out.append((token,pool))\n        print("[MRIYA_HOT] token=%s age=%.2fs pool=%s"%(token[:10],h["age"],pool[:10]),flush=True)\n    for token,pool in fallback:\n        if token not in seen:\n            seen.add(token);out.append((token,pool))\n    return out[:MAX_TOKENS]\n\n'+s[pos:]

old='    tokens=tape_candidates(root)\n'
new='    tokens=mriya_first_candidates(root)\n'
if old not in s:
    raise SystemExit("[FAIL] QSB-056 candidate source missing")
s=s.replace(old,new,1)

old_sizes='SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_054_SIZES_SOL","0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0").split(",") if x.strip())'
new_sizes='SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_057_SIZES_SOL","0.005,0.01,0.025,0.05,0.1,0.15,0.25,0.5,0.6,1.0,1.25,1.75").split(",") if x.strip())'
if old_sizes in s:
    s=s.replace(old_sizes,new_sizes,1)

s=s.replace("[QSB-056] SNAPSHOT-LOCAL PROFIT HUNTER","[QSB-057] MRIYA-HOTSET SNAPSHOT ARBITRAGE ENGINE",1)
s=s.replace("[PATH] SAME TOKEN BUY LOW / SELL HIGH | BOTH DIRECTIONS | JUPITER=NONE",
            "[PATH] MRIYA-HOT TOKENS FIRST -> SAME TOKEN BUY LOW / SELL HIGH | JUPITER=NONE",1)

CORE.write_text(s,encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_057_mriya_hotset_arb_engine.py"
TEST.write_text('import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c\n\nclass T(unittest.TestCase):\n    def test_hot_tx_mints(self):\n        tx={"meta":{"preTokenBalances":[{"mint":"TokenAAA"},{"mint":c.WSOL}],\n                    "postTokenBalances":[{"mint":"TokenAAA"},{"mint":"TokenBBB"}]}}\n        self.assertEqual(c._hot_token_mints_from_tx(tx),["TokenAAA","TokenBBB"])\n        print("[PASS] recent target-wallet transactions yield dynamic token mints")\n\n    def test_hot_first_merge(self):\n        old_hot,old_tape,old_pool=c.mriya_hot_tokens,c.tape_candidates,c.canonical_pump_pool\n        c.mriya_hot_tokens=lambda:[{"mint":"HOT","score":1,"age":2.0,"signature":"S"}]\n        c.tape_candidates=lambda root:[("COLD","P2")]\n        c.canonical_pump_pool=lambda token:"P1" if token=="HOT" else None\n        try:\n            x=c.mriya_first_candidates(".")\n            self.assertEqual(x[0],("HOT","P1"))\n            self.assertEqual(x[1],("COLD","P2"))\n        finally:\n            c.mriya_hot_tokens,c.tape_candidates,c.canonical_pump_pool=old_hot,old_tape,old_pool\n        print("[PASS] hot wallet tokens are searched before fallback tape")\n\n    def test_size_band(self):\n        self.assertIn(0.15,c.SIZES_SOL)\n        self.assertIn(0.6,c.SIZES_SOL)\n        self.assertIn(1.25,c.SIZES_SOL)\n        print("[PASS] size grid covers sub-SOL and >1-SOL bands")\n\n    def test_no_jupiter(self):\n        with open(c.__file__,encoding="utf-8") as f:\n            src=f.read().lower()\n        self.assertNotIn("jup.ag",src)\n        self.assertNotIn("swap-instructions",src)\n        print("[PASS] zero Jupiter hot-path code")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_057_mriya_hotset_arb_engine.py"
RUN.write_text(
    "from pathlib import Path\n"
    "from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\n"
    "run(Path.cwd())\n",
    encoding="utf-8"
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-057 Mriya-hotset arbitrage engine installed")
print("[DISCOVERY] recent Mriya transactions -> hot token mints -> PumpSwap pool lookup")
print("[SEARCH] hot tokens first + 12 sizes + both directions")
print("[STATE] one snapshot hydration per token")
print("[JUPITER] NONE")
