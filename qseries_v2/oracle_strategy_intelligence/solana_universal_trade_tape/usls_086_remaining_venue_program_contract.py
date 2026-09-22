from __future__ import annotations
import json
from pathlib import Path

PROGRAMS={
 "MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
}

def write(root):
 d={"revision":"USLS_086","programs":PROGRAMS,
  "policy":"PHYSICAL_DISCOVERY_FIRST_NO_UNVERIFIED_TRADE_DISCRIMINATORS",
  "unknown_instruction_retention":True,
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_program_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
