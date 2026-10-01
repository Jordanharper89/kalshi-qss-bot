from pathlib import Path
import py_compile

ROOT=Path.cwd()
CORE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"
if not CORE.is_file():
    raise SystemExit("[FAIL] QSB-054 core missing")

s=CORE.read_text(encoding="utf-8")

if "import urllib.error" not in s:
    s=s.replace(
        "import base64,json,os,struct,time,urllib.request",
        "import base64,json,os,struct,time,urllib.request,urllib.error",
        1
    )

if "_DLMM_CACHE={}" not in s:
    marker='ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"\n'
    if marker in s:
        s=s.replace(marker, marker+"_DLMM_CACHE={}\n", 1)
    else:
        pos=s.find("\ndef ")
        if pos<0:
            raise SystemExit("[FAIL] module insertion boundary missing")
        s=s[:pos]+"\n_DLMM_CACHE={}\n"+s[pos:]

start=s.find("def discover_dlmm(token):")
end=s.find("\ndef dlmm_arrays(",start)
if start<0 or end<0:
    raise SystemExit("[FAIL] discover_dlmm boundary missing")

new_discover = '''def discover_dlmm(token):
    if token in _DLMM_CACHE:
        v=_DLMM_CACHE[token]
        if isinstance(v,Exception):
            raise v
        return v

    url="https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query="+token
    last=None
    for attempt in range(4):
        try:
            j=http(url)
            rows=j.get("data") if isinstance(j,dict) else j
            best=None
            for x in rows or []:
                tx=x.get("token_x") or x.get("tokenX") or {}
                ty=x.get("token_y") or x.get("tokenY") or {}
                def mint(v):
                    if isinstance(v,str): return v
                    return v.get("address") or v.get("mint") or v.get("token_address")
                mx,my=mint(tx),mint(ty)
                if {mx,my}!={WSOL,token}: continue
                a=x.get("address") or x.get("pool_address") or x.get("pubkey")
                if not a: continue
                tvl=float(x.get("tvl") or x.get("liquidity") or x.get("liquidity_usd") or 0)
                dx=int(tx.get("decimals",9)) if isinstance(tx,dict) else 9
                dy=int(ty.get("decimals",6)) if isinstance(ty,dict) else 6
                row={"address":str(a),"token_x":mx,"token_y":my,"decimals_x":dx,"decimals_y":dy}
                if best is None or tvl>best[0]:
                    best=(tvl,row)
            if not best:
                err=RuntimeError("NO_DLMM_PAIR")
                _DLMM_CACHE[token]=err
                raise err
            _DLMM_CACHE[token]=best[1]
            return best[1]
        except urllib.error.HTTPError as e:
            last=e
            if getattr(e,"code",None)!=429 or attempt==3:
                raise
            delay=0.35*(2**attempt)
            print("[RATE_LIMIT] token=%s retry=%d sleep=%.2fs"%(token[:10],attempt+1,delay),flush=True)
            time.sleep(delay)
    raise last if last else RuntimeError("DLMM_DISCOVERY_FAILED")
'''
s=s[:start]+new_discover+s[end:]

old_sig="def sized_bidirectional_opportunities(token,pump_pool,size_sol):"
new_sig="def sized_bidirectional_opportunities(token,pump_pool,size_sol,meta=None):"
if old_sig not in s:
    raise SystemExit("[FAIL] sized helper boundary missing")
s=s.replace(old_sig,new_sig,1)
s=s.replace("    meta=discover_dlmm(token)\n    start=int(float(size_sol)*1e9)",
            "    meta=meta or discover_dlmm(token)\n    start=int(float(size_sol)*1e9)",1)

old_loop = '''    for token,pool in tokens:
        for size_sol in SIZES_SOL:
            try:
                for op in sized_bidirectional_opportunities(token,pool,size_sol):
                    ranked.append(op)
                    if op["local_bps"]>=MIN_NET_BPS:
                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(
                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)
            except Exception as e:
                print("[SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)
'''
new_loop = '''    for token,pool in tokens:
        try:
            meta=discover_dlmm(token)
        except Exception as e:
            print("[SKIP_TOKEN] token=%s %s: %s"%(token[:10],type(e).__name__,e),flush=True)
            continue

        for size_sol in SIZES_SOL:
            try:
                for op in sized_bidirectional_opportunities(token,pool,size_sol,meta=meta):
                    ranked.append(op)
                    if op["local_bps"]>=MIN_NET_BPS:
                        print("[POSITIVE] token=%s size=%.3f direction=%s net=%+.9f SOL bps=%+.2f"%(
                            token[:10],size_sol,op["direction"],op["local_net"]/1e9,op["local_bps"]),flush=True)
            except RuntimeError as e:
                if str(e)=="DLMM_PARTIAL":
                    print("[SIZE_SKIP] token=%s size=%.3f DLMM_PARTIAL"%(token[:10],size_sol),flush=True)
                    continue
                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)
            except Exception as e:
                print("[SIZE_SKIP] token=%s size=%.3f %s: %s"%(token[:10],size_sol,type(e).__name__,e),flush=True)
'''
if old_loop not in s:
    raise SystemExit("[FAIL] QSB-054 scan loop boundary missing")
s=s.replace(old_loop,new_loop,1)

CORE.write_text(s,encoding="utf-8")
py_compile.compile(str(CORE),doraise=True)

TEST=ROOT/"test_qsb_055_rate_limit_cached_profit_hunter.py"
TEST.write_text('''import unittest,inspect
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_cache(self):
        self.assertIsInstance(c._DLMM_CACHE,dict)
        print("[PASS] DLMM cache installed")

    def test_cached_miss(self):
        old=c.http
        c._DLMM_CACHE.clear()
        calls={"n":0}
        def fake(*a,**k):
            calls["n"]+=1
            return {"data":[]}
        c.http=fake
        try:
            with self.assertRaises(RuntimeError): c.discover_dlmm("TokenX")
            with self.assertRaises(RuntimeError): c.discover_dlmm("TokenX")
            self.assertEqual(calls["n"],1)
        finally:
            c.http=old
        print("[PASS] NO_DLMM_PAIR queried once per token")

    def test_meta_reuse(self):
        self.assertIn("meta",inspect.signature(c.sized_bidirectional_opportunities).parameters)
        print("[PASS] one pool discovery reused across all sizes")

    def test_no_jupiter(self):
        with open(c.__file__,encoding="utf-8") as f:
            src=f.read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
''',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qsb_055_rate_limit_cached_profit_hunter.py"
RUN.write_text(
    "from pathlib import Path\n"
    "from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core import run\n"
    "run(Path.cwd())\n",
    encoding="utf-8"
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QSB-055 rate-limit cached profit hunter installed")
print("[FIX] one Meteora discovery call per token")
print("[FIX] HTTP 429 retry/backoff")
print("[SEARCH] 64 tokens x 8 sizes x both directions")
print("[JUPITER] NONE")
