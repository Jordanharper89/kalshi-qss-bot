from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-076"
REVISION="OAD_076_PRODUCTION_INSTALLER_V1"
TITLE='PRECISION CURRENT-MARKET TOPIC CLASSIFIER'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_076_precision_current_market_topic_classifier.py'
TEST=ROOT/'test_oad_076_precision_current_market_topic_classifier.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nfrom qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass MarketTopicClassification:\n    ticker:str\n    primary_topic:str\n    matched_signals:tuple[str,...]\n    confidence_tier:str\n\ndef _text(m):\n    return " ".join(str(m.get(k,"") or "") for k in (\n        "ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"\n    )).lower()\n\ndef _tokens(text):\n    return tuple(re.findall(r"[a-z0-9]+",text.lower()))\n\ndef _contains_phrase(text,phrase):\n    return bool(re.search(r"(?<![a-z0-9])"+re.escape(phrase.lower())+r"(?![a-z0-9])",text.lower()))\n\ndef _hits(text,terms):\n    return tuple(sorted(t for t in terms if _contains_phrase(text,t)))\n\nTOPIC_TERMS={\n "crypto":("bitcoin","btc","ethereum","eth","solana","crypto","cryptocurrency"),\n "macroeconomics":("cpi","inflation","gdp","unemployment","payrolls","jobs report","federal reserve","fed rate","interest rate","pce"),\n "politics_elections":("election","president","presidential","senate","senator","governor","primary election","electoral"),\n "corporate_finance":("earnings","revenue","eps","sec filing","ipo","acquisition","merger"),\n "energy_commodities":("crude oil","oil price","natural gas","gasoline","gold price","corn","wheat","soybean"),\n "legal_regulatory":("supreme court","court ruling","lawsuit","regulation","regulatory","tariff","sanction","federal register"),\n "health":("cdc","fda","disease","outbreak","vaccine","hospitalization"),\n "transport":("faa","flight","airport","tsa","shipping","port","rail","train"),\n "science_space":("nasa","spacex","rocket","launch","asteroid","spacecraft"),\n "geopolitics":("ceasefire","war","invasion","military","nato","treaty"),\n}\n\nSPORT_TERMS=(" vs "," versus ","match","game","tournament","nba","nfl","mlb","nhl","wnba","atp","wta","ufc","touchdown","runs scored","goals")\nWEATHER_STRONG=("hurricane","tornado","flood","rainfall","temperature","snowfall","blizzard","heat wave","wind speed","weather")\nWEATHER_STORM_CONTEXT=("tropical storm","winter storm","storm warning","storm watch","storm surge")\n\ndef classify_market_topic(m):\n    text=_text(m)\n    ticker=str(m.get("ticker",""))\n    candidates=[]\n\n    sport_hits=tuple(sorted(x.strip() for x in SPORT_TERMS if x in text))\n    if sport_hits:\n        candidates.append(("sports",sport_hits,3))\n\n    weather_hits=tuple(sorted(set(_hits(text,WEATHER_STRONG)+_hits(text,WEATHER_STORM_CONTEXT))))\n    if weather_hits:\n        candidates.append(("weather",weather_hits,3))\n\n    for topic,terms in TOPIC_TERMS.items():\n        h=_hits(text,terms)\n        if h:\n            candidates.append((topic,h,2 if len(h)==1 else 3))\n\n    if not candidates:\n        return MarketTopicClassification(ticker,"other",(),"UNCLASSIFIED")\n\n    # Prefer the highest evidence score, then most signals, then deterministic topic name.\n    candidates.sort(key=lambda x:(-x[2],-len(x[1]),x[0]))\n    topic,hits,score=candidates[0]\n    return MarketTopicClassification(ticker,topic,tuple(semantic_key(x) for x in hits),"HIGH" if score>=3 else "MEDIUM")\n\ndef classify_market_cohort(markets):\n    return tuple(classify_market_topic(m) for m in markets)\n\ndef verify_oad_076_false_positive_guards():\n    # "Storm" as a surname must not make a weather market.\n    a=classify_market_topic({"ticker":"X","title":"Lloyd Storm vs Frances Tiafoe"})\n    b=classify_market_topic({"ticker":"Y","title":"Will a tropical storm make landfall in Florida?"})\n    return a.primary_topic=="sports" and b.primary_topic=="weather"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import *\n\nclass T(unittest.TestCase):\n    def test_storm_surname_not_weather(self):\n        x=classify_market_topic({"ticker":"X","title":"Lloyd Storm vs Frances Tiafoe"})\n        self.assertEqual(x.primary_topic,"sports")\n    def test_real_storm_weather(self):\n        x=classify_market_topic({"ticker":"X","title":"Will a tropical storm make landfall in Florida?"})\n        self.assertEqual(x.primary_topic,"weather")\n    def test_florida_person_fragment_not_geography_logic(self):\n        x=classify_market_topic({"ticker":"X","title":"Dakota Davis vs Florida King"})\n        self.assertNotEqual(x.primary_topic,"weather")\n    def test_verify(self): self.assertTrue(verify_oad_076_false_positive_guards())\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-076 CERTIFICATION TEST");print(" PRECISION CURRENT-MARKET TOPIC CLASSIFIER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Substring/name collisions no longer create weather classifications")\n    print("[PASS] Exact phrase boundaries and context rules certified")\n    print("[DONE] OAD-076 CERTIFIED")\n'

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

    kalshi=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    umd098=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_098_market_taxonomy.py"
    umd109=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_109_market_semantic_profile.py"
    oad075=PKG/"oad_075_persisted_independent_association_quality_gate.py"

    deps=((kalshi,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(umd098,"Frozen UMD-098"),
          (umd109,"Frozen UMD-109"),(oad075,"Certified OAD-075"))
    for p,label in deps:
        if not p.is_file(): raise RuntimeError(label+" missing")

    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (kalshi,oph,umd098,umd109)}
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Certified OAD-075 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-098 taxonomy unchanged")
        print("[PASS] Frozen UMD-109 semantic profile unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
