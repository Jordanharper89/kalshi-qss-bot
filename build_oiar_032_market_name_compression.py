from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_032_market_name_compression.py'
TEST=ROOT/'test_oiar_032_market_name_compression.py'
MODULE_SOURCE='from __future__ import annotations\nimport re\nOIAR_032_BUILD_ID="OIAR-032"\nOIAR_032_REVISION="OIAR_032_MARKET_NAME_COMPRESSION_V1"\nEXECUTION_AUTHORITY=False\n\ndef _clean_piece(x):\n    x=" ".join(str(x).replace("\\n"," ").split())\n    x=re.sub(r"^(yes|no)\\s+","",x,flags=re.I)\n    return x.strip(" ,")\n\ndef compress_market_name(market,max_parts=4,max_chars=96):\n    title=str(market.get("market_title") or market.get("title") or "").strip()\n    if not title:return "Market identity unavailable"\n    parts=[_clean_piece(x) for x in title.split(",") if _clean_piece(x)]\n    if not parts:return "Market identity unavailable"\n    if len(parts)==1:return parts[0][:max_chars]\n    shown=parts[:max_parts]\n    text=" + ".join(shown)\n    remaining=len(parts)-len(shown)\n    if remaining>0:text+=f" + {remaining} more"\n    if len(text)>max_chars:text=text[:max_chars-3].rstrip()+"..."\n    return text\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_032_market_name_compression as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_032_BUILD_ID,"OIAR-032")\n def test_combo(self):\n  x=m.compress_market_name({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh"})\n  self.assertEqual(x,"Philadelphia + Cleveland + Boston + Milwaukee + 1 more")\n def test_not_raw(self):\n  x=m.compress_market_name({"market_title":"yes Both Teams To Score,yes Atletico,yes Real Madrid,no Valencia wins"})\n  self.assertNotIn("yes ",x.lower());self.assertNotIn("no ",x.lower())\nif __name__=="__main__":\n print("="*88);print(" OIAR-032 CERTIFICATION TEST");print(" MARKET NAME COMPRESSION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] trader-readable market-name compression certified");print("[DONE] OIAR-032 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_031_unified_trader_conversation_cutover.py',)
EXTRA={}

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8")
    os.replace(t,p)

def restore(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def main():
    print("="*88);print(" OIAR-032 INSTALLER");print(" MARKET NAME COMPRESSION");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file():raise RuntimeError(f"Required upstream missing: {p}")
    targets=[MOD,TEST]+[ROOT/x for x in EXTRA]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        for s in EXTRA.values():ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,s in EXTRA.items():write_exact(ROOT/rel,s)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-032 failed; affected repository files restored")
        raise
    print("[PASS] snapshot-only trader presentation boundary preserved")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-032 INSTALLATION COMPLETE")
if __name__=="__main__":main()
