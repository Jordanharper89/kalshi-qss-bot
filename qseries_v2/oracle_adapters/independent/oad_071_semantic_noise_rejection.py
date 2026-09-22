from __future__ import annotations
import re
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import semantic_key
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
WEAK_TERMS=frozenset({
 "new","latest","update","updated","active","open","closed","market","markets","will","would","could","should",
 "today","tomorrow","yesterday","week","month","year","event","events","document","documents","alert","alerts",
 "state","states","federal","register","weather","earthquake","earthquakes","united","official","current",
})
def semantic_tokens(value):
    toks=[semantic_key(x) for x in re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}",str(value or ""))]
    return tuple(sorted({x for x in toks if x and x not in WEAK_TERMS and len(x)>=3}))
def strong_phrases(value):
    words=semantic_tokens(value)
    out=set(words)
    for n in (2,3):
        for i in range(max(0,len(words)-n+1)):
            phrase="-".join(words[i:i+n])
            if phrase and not any(x in WEAK_TERMS for x in words[i:i+n]): out.add(phrase)
    return tuple(sorted(out))
def verify_oad_071():
    return "new" not in semantic_tokens("new federal update") and "bitcoin" in semantic_tokens("Bitcoin price")
