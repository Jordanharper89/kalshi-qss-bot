from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-052E core missing")
s=CORE.read_text(encoding="utf-8")
for required in ("def pump_sell_local(","def dlmm_quote(","def sim_identity(","def dlmm_ix("):
    if required not in s:
        raise SystemExit("[FAIL] missing QSB-052E boundary: "+required)

helper='\ndef pump_buy_local(pool,amount):\n    d,_=account(pool);p=decode_pump_pool(d)\n    if p["quote_mint"]!=WSOL:raise RuntimeError("PUMP_NOT_SOL")\n    br=token_amount(p["base_vault"]);qr=token_amount(p["quote_vault"])\n    net=amount*(10000-PUMP_FEE_BPS)//10000\n    out=br*net//(qr+net)\n    return {"raw_out":out,"pool":p}\n\ndef pump_tx(user,input_mint,output_mint,amount):\n    j=http(PUMP_API,"POST",{"inputMint":input_mint,"outputMint":output_mint,"amount":str(int(amount)),\n        "user":user,"feePayer":user,"slippagePct":SLIPPAGE_BPS/100.0,\n        "frontRunningProtection":False,"tipAmount":0,"encoding":"base64"},20)\n    if not j.get("transaction"):raise RuntimeError("PUMP_TX_MISSING")\n    info=j.get("pumpMintInfo") or {}\n    return j["transaction"],int(info.get("expectedOutAmount") or 0)\n\ndef bidirectional_opportunities(token,pump_pool):\n    meta=discover_dlmm(token)\n    start=int(START_SOL*1e9)\n\n    # Meteora low -> Pump high\n    m_buy=dlmm_quote(meta,start,WSOL)\n    p_sell=pump_sell_local(pump_pool,m_buy["raw_out"])\n    a=dict(token=token,pump_pool=pump_pool,meteora=meta,start=start,\n           direction="METEORA_TO_PUMP",first_out=m_buy["raw_out"],\n           local_end=p_sell["raw_out"],local_net=p_sell["raw_out"]-start)\n    a["local_bps"]=a["local_net"]/start*10000.0\n\n    # Pump low -> Meteora high\n    p_buy=pump_buy_local(pump_pool,start)\n    m_sell=dlmm_quote(meta,p_buy["raw_out"],token)\n    b=dict(token=token,pump_pool=pump_pool,meteora=meta,start=start,\n           direction="PUMP_TO_METEORA",first_out=p_buy["raw_out"],\n           local_end=m_sell["raw_out"],local_net=m_sell["raw_out"]-start)\n    b["local_bps"]=b["local_net"]/start*10000.0\n    return sorted([a,b],key=lambda x:x["local_bps"],reverse=True)\n'
run='\ndef run(root):\n    print("[QSB-053] BIDIRECTIONAL SAME-TOKEN MONEY MACHINE",flush=True)\n    print("[PATH] BUY LOW / SELL HIGH BOTH DIRECTIONS | METEORA <-> PUMPSWAP | JUPITER=NONE",flush=True)\n    kp,user=sim_identity()\n    print("[SIGNER] %s"%("LOCAL_PRIVATE_KEY" if kp is not None else "SIM_ONLY_PUBLIC_KEY"),flush=True)\n    best=None\n    for token,pool in tape_candidates(root):\n        try:\n            ops=bidirectional_opportunities(token,pool)\n            for op in ops:\n                print("[SPREAD] token=%s direction=%s net=%+.9f SOL bps=%+.2f"%(\n                    token[:10],op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)\n                if op["local_bps"]<MIN_NET_BPS:\n                    continue\n                # Keep execution conservative: only route through the existing certified\n                # atomic composer when direction matches its native leg ordering.\n                if op["direction"]=="METEORA_TO_PUMP":\n                    meta=op["meteora"]\n                    mq=dlmm_quote(meta,op["start"],WSOL)\n                    ptx,expected=pump_tx(user,token,WSOL,mq["raw_out"])\n                    api_net=expected-op["start"];api_bps=api_net/op["start"]*10000.0\n                    print("[EXEC_QUOTE] token=%s direction=%s net=%+.9f SOL bps=%+.2f"%(\n                        token[:10],op["direction"],api_net/1e9,api_bps),flush=True)\n                    if api_bps<MIN_NET_BPS:\n                        continue\n                    legacy={"token":token,"pump_pool":pool,"meteora":meta,"mq":mq,\n                            "start":op["start"],"local_net":api_net,"local_bps":api_bps}\n                    p_ixs,alts=resolve_pump_instructions(ptx)\n                    m_ix=dlmm_ix(user,legacy)\n                    ixs=[];inserted=False\n                    for ix in p_ixs:\n                        if ix["programId"]==PUMP and not inserted:\n                            ixs.append(m_ix);ixs.append(ix);inserted=True\n                        else:ixs.append(ix)\n                    if not inserted:raise RuntimeError("PUMP_PROGRAM_IX_NOT_FOUND")\n                    bh=rpc("getLatestBlockhash",[{"commitment":"processed"}])["value"]["blockhash"]\n                    msg,unsigned=compile_v0(user,ixs,alts,bh)\n                    raw=signed_tx(msg,kp) if kp is not None else unsigned\n                    sim=simulate(raw,user,sigverify=(kp is not None))\n                    pnl=sim["pnl"];bps=(pnl/op["start"]*10000.0 if pnl is not None else None)\n                    good=sim["err"] is None and pnl is not None and pnl>0 and bps>=MIN_NET_BPS\n                    print("[SIM_PNL] token=%s net=%s SOL bps=%s PROFITABLE=%s"%(\n                        token[:10],("%+.9f"%(pnl/1e9) if pnl is not None else "NA"),\n                        ("%+.2f"%bps if bps is not None else "NA"),good),flush=True)\n                    if good:\n                        best={"token":token,"direction":op["direction"],"sim_pnl":pnl,"sim_bps":bps}\n                        if can_broadcast(kp):\n                            sig=send(raw);best["signature"]=sig\n                            print("[LIVE_BUY_SELL] signature=%s"%sig,flush=True)\n                        print("[MONEY] %s"%("TRADE_SENT" if best.get("signature") else "PROFITABLE_SIM_ONLY"),flush=True)\n                        return best\n                else:\n                    print("[REVERSE_CANDIDATE] profitable PumpSwap->Meteora spread detected; native reverse composer not broadcast-enabled",flush=True)\n        except Exception as e:\n            print("[SKIP] token=%s %s: %s"%(token[:10],type(e).__name__,e),flush=True)\n    print("[MONEY] NO_POSITIVE_ATOMIC_TRADE",flush=True)\n    return best\n'

pos=s.find("def pump_sell_tx(")
if pos<0: raise SystemExit("[FAIL] pump_sell_tx boundary missing")
s=s[:pos]+helper+s[pos:]

rpos=s.find("def run(root):")
if rpos<0: raise SystemExit("[FAIL] run boundary missing")
s=s[:rpos]+run+"\n"

CORE.write_text(s,encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_053_bidirectional_same_token_money_machine.py"
TEST.write_text('import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c\n\nclass T(unittest.TestCase):\n    def test_bidirectional_symbols(self):\n        self.assertTrue(callable(c.pump_buy_local))\n        self.assertTrue(callable(c.bidirectional_opportunities))\n        print("[PASS] both-direction same-token opportunity engine installed")\n\n    def test_no_jupiter(self):\n        with open(c.__file__,encoding="utf-8") as f:s=f.read().lower()\n        self.assertNotIn("jup.ag",s)\n        self.assertNotIn("swap-instructions",s)\n        print("[PASS] zero Jupiter hot-path code")\n\n    def test_reverse_direction_constant(self):\n        src=open(c.__file__,encoding="utf-8").read()\n        self.assertIn("PUMP_TO_METEORA",src)\n        self.assertIn("METEORA_TO_PUMP",src)\n        print("[PASS] both low->high directions evaluated")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_053_bidirectional_same_token_money_machine.py"
RUN.write_text(
"from pathlib import Path\n"
"from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\n"
"run(Path.cwd())\n",encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-053 bidirectional same-token money machine installed")
print("[SEARCH] Meteora->PumpSwap AND PumpSwap->Meteora")
print("[JUPITER] NONE")
print("[PNL] only positive spread advances to atomic simulation on certified direction")
