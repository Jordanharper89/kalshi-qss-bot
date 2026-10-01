from pathlib import Path
import py_compile
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"certified_roles.py").is_file(): raise SystemExit("[FAIL] QARB-016 missing")
SRC=r"""
from __future__ import annotations
import ast,importlib.util,inspect
from dataclasses import dataclass
from pathlib import Path

BAD=("requests","urllib","http(","rpc(","urlopen","jupiter","subprocess","sleep(")
VENUE_HINTS={
 "RAYDIUM_CLMM":("raydium","clmm"),
 "ORCA_WHIRLPOOL":("orca","whirl"),
}
FN_HINTS=("quote","swap_quote","quote_exact_in","compute_swap","simulate_swap")

@dataclass(frozen=True)
class Candidate:
    venue:str
    module_path:str
    function:str
    score:int
    hot_io_free:bool

def scan(root,venue):
    root=Path(root);hints=VENUE_HINTS[venue];rows=[]
    q=root/"qseries_v2"
    if not q.exists(): return rows
    for p in q.rglob("*.py"):
        low=str(p).lower()
        if not all(h in low for h in hints): continue
        try: src=p.read_text(encoding="utf-8");tree=ast.parse(src)
        except Exception: continue
        s=src.lower();iofree=not any(x in s for x in BAD)
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                name=n.name.lower()
                score=sum(4 for h in FN_HINTS if h in name)+sum(1 for h in hints if h in low)
                if score>=6:
                    rows.append(Candidate(venue,str(p.relative_to(root)),n.name,score,iofree))
    rows.sort(key=lambda x:(not x.hot_io_free,-x.score,x.module_path,x.function))
    return rows

def best(root,venue):
    rows=[x for x in scan(root,venue) if x.hot_io_free]
    return rows[0] if rows else None
"""
TEST=r"""
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.native_provider_resolver import *
class T(unittest.TestCase):
    def test_finds_local_provider(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"qseries_v2/x/raydium/clmm";p.mkdir(parents=True)
            (p/"local_math.py").write_text("def quote_exact_in(state,mint,amount):\n return amount\n",encoding="utf-8")
            x=best(td,"RAYDIUM_CLMM");self.assertIsNotNone(x);self.assertTrue(x.hot_io_free)
        print("[PASS] native local quote provider resolver finds I/O-free candidate")
    def test_rejects_http_source(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"qseries_v2/x/orca/whirlpool";p.mkdir(parents=True)
            (p/"bad.py").write_text("import urllib\ndef quote_exact_in(x): return urllib.request.urlopen('x')\n",encoding="utf-8")
            self.assertIsNone(best(td,"ORCA_WHIRLPOOL"))
        print("[PASS] resolver rejects network-dependent quote providers")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=SUB/"native_provider_resolver.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_017b_native_local_quote_provider_resolver_repair.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-017B native local quote provider resolver repair installed")
print("[RULE] CLMM/Orca provider candidates must be local and hot-I/O-free")
print("[MODE] execution_authority=FALSE")
