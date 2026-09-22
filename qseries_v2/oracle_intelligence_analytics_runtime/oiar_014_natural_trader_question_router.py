OIAR_014_BUILD_ID="OIAR-014"
TOKENS=("what do you like","best markets","best 5","best five","anything worth","anything moving","what should i watch","show me crypto","show me bitcoin","show me btc","show me sports","what does oracle know best","historically proven","live opportunities","rank trader intelligence","learned markets","worth trading","edge right now")
def normalize(q):return " ".join(str(q or "").lower().split())
def is_trader_brief_query(q):return any(t in normalize(q) for t in TOKENS)
def trader_query_filter(q):
 n=normalize(q)
 if "bitcoin" in n or "btc" in n or "crypto" in n:return "crypto"
 if "sport" in n:return "sports"
 return None
