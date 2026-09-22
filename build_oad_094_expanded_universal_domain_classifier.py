from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-094";REVISION="OAD_094_PRODUCTION_INSTALLER_V1";TITLE='EXPANDED UNIVERSAL DOMAIN CLASSIFIER'
def find_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root();PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_094_expanded_universal_domain_classifier.py';TEST=ROOT/'test_oad_094_expanded_universal_domain_classifier.py';INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import deep_classify_market\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass ExpandedDomain:\n ticker:str;domain:str;evidence:tuple[str,...]\nDOMAIN_TERMS={\n "macroeconomics":("inflation","cpi","gdp","unemployment","jobs","payroll","interest rate","federal reserve","fed funds","treasury yield"),\n "politics_elections":("election","president","senate","house of representatives","governor","approval rating","primary","electoral"),\n "corporate_finance":("earnings","revenue","eps","ipo","merger","acquisition","market cap","stock price","sec filing"),\n "crypto":("bitcoin","ethereum","solana","crypto","btc","eth"),\n "weather":("hurricane","tornado","rainfall","snowfall","temperature","flood","tropical storm"),\n "energy_commodities":("crude oil","natural gas","gasoline","gold","silver","wheat","corn","soybean"),\n "legal_regulatory":("supreme court","court ruling","lawsuit","indictment","regulation","tariff","sanction"),\n "health":("cdc","fda","vaccine","outbreak","disease","drug approval"),\n "transport":("faa","tsa","airport","flight","shipping","port","rail"),\n "science_space":("nasa","rocket","spacecraft","asteroid","moon","mars"),\n "geopolitics":("ceasefire","nato","invasion","military","peace deal","treaty"),\n "technology":("openai","artificial intelligence","ai model","iphone","android","semiconductor","chip"),\n "entertainment_awards":("oscar","grammy","emmy","box office","album","movie","billboard"),\n}\ndef expanded_domain_classify(m):\n b=deep_classify_market(m)\n if b.topic!="other":return ExpandedDomain(b.ticker,b.topic,b.evidence)\n if detect_sports_market(m).is_sports:return ExpandedDomain(str(m.get("ticker","")),"sports",("structural_sports",))\n text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()\n hits=[]\n for d,terms in DOMAIN_TERMS.items():\n  found=tuple(x for x in terms if x in text)\n  if found:hits.append((len(found),d,found))\n if not hits:return ExpandedDomain(str(m.get("ticker","")),"other",())\n hits.sort(key=lambda x:(-x[0],x[1]));_,d,found=hits[0]\n return ExpandedDomain(str(m.get("ticker","")),d,found)\n';TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import *\nclass T(unittest.TestCase):\n def test_macro(self):self.assertEqual(expanded_domain_classify({"title":"Will CPI inflation exceed 3%?"}).domain,"macroeconomics")\n def test_crypto(self):self.assertEqual(expanded_domain_classify({"title":"Will Bitcoin exceed $100k?"}).domain,"crypto")\n def test_unknown(self):self.assertEqual(expanded_domain_classify({"title":"Unrecognized proposition"}).domain,"other")\nif __name__=="__main__":\n print("="*88);print(" OAD-094 CERTIFICATION TEST");print(" EXPANDED UNIVERSAL DOMAIN CLASSIFIER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Expanded non-sports domain classification certified");print("[DONE] OAD-094 CERTIFIED")\n';FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')];REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_093_remaining_other_domain_audit.py', 'Certified OAD-093')]
def write(p,s):
    s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p));p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88);print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        if not (ROOT/rel).is_file():raise RuntimeError(label+" missing")
        print("[PASS]",label,"verified")
    frozen={ROOT/r:hashlib.sha256((ROOT/r).read_bytes()).hexdigest() for r,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE);write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged");print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
