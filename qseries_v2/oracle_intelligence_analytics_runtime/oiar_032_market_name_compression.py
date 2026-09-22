from __future__ import annotations
import re
OIAR_032_BUILD_ID="OIAR-032"
OIAR_032_REVISION="OIAR_032_MARKET_NAME_COMPRESSION_V1"
EXECUTION_AUTHORITY=False

def _clean_piece(x):
    x=" ".join(str(x).replace("\n"," ").split())
    x=re.sub(r"^(yes|no)\s+","",x,flags=re.I)
    return x.strip(" ,")

def compress_market_name(market,max_parts=4,max_chars=96):
    title=str(market.get("market_title") or market.get("title") or "").strip()
    if not title:return "Market identity unavailable"
    parts=[_clean_piece(x) for x in title.split(",") if _clean_piece(x)]
    if not parts:return "Market identity unavailable"
    if len(parts)==1:return parts[0][:max_chars]
    shown=parts[:max_parts]
    text=" + ".join(shown)
    remaining=len(parts)-len(shown)
    if remaining>0:text+=f" + {remaining} more"
    if len(text)>max_chars:text=text[:max_chars-3].rstrip()+"..."
    return text
