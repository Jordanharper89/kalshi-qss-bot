from __future__ import annotations
import re
OIAR_035_BUILD_ID="OIAR-035"
OIAR_035_REVISION="OIAR_035_CONVERSATIONAL_FOLLOWUP_RESOLUTION_V1"
EXECUTION_AUTHORITY=False
FOLLOWUP_PATTERNS=(
 "is this for today","is that for today","is this today","is that today",
 "what about the first one","what about the second one","what about the third one",
 "why","why that one","anything better","what's the risk","whats the risk","what is the risk",
)
def classify_followup(query):
    q=" ".join(str(query).lower().split()).strip(" ?")
    if q in FOLLOWUP_PATTERNS:return True
    if re.match(r"^(what about|how about) (the )?(first|second|third|#?[123])",q):return True
    return False
def ordinal_index(query):
    q=str(query).lower()
    if "first" in q or "#1" in q:return 0
    if "second" in q or "#2" in q:return 1
    if "third" in q or "#3" in q:return 2
    return None
def followup_kind(query):
    q=" ".join(str(query).lower().split())
    if "today" in q:return "time"
    if "risk" in q:return "risk"
    if q.startswith("why"):return "why"
    if "better" in q:return "better"
    if ordinal_index(q) is not None:return "market"
    return "context"
