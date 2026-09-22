from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-086"; REVISION="OAD_086_PRODUCTION_INSTALLER_V1"; TITLE='STRUCTURAL SPORTS MARKET DETECTOR'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_086_structural_sports_market_detector.py'; TEST=ROOT/'test_oad_086_structural_sports_market_detector.py'; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass SportsDetection:\n    ticker:str; is_sports:bool; signals:tuple[str,...]; confidence:str\n\nSPORT_STRUCTURE=(\n "both teams to score","wins by over","points scored","runs scored","goals scored",\n "1st half","first half","set betting","game spread","total points","total runs",\n "moneyline","touchdown","home runs","strikeouts","assists","rebounds","yards",\n "round of 16","quarterfinal","semifinal","final","to win","vs","versus"\n)\nSPORT_SERIES_MARKERS=("NFL","NBA","WNBA","MLB","NHL","NCAAF","NCAAB","ATP","WTA","UFC","MMA","SOCCER","TENNIS","BOXING")\n\ndef _fields(m):\n    return " ".join(str(m.get(k,"") or "") for k in (\n      "ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary"\n    ))\ndef _hit(text,phrase):\n    return bool(re.search(r"(?<![a-z0-9])"+re.escape(phrase.lower())+r"(?![a-z0-9])",text.lower()))\ndef detect_sports_market(m):\n    text=_fields(m); upper=text.upper(); sig=[]\n    for x in SPORT_STRUCTURE:\n        if _hit(text,x): sig.append("structure:"+x)\n    for x in SPORT_SERIES_MARKERS:\n        if re.search(r"(?<![A-Z0-9])"+re.escape(x)+r"(?![A-Z0-9])",upper): sig.append("series:"+x)\n    # Cross-category shards often contain comma-separated yes/no legs. Sports structure within a leg is valid evidence.\n    yesno=len(re.findall(r"(?<![a-z])(yes|no)(?![a-z])",text.lower()))\n    if yesno>=2 and any(k in text.lower() for k in (" points"," runs"," score"," wins by"," vs "," versus ")):\n        sig.append("multi_leg_sports_structure")\n    sig=tuple(sorted(set(sig)))\n    return SportsDetection(str(m.get("ticker","")),bool(sig),sig,"HIGH" if len(sig)>=2 else ("MEDIUM" if sig else "NONE"))\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import *\nclass T(unittest.TestCase):\n def test_prop(self): self.assertTrue(detect_sports_market({"title":"yes Rafael Devers: 1+, no Corbin Carroll: 5+","rules_primary":"runs"}).is_sports)\n def test_btts(self): self.assertTrue(detect_sports_market({"title":"1st Half: Both Teams To Score"}).is_sports)\n def test_non_sport(self): self.assertFalse(detect_sports_market({"title":"Will CPI inflation exceed 3 percent?"}).is_sports)\nif __name__=="__main__":\n print("="*88);print(" OAD-086 CERTIFICATION TEST");print(" STRUCTURAL SPORTS MARKET DETECTOR");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Sports detected from market structure without athlete/team dictionaries");print("[DONE] OAD-086 CERTIFIED")\n'
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]; REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_085_single_snapshot_adapter_priority_gate.py', 'Certified OAD-085')]
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        if not (ROOT/rel).is_file(): raise RuntimeError(label+" missing")
        print("[PASS]",label,"verified")
    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
