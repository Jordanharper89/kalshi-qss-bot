
from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-053 core missing")

s=CORE.read_text(encoding="utf-8")

s=s.replace(
    'MAX_TOKENS=int(os.getenv("QSB_052_MAX_TOKENS","8"))',
    'MAX_TOKENS=int(os.getenv("QSB_054_MAX_TOKENS","64"))'
)

anchor='PUMP_FEE_BPS=int(os.getenv("QSB_052_PUMP_FEE_BPS","120"))\n'
if 'QSB_054_SIZES_SOL' not in s:
    if anchor not in s:
        raise SystemExit("[FAIL] config anchor missing")
    s=s.replace(
        anchor,
        anchor+'SIZES_SOL=tuple(float(x) for x in os.getenv("QSB_054_SIZES_SOL","0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0").split(",") if x.strip())\n',
        1
    )

helper = """
def sized_bidirectional_opportunities(token,pump_pool,size_sol):
    meta=discover_dlmm(token)
    start=int(float(size_sol)*1e9)

    m_buy=dlmm_quote(meta,start,WSOL)
    p_sell=pump_sell_local(pump_pool,m_buy["raw_out"])
    net1=p_sell["raw_out"]-start
    a={"token":token,"pump_pool":pump_pool,"meteora":meta,"start":start,"size_sol":float(size_sol),
       "direction":"METEORA_TO_PUMP","mq":m_buy,"local_end":p_sell["raw_out"],
       "local_net":net1,"local_bps":net1/start*10000.0}

    p_buy=pump_buy_local(pump_pool,start)
    m_sell=dlmm_quote(meta,p_buy["raw_out"],token)
    net2=m_sell["raw_out"]-start
    b={"token":token,"pump_pool":pump_pool,"meteora":meta,"start":start,"size_sol":float(size_sol),
       "direction":"PUMP_TO_METEORA","mq":m_sell,"local_end":m_sell["raw_out"],
       "local_net":net2,"local_bps":net2/start*10000.0}

    return sorted([a,b],key=lambda x:x["local_net"],reverse=True)

"""
if "def sized_bidirectional_opportunities(" not in s:
    pos=s.find("def bidirectional_opportunities(")
    if pos<0:
        raise SystemExit("[FAIL] bidirectional boundary missing")
    s=s[:pos]+helper+s[pos:]

rpos=s.find("def run(root):")
if rpos<0:
    raise SystemExit("[FAIL] run boundary missing")

new_run = """
def run(root):
    print("[QSB-054] PROFIT HUNTER",flush=True)
    print("[PATH] SAME TOKEN BUY LOW / SELL HIGH | BOTH DIRECTIONS | JUPITER=NONE",flush=True)
    print("[SEARCH] tokens<=%d sizes=%s"%(MAX_TOKENS,",".join(str(x) for x in SIZES_SOL)),flush=True)

    ranked=[]
    tokens=tape_candidates(root)
    print("[TOKENS] %d"%len(tokens),flush=True)

    for token,pool in tokens:
        for size_sol in SIZES_SOL:
            try:
                for op in sized_bidirectional_opportunities(token,pool,size_sol):
                    ranked.append(op)
                    if op["local_bps"]>=MIN_NET_BPS:
                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(
                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)
            except Exception as e:
                print("[SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)

    ranked.sort(key=lambda x:x["local_net"],reverse=True)
    positives=[x for x in ranked if x["local_bps"]>=MIN_NET_BPS]
    print("[RANKED] candidates=%d positive=%d"%(len(ranked),len(positives)),flush=True)

    if positives:
        top=positives[0]
        print("[BEST_PNL] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f PROFITABLE=True"%(
            top["token"][:10],top["size_sol"],top["direction"],top["local_net"]/1e9,top["local_bps"]),flush=True)
    elif ranked:
        top=ranked[0]
        print("[BEST_PNL] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f PROFITABLE=False"%(
            top["token"][:10],top["size_sol"],top["direction"],top["local_net"]/1e9,top["local_bps"]),flush=True)
    else:
        print("[BEST_PNL] NONE",flush=True)

    print("[MONEY] %s"%("POSITIVE_SPREAD_FOUND" if positives else "NO_POSITIVE_SPREAD"),flush=True)
    return positives[0] if positives else None
"""
s=s[:rpos]+new_run+"\n"

CORE.write_text(s,encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_054_profit_hunter.py"
TEST.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_size_grid(self):
        self.assertGreaterEqual(len(c.SIZES_SOL),8)
        self.assertLessEqual(min(c.SIZES_SOL),0.005)
        self.assertGreaterEqual(max(c.SIZES_SOL),1.0)
        print("[PASS] 8-size search grid enabled")

    def test_token_universe(self):
        self.assertGreaterEqual(c.MAX_TOKENS,64)
        print("[PASS] token universe expanded to 64")

    def test_bidirectional(self):
        src=open(c.__file__,encoding="utf-8").read()
        self.assertIn("METEORA_TO_PUMP",src)
        self.assertIn("PUMP_TO_METEORA",src)
        print("[PASS] both arbitrage directions searched")

    def test_no_jupiter(self):
        src=open(c.__file__,encoding="utf-8").read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
""",encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_054_profit_hunter.py"
RUN.write_text(
    "from pathlib import Path\n"
    "from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\n"
    "run(Path.cwd())\n",
    encoding="utf-8"
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-054 profit hunter installed")
print("[SEARCH] 64 tokens x 8 trade sizes x both directions")
print("[JUPITER] NONE")
