from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import re

from qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_topic
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class DeepTopicClassification:
    ticker:str
    topic:str
    evidence:tuple[str,...]
    tier:str

FIELDS=("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")

PHRASES={
 "crypto":("bitcoin","ethereum","solana","crypto","btc","eth"),
 "macroeconomics":("consumer price index","cpi","inflation","gross domestic product","gdp","unemployment","nonfarm payroll","jobs report","federal reserve","fed funds","interest rate","pce"),
 "politics_elections":("election","presidential","president","senate","senator","governor","primary","electoral college","congress"),
 "corporate_finance":("earnings","revenue","eps","sec filing","ipo","merger","acquisition","stock price","market cap"),
 "energy_commodities":("crude oil","natural gas","gasoline","wti","brent","gold","silver","corn","wheat","soybean"),
 "legal_regulatory":("supreme court","court","lawsuit","indictment","regulation","regulatory","tariff","sanction","federal register"),
 "health":("cdc","fda","outbreak","vaccine","hospitalization","disease","drug approval"),
 "transport":("faa","tsa","airport","flight","shipping","port","rail","train"),
 "science_space":("nasa","spacex","rocket","launch","asteroid","spacecraft","moon","mars"),
 "geopolitics":("ceasefire","invasion","military","nato","treaty","war","peace deal"),
 "entertainment_awards":("oscar","academy awards","grammy","emmy","golden globe","box office","billboard","album","movie"),
 "technology":("apple","google","microsoft","openai","nvidia","ai model","iphone","android"),
 "weather":("hurricane","tornado","flood","rainfall","snowfall","temperature","blizzard","heat wave","wind speed","tropical storm"),
}

def _text(m):
    return " ".join(str(m.get(k,"") or "") for k in FIELDS).lower()

def _boundary_hit(text,p):
    return bool(re.search(r"(?<![a-z0-9])"+re.escape(p.lower())+r"(?![a-z0-9])",text))

def deep_classify_market(m):
    base=classify_market_topic(m)
    if base.primary_topic!="other":
        return DeepTopicClassification(base.ticker,base.primary_topic,base.matched_signals,"BASE_HIGH")
    text=_text(m)
    hits=[]
    for topic,phrases in PHRASES.items():
        found=tuple(sorted(p for p in phrases if _boundary_hit(text,p)))
        if found:
            hits.append((topic,found))
    if not hits:
        return DeepTopicClassification(str(m.get("ticker","")),"other",(),"UNRESOLVED")
    hits.sort(key=lambda x:(-len(x[1]),x[0]))
    topic,found=hits[0]
    return DeepTopicClassification(str(m.get("ticker","")),topic,found,"DEEP")

def classify_snapshot(snapshot):
    rows=tuple(deep_classify_market(m) for m in snapshot_markets(snapshot))
    counts=Counter(x.topic for x in rows)
    return rows,tuple(sorted(counts.items(),key=lambda kv:(-kv[1],kv[0])))
