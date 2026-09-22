from __future__ import annotations
from dataclasses import dataclass
import re

from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class MarketTopicClassification:
    ticker:str
    primary_topic:str
    matched_signals:tuple[str,...]
    confidence_tier:str

def _text(m):
    return " ".join(str(m.get(k,"") or "") for k in (
        "ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"
    )).lower()

def _tokens(text):
    return tuple(re.findall(r"[a-z0-9]+",text.lower()))

def _contains_phrase(text,phrase):
    return bool(re.search(r"(?<![a-z0-9])"+re.escape(phrase.lower())+r"(?![a-z0-9])",text.lower()))

def _hits(text,terms):
    return tuple(sorted(t for t in terms if _contains_phrase(text,t)))

TOPIC_TERMS={
 "crypto":("bitcoin","btc","ethereum","eth","solana","crypto","cryptocurrency"),
 "macroeconomics":("cpi","inflation","gdp","unemployment","payrolls","jobs report","federal reserve","fed rate","interest rate","pce"),
 "politics_elections":("election","president","presidential","senate","senator","governor","primary election","electoral"),
 "corporate_finance":("earnings","revenue","eps","sec filing","ipo","acquisition","merger"),
 "energy_commodities":("crude oil","oil price","natural gas","gasoline","gold price","corn","wheat","soybean"),
 "legal_regulatory":("supreme court","court ruling","lawsuit","regulation","regulatory","tariff","sanction","federal register"),
 "health":("cdc","fda","disease","outbreak","vaccine","hospitalization"),
 "transport":("faa","flight","airport","tsa","shipping","port","rail","train"),
 "science_space":("nasa","spacex","rocket","launch","asteroid","spacecraft"),
 "geopolitics":("ceasefire","war","invasion","military","nato","treaty"),
}

SPORT_TERMS=(" vs "," versus ","match","game","tournament","nba","nfl","mlb","nhl","wnba","atp","wta","ufc","touchdown","runs scored","goals")
WEATHER_STRONG=("hurricane","tornado","flood","rainfall","temperature","snowfall","blizzard","heat wave","wind speed","weather")
WEATHER_STORM_CONTEXT=("tropical storm","winter storm","storm warning","storm watch","storm surge")

def classify_market_topic(m):
    text=_text(m)
    ticker=str(m.get("ticker",""))
    candidates=[]

    sport_hits=tuple(sorted(x.strip() for x in SPORT_TERMS if x in text))
    if sport_hits:
        candidates.append(("sports",sport_hits,3))

    weather_hits=tuple(sorted(set(_hits(text,WEATHER_STRONG)+_hits(text,WEATHER_STORM_CONTEXT))))
    if weather_hits:
        candidates.append(("weather",weather_hits,3))

    for topic,terms in TOPIC_TERMS.items():
        h=_hits(text,terms)
        if h:
            candidates.append((topic,h,2 if len(h)==1 else 3))

    if not candidates:
        return MarketTopicClassification(ticker,"other",(),"UNCLASSIFIED")

    # Prefer the highest evidence score, then most signals, then deterministic topic name.
    candidates.sort(key=lambda x:(-x[2],-len(x[1]),x[0]))
    topic,hits,score=candidates[0]
    return MarketTopicClassification(ticker,topic,tuple(semantic_key(x) for x in hits),"HIGH" if score>=3 else "MEDIUM")

def classify_market_cohort(markets):
    return tuple(classify_market_topic(m) for m in markets)

def verify_oad_076_false_positive_guards():
    # "Storm" as a surname must not make a weather market.
    a=classify_market_topic({"ticker":"X","title":"Lloyd Storm vs Frances Tiafoe"})
    b=classify_market_topic({"ticker":"Y","title":"Will a tropical storm make landfall in Florida?"})
    return a.primary_topic=="sports" and b.primary_topic=="weather"
