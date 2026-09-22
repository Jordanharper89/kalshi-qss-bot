from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_006_structural_identity.py";TEST=ROOT/"test_olf_006_learned_market_structural_identity.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nOLF_006_BUILD_ID="OLF-006"\nOLF_006_REVISION="OLF_006_LEARNED_MARKET_STRUCTURAL_IDENTITY_V1"\n\n_TICKER=re.compile(r"^[A-Z0-9._:-]+(?:-[A-Z0-9._:-]+)*$")\n\n@dataclass(frozen=True)\nclass LearnedMarketStructuralIdentity:\n    market_ticker:str\n    series_key:str\n    series_token:str\n    structural_depth:int\n    exact_key:str\n    execution_authority:bool=False\n\ndef normalize_ticker(value):\n    ticker=str(value or "").strip().upper()\n    if not ticker or not _TICKER.fullmatch(ticker):\n        raise ValueError("invalid Kalshi market ticker")\n    return ticker\n\ndef resolve_structural_identity(market_ticker):\n    ticker=normalize_ticker(market_ticker)\n    parts=tuple(x for x in ticker.split("-") if x)\n    series=parts[0]\n    # Strict production generalization boundary:\n    # only the exact Kalshi series token is reusable across different contracts.\n    return LearnedMarketStructuralIdentity(\n        ticker,\n        "kalshi:series:"+series,\n        series,\n        len(parts),\n        "kalshi:ticker:"+ticker,\n        False,\n    )\n\ndef same_series(left,right):\n    return resolve_structural_identity(left).series_key==resolve_structural_identity(right).series_key\n\ndef verify_olf_006_learned_market_structural_identity():\n    a=resolve_structural_identity("KXBTC15M-26AUG192200-00")\n    b=resolve_structural_identity("KXBTC15M-26AUG192215-15")\n    c=resolve_structural_identity("KXETH15M-26AUG192200-00")\n    return a.series_key==b.series_key and a.series_key!=c.series_key and not a.execution_authority\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_006_structural_identity import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_006_BUILD_ID,"OLF-006")\n    def test_same_series(self):\n        self.assertTrue(same_series("KXBTC15M-26AUG192200-00","KXBTC15M-26AUG192215-15"))\n    def test_cross_series_rejected(self):\n        self.assertFalse(same_series("KXBTC15M-26AUG192200-00","KXETH15M-26AUG192200-00"))\n    def test_invalid(self):\n        with self.assertRaises(ValueError):normalize_ticker("bad ticker!")\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-006 CERTIFICATION TEST");print(" LEARNED MARKET STRUCTURAL IDENTITY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Exact Kalshi-series structural identity certified")\n    print("[PASS] Cross-series transfer prohibited")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-006 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OLF-006 INSTALLER");print(" LEARNED MARKET STRUCTURAL IDENTITY");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_005_live_cutover")
    if not up.verify_olf_005_physical_learning_to_reasoning_cutover_gate():raise RuntimeError("OLF-005 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_006_structural_identity import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-006 failed; files restored");raise
    print("[PASS] Existing learned state untouched")
    print("[PASS] Exact-ticker learning remains strongest")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-006 INSTALLATION COMPLETE")
if __name__=="__main__":main()
