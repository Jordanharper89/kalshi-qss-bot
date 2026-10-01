from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-055 core missing")

s=CORE.read_text(encoding="utf-8")

anchor="def sized_bidirectional_opportunities("
if anchor not in s:
    raise SystemExit("[FAIL] QSB-055 quote boundary missing")
if "def build_token_snapshot(" not in s:
    s=s.replace(anchor,'\ndef build_token_snapshot(token,pump_pool):\n    from meteora_dlmm import PoolState\n    meta=discover_dlmm(token)\n    lb,_=account(meta["address"])\n    arr=dlmm_arrays(meta["address"])\n    state=PoolState.from_accounts(\n        lb,[x[2] for x in arr],\n        decimals_x=meta["decimals_x"],\n        decimals_y=meta["decimals_y"],\n        lb_pair_key=b58d(meta["address"]),\n        exhaustive=True\n    )\n    pd,_=account(pump_pool)\n    pp=decode_pump_pool(pd)\n    if pp["quote_mint"]!=WSOL:\n        raise RuntimeError("PUMP_NOT_SOL")\n    return {\n        "token":token,\n        "pump_pool":pump_pool,\n        "meteora":meta,\n        "dlmm_state":state,\n        "pump_base_reserve":token_amount(pp["base_vault"]),\n        "pump_quote_reserve":token_amount(pp["quote_vault"]),\n    }\n\ndef dlmm_quote_snapshot(snap,amount_raw,input_mint):\n    from meteora_dlmm import quote\n    meta=snap["meteora"]\n    if input_mint==meta["token_x"]:\n        swap_for_y=True\n    elif input_mint==meta["token_y"]:\n        swap_for_y=False\n    else:\n        raise RuntimeError("DLMM_DIRECTION")\n    q=quote(snap["dlmm_state"],amount_in=int(amount_raw),swap_for_y=swap_for_y,strict=True)\n    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):\n        raise RuntimeError("DLMM_PARTIAL")\n    return {\n        "raw_out":int(q.amount_out),\n        "bins_crossed":max(1,int(getattr(q,"bins_crossed",1) or 1)),\n        "swap_for_y":swap_for_y,\n        "arrays":[],\n    }\n\ndef pump_sell_snapshot(snap,amount):\n    br=snap["pump_base_reserve"];qr=snap["pump_quote_reserve"]\n    net=int(amount)*(10000-PUMP_FEE_BPS)//10000\n    return qr*net//(br+net)\n\ndef pump_buy_snapshot(snap,amount):\n    br=snap["pump_base_reserve"];qr=snap["pump_quote_reserve"]\n    net=int(amount)*(10000-PUMP_FEE_BPS)//10000\n    return br*net//(qr+net)\n\ndef sized_snapshot_opportunities(snap,size_sol):\n    token=snap["token"]\n    start=int(float(size_sol)*1e9)\n\n    mb=dlmm_quote_snapshot(snap,start,WSOL)\n    ps=pump_sell_snapshot(snap,mb["raw_out"])\n    net1=ps-start\n    a={\n        "token":token,"pump_pool":snap["pump_pool"],"meteora":snap["meteora"],\n        "start":start,"size_sol":float(size_sol),"direction":"METEORA_TO_PUMP",\n        "mq":mb,"local_end":ps,"local_net":net1,"local_bps":net1/start*10000.0\n    }\n\n    pb=pump_buy_snapshot(snap,start)\n    ms=dlmm_quote_snapshot(snap,pb,token)\n    net2=ms["raw_out"]-start\n    b={\n        "token":token,"pump_pool":snap["pump_pool"],"meteora":snap["meteora"],\n        "start":start,"size_sol":float(size_sol),"direction":"PUMP_TO_METEORA",\n        "mq":ms,"local_end":ms["raw_out"],"local_net":net2,"local_bps":net2/start*10000.0\n    }\n    return sorted([a,b],key=lambda x:x["local_net"],reverse=True)\n\n'+anchor,1)

old_loop='    for token,pool in tokens:\n        try:\n            meta=discover_dlmm(token)\n        except Exception as e:\n            print("[SKIP_TOKEN] token=%s %s: %s"%(token[:10],type(e).__name__,e),flush=True)\n            continue\n\n        for size_sol in SIZES_SOL:\n            try:\n                for op in sized_bidirectional_opportunities(token,pool,size_sol,meta=meta):\n                    ranked.append(op)\n                    if op["local_bps"]>=MIN_NET_BPS:\n                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(\n                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)\n            except RuntimeError as e:\n                if str(e)=="DLMM_PARTIAL":\n                    print("[SIZE_SKIP] token=%s size=%.3f DLMM_PARTIAL"%(token[:10],size_sol),flush=True)\n                    continue\n                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)\n            except Exception as e:\n                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)\n'
new_loop='    for token,pool in tokens:\n        try:\n            snap=build_token_snapshot(token,pool)\n            print("[SNAPSHOT] token=%s hydrated_once=True"%(token[:10]),flush=True)\n        except Exception as e:\n            print("[SKIP_TOKEN] token=%s %s: %s"%(token[:10],type(e).__name__,e),flush=True)\n            continue\n\n        for size_sol in SIZES_SOL:\n            try:\n                for op in sized_snapshot_opportunities(snap,size_sol):\n                    ranked.append(op)\n                    if op["local_bps"]>=MIN_NET_BPS:\n                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(\n                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)\n            except RuntimeError as e:\n                if str(e)=="DLMM_PARTIAL":\n                    print("[SIZE_SKIP] token=%s size=%.3f DLMM_PARTIAL"%(token[:10],size_sol),flush=True)\n                    continue\n                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)\n            except Exception as e:\n                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)\n'
if old_loop not in s:
    raise SystemExit("[FAIL] exact QSB-055 scan loop missing")
s=s.replace(old_loop,new_loop,1)

s=s.replace("[QSB-054] PROFIT HUNTER","[QSB-056] SNAPSHOT-LOCAL PROFIT HUNTER",1)

CORE.write_text(s,encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_056_snapshot_local_quote_engine.py"
TEST.write_text('import inspect,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c\n\nclass T(unittest.TestCase):\n    def test_snapshot_engine(self):\n        self.assertTrue(callable(c.build_token_snapshot))\n        self.assertTrue(callable(c.sized_snapshot_opportunities))\n        print("[PASS] snapshot-local engine installed")\n\n    def test_size_path_no_network(self):\n        src=inspect.getsource(c.sized_snapshot_opportunities)\n        for bad in ("discover_dlmm(","dlmm_arrays(","account(","token_amount("):\n            self.assertNotIn(bad,src)\n        print("[PASS] all trade sizes quote with zero network hydration")\n\n    def test_local_pump_math(self):\n        s={"pump_base_reserve":1_000_000_000,"pump_quote_reserve":1_000_000_000}\n        self.assertGreater(c.pump_buy_snapshot(s,1_000_000),0)\n        self.assertGreater(c.pump_sell_snapshot(s,1_000_000),0)\n        print("[PASS] PumpSwap reserves reused locally")\n\n    def test_no_jupiter(self):\n        with open(c.__file__,encoding="utf-8") as f: src=f.read().lower()\n        self.assertNotIn("jup.ag",src)\n        self.assertNotIn("swap-instructions",src)\n        print("[PASS] zero Jupiter hot-path code")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_056_snapshot_local_quote_engine.py"
RUN.write_text(
    "from pathlib import Path\n"
    "from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\n"
    "run(Path.cwd())\n",
    encoding="utf-8"
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-056 snapshot-local quote engine installed")
print("[FIX] one Meteora/PumpSwap state hydration per token")
print("[FIX] all 8 sizes quote locally from that snapshot")
print("[FIX] removed repeated per-size RPC calls causing HTTP 429")
print("[JUPITER] NONE")
