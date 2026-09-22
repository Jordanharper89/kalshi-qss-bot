from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
BUILD_ID="OAD-069"
REVISION="OAD_069_PRODUCTION_INSTALLER_V1"
TITLE='CURRENT OPEN KALSHI BOUNDED MARKET INDEX'
def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_069_current_open_kalshi_market_index.py'
TEST=ROOT/'test_oad_069_current_open_kalshi_market_index.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nimport re\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\nSTOP={"the","and","for","with","will","what","when","from","this","that","yes","no","market"}\ndef _terms(m):\n    text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title"))\n    return tuple(sorted({w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}",text) if w.lower() not in STOP}))\ndef fetch_current_open_kalshi_market_index(root=None,limit=1000,timeout_seconds=20):\n    limit=max(1,min(int(limit),1000))\n    cred=load_kalshi_credentials(root=Path(root or Path.cwd()).resolve())\n    r=kalshi_rest_get(cred,"/markets",{"limit":limit,"status":"open"},timeout_seconds)\n    if r.status_code!=200: raise RuntimeError("Kalshi current-market request failed")\n    markets=tuple(r.body.get("markets",()))\n    index={}\n    for m in markets:\n        ticker=str(m.get("ticker","")).strip()\n        if ticker:index[ticker]=_terms(m)\n    return markets,index\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        markets,index=fetch_current_open_kalshi_market_index(limit=1000)\n        print("[PHYSICAL] current_open_markets=",len(markets));print("[PHYSICAL] indexed_markets=",len(index))\n        self.assertGreater(len(markets),0);self.assertLessEqual(len(markets),1000)\nif __name__=="__main__":\n    print("="*88);print(" OAD-069 PHYSICAL CERTIFICATION TEST");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Real current open Kalshi market page indexed read-only");print("[DONE] OAD-069 CERTIFIED")\n'
def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    dep=PKG/"oad_065_independent_canonical_batch_gate.py"
    for p,label in ((freeze,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(dep,"Certified OAD-065")):
        if not p.is_file(): raise RuntimeError(label+" dependency missing")
    freeze_hash=hashlib.sha256(freeze.read_bytes()).hexdigest()
    oph_hash=hashlib.sha256(oph.read_bytes()).hexdigest()
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        if hashlib.sha256(freeze.read_bytes()).hexdigest()!=freeze_hash: raise RuntimeError("Frozen Kalshi OAD-055 changed")
        if hashlib.sha256(oph.read_bytes()).hexdigest()!=oph_hash: raise RuntimeError("Frozen OPH-023 changed")
        print("[PASS] Certified OAD-065 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 single-writer boundary unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__": main()
