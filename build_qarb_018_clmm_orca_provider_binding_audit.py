from pathlib import Path
import py_compile,json
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"native_provider_resolver.py").is_file(): raise SystemExit("[FAIL] QARB-017 missing")
SRC=r"""
from __future__ import annotations
import json
from pathlib import Path
from .native_provider_resolver import best

def audit(root):
    out={}
    for venue in ("RAYDIUM_CLMM","ORCA_WHIRLPOOL"):
        c=best(root,venue)
        out[venue]=None if c is None else {
          "module_path":c.module_path,"function":c.function,
          "score":c.score,"hot_io_free":c.hot_io_free,
        }
    return out

def write(root):
    root=Path(root);d=audit(root)
    p=root/"runtime_state/qseries/qarb_clean_bot/native_provider_binding_audit.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({"providers":d,"execution_authority":False},sort_keys=True,indent=2),encoding="utf-8")
    return d,p
"""
TEST=r"""
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.provider_binding_audit import *
class T(unittest.TestCase):
    def test_audit_truthfully_reports_absent(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,"qseries_v2").mkdir()
            d,p=write(td)
            self.assertIsNone(d["RAYDIUM_CLMM"]);self.assertIsNone(d["ORCA_WHIRLPOOL"]);self.assertTrue(p.exists())
        print("[PASS] provider audit fails closed instead of inventing CLMM/Orca math")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=SUB/"provider_binding_audit.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_018_clmm_orca_provider_binding_audit.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
RUN=ROOT/"run_qarb_018_clmm_orca_provider_binding_audit.py"
RUN.write_text("from pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.provider_binding_audit import write\nd,p=write(Path.cwd());print('[QARB-018]',d);print('[REPORT]',p)\n",encoding="utf-8");py_compile.compile(str(RUN),doraise=True)
print("[PASS] QARB-018 CLMM/Orca native-provider binding audit installed")
print("[TRUTH] writes exact found/absent result; no fake provider")
print("[MODE] execution_authority=FALSE")
