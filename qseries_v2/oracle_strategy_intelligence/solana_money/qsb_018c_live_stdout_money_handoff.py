
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict

READ_ONLY = True
EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REVISION = "QSB_018C_LIVE_STDOUT_MONEY_HANDOFF_V1"

FAST_PREFIX = "[FAST ENTRIES]"
MONEY_PREFIX = "[FRESH MONEY]"
BURST_PREFIX = "[BURST]"
FAMILIES_PREFIX = "[FAMILIES]"

@dataclass(frozen=True)
class FastEntry:
    family: str
    token: str
    score: float
    liquidity_usd: float
    def to_dict(self): return asdict(self)

def parse_fast_entries(line: str):
    if FAST_PREFIX not in line:
        return ()
    payload=line.split(FAST_PREFIX,1)[1].strip()
    try:
        rows=json.loads(payload)
    except Exception:
        return ()
    out=[]
    if isinstance(rows,list):
        for r in rows:
            if not isinstance(r,dict):
                continue
            token=str(r.get("token") or "").strip()
            if not token:
                continue
            try: score=float(r.get("score",0.0))
            except Exception: score=0.0
            try: liq=float(r.get("liq",0.0))
            except Exception: liq=0.0
            out.append(FastEntry(str(r.get("family") or "UNKNOWN"),token,score,liq))
    return tuple(out)

def parse_fresh_money(line: str):
    if MONEY_PREFIX not in line:
        return None
    def grab(name, cast=float):
        m=re.search(r"\b"+re.escape(name)+r"=([^\s]+)",line)
        if not m: return None
        raw=m.group(1).replace("$","")
        if raw=="None": return None
        try: return cast(raw)
        except Exception: return None
    return {
        "closed": grab("closed",int),
        "wins": grab("wins",int),
        "losses": grab("losses",int),
        "win_rate": grab("win_rate",float),
        "net": grab("NET",float),
    }

def qualifies_existing_qsb015_entry(entry: FastEntry):
    # Do not invent a second strategy. Respect QSB-015's own live entry;
    # only reject malformed / non-executable rows.
    return bool(entry.token and entry.score > 0 and entry.liquidity_usd > 0)
