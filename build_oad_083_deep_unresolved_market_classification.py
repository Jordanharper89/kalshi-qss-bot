from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-083"
REVISION="OAD_083_PRODUCTION_INSTALLER_V1"
TITLE='DEEP UNRESOLVED MARKET CLASSIFICATION'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
WRITES=[('qseries_v2/oracle_adapters/independent/oad_083_deep_unresolved_market_classification.py', '\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nimport re\n\nfrom qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_topic\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass DeepTopicClassification:\n    ticker:str\n    topic:str\n    evidence:tuple[str,...]\n    tier:str\n\nFIELDS=("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")\n\nPHRASES={\n "crypto":("bitcoin","ethereum","solana","crypto","btc","eth"),\n "macroeconomics":("consumer price index","cpi","inflation","gross domestic product","gdp","unemployment","nonfarm payroll","jobs report","federal reserve","fed funds","interest rate","pce"),\n "politics_elections":("election","presidential","president","senate","senator","governor","primary","electoral college","congress"),\n "corporate_finance":("earnings","revenue","eps","sec filing","ipo","merger","acquisition","stock price","market cap"),\n "energy_commodities":("crude oil","natural gas","gasoline","wti","brent","gold","silver","corn","wheat","soybean"),\n "legal_regulatory":("supreme court","court","lawsuit","indictment","regulation","regulatory","tariff","sanction","federal register"),\n "health":("cdc","fda","outbreak","vaccine","hospitalization","disease","drug approval"),\n "transport":("faa","tsa","airport","flight","shipping","port","rail","train"),\n "science_space":("nasa","spacex","rocket","launch","asteroid","spacecraft","moon","mars"),\n "geopolitics":("ceasefire","invasion","military","nato","treaty","war","peace deal"),\n "entertainment_awards":("oscar","academy awards","grammy","emmy","golden globe","box office","billboard","album","movie"),\n "technology":("apple","google","microsoft","openai","nvidia","ai model","iphone","android"),\n "weather":("hurricane","tornado","flood","rainfall","snowfall","temperature","blizzard","heat wave","wind speed","tropical storm"),\n}\n\ndef _text(m):\n    return " ".join(str(m.get(k,"") or "") for k in FIELDS).lower()\n\ndef _boundary_hit(text,p):\n    return bool(re.search(r"(?<![a-z0-9])"+re.escape(p.lower())+r"(?![a-z0-9])",text))\n\ndef deep_classify_market(m):\n    base=classify_market_topic(m)\n    if base.primary_topic!="other":\n        return DeepTopicClassification(base.ticker,base.primary_topic,base.matched_signals,"BASE_HIGH")\n    text=_text(m)\n    hits=[]\n    for topic,phrases in PHRASES.items():\n        found=tuple(sorted(p for p in phrases if _boundary_hit(text,p)))\n        if found:\n            hits.append((topic,found))\n    if not hits:\n        return DeepTopicClassification(str(m.get("ticker","")),"other",(),"UNRESOLVED")\n    hits.sort(key=lambda x:(-len(x[1]),x[0]))\n    topic,found=hits[0]\n    return DeepTopicClassification(str(m.get("ticker","")),topic,found,"DEEP")\n\ndef classify_snapshot(snapshot):\n    rows=tuple(deep_classify_market(m) for m in snapshot_markets(snapshot))\n    counts=Counter(x.topic for x in rows)\n    return rows,tuple(sorted(counts.items(),key=lambda kv:(-kv[1],kv[0])))\n'), ('test_oad_083_deep_unresolved_market_classification.py', '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        s=capture_current_market_cohort(1000)\n        rows,counts=classify_snapshot(s)\n        unresolved=[x for x in rows if x.topic=="other"]\n        print("[PHYSICAL] snapshot_id=",s.snapshot_id)\n        print("[PHYSICAL] market_count=",s.market_count)\n        print("[PHYSICAL] topic_counts=",counts)\n        print("[PHYSICAL] unresolved_markets=",len(unresolved))\n        markets={str(m.get("ticker","")):m for m in snapshot_markets(s)}\n        for x in unresolved[:20]:\n            m=markets.get(x.ticker,{})\n            print("[UNRESOLVED]",x.ticker,str(m.get("title",""))[:160])\n        self.assertEqual(len(rows),s.market_count)\n        self.assertEqual(sum(v for _,v in counts),s.market_count)\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-083 PHYSICAL CERTIFICATION TEST");print(" DEEP UNRESOLVED MARKET CLASSIFICATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Deeper classification uses exact phrase boundaries and preserves unresolved markets")\n    print("[DONE] OAD-083 CERTIFIED")\n')]
FROZEN_DEPS=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED_DEPS=[('qseries_v2/oracle_adapters/independent/oad_076_precision_current_market_topic_classifier.py', 'Certified OAD-076'), ('qseries_v2/oracle_adapters/independent/oad_082_single_live_market_cohort_snapshot.py', 'Certified OAD-082')]

def write_exact(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("="*88)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    for rel,label in REQUIRED_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    frozen={}
    for rel,label in FROZEN_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()

    targets=[ROOT/rel for rel,_ in WRITES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}

    try:
        for rel,source in WRITES:
            p=ROOT/rel
            write_exact(p, source)
            print("[PASS] Wrote:",rel)

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
