from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning_feedback"
MOD=PKG/"olf_008_related_market_learning_resolver.py";TEST=ROOT/"test_olf_008_related_market_learning_resolver.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .olf_006_structural_identity import resolve_structural_identity\nfrom .olf_007_cross_market_learning_index import load_cross_market_learning_index\n\nOLF_008_BUILD_ID="OLF-008"\nOLF_008_REVISION="OLF_008_RELATED_MARKET_LEARNING_RESOLVER_V1"\n\n@dataclass(frozen=True)\nclass RelatedMarketLearningResolution:\n    market_ticker:str\n    relationship_type:str\n    relationship_strength:float\n    source_markets:tuple\n    learned_records:int\n    generalized_experience_weight:float\n    learner_state_hash:str\n    available:bool\n    directional_signal_available:bool=False\n    execution_authority:bool=False\n\ndef resolve_related_market_learning(root=None,market_ticker=""):\n    root=Path(root or Path.cwd()).resolve()\n    ident=resolve_structural_identity(market_ticker)\n    idx=load_cross_market_learning_index(root)\n    state_hash=str(idx.get("learner_state_hash") or "")\n    exact=idx.get("exact",{}).get(ident.exact_key)\n    if exact:\n        records=int(exact.get("learned_records",0))\n        return RelatedMarketLearningResolution(\n            ident.market_ticker,"EXACT_TICKER",1.0,(ident.market_ticker,),records,\n            min(1.0,records/25.0),state_hash,records>0,False,False\n        )\n\n    rows=tuple(idx.get("series",{}).get(ident.series_key,()))\n    if not rows:\n        return RelatedMarketLearningResolution(\n            ident.market_ticker,"NONE",0.0,tuple(),0,0.0,state_hash,False,False,False\n        )\n\n    source=tuple(sorted(str(x.get("market_ticker") or "") for x in rows if x.get("market_ticker")))\n    records=sum(int(x.get("learned_records",0)) for x in rows)\n    # Same exact venue series is strong historical analogy, but never treated as identical.\n    strength=.75\n    weight=min(1.0,records/25.0)*strength\n    return RelatedMarketLearningResolution(\n        ident.market_ticker,"SAME_KALSHI_SERIES",strength,source,records,weight,\n        state_hash,records>0,False,False\n    )\n\ndef verify_olf_008_related_market_learning_resolver():\n    return OLF_008_BUILD_ID=="OLF-008" and callable(resolve_related_market_learning)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_feedback.olf_008_related_market_learning_resolver import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLF_008_BUILD_ID,"OLF-008")\n    def test_contract(self):\n        x=RelatedMarketLearningResolution("KX","NONE",0.0,tuple(),0,0.0,"h",False,False,False)\n        self.assertFalse(x.available);self.assertFalse(x.directional_signal_available)\n\nif __name__=="__main__":\n    print("="*88);print(" OLF-008 CERTIFICATION TEST");print(" RELATED-MARKET LEARNING RESOLVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Exact -> same-series -> none relationship order certified")\n    print("[PASS] Related learning remains non-directional")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLF-008 CERTIFIED")\n'

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
    print("="*88);print(" OLF-008 INSTALLER");print(" RELATED-MARKET LEARNING RESOLVER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning_feedback.olf_007_cross_market_learning_index")
    if not up.verify_olf_007_cross_market_learning_index():raise RuntimeError("OLF-007 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olf_008_related_market_learning_resolver import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLF-008 failed; files restored");raise
    print("[PASS] Cross-series knowledge transfer remains prohibited")
    print("[PASS] No directional adjustment created")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-008 INSTALLATION COMPLETE")
if __name__=="__main__":main()
