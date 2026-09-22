from __future__ import annotations
import hashlib,json
from pathlib import Path

ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

NAMES=("buy","sell","buy_exact_sol_in")
REGISTRY={hashlib.sha256(("global:"+n).encode()).digest()[:8].hex():n for n in NAMES}

def b58decode(s):
 n=0
 for c in s:n=n*58+ALPHABET.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def classify(data):
 raw=b58decode(data or "")
 disc=raw[:8].hex() if len(raw)>=8 else None
 name=REGISTRY.get(disc)
 side="BUY" if name in ("buy","buy_exact_sol_in") else ("SELL" if name=="sell" else "UNKNOWN_TRADE_TYPE")
 return {"discriminator_hex":disc,"instruction_name":name,"side":side,
  "decoder_state":"EXACT_DISCRIMINATOR" if name else "UNKNOWN_DISCRIMINATOR"}

def write(root):
 d={"revision":"USLS_031","program_id":PUMP,"registry":REGISTRY,
  "unknown_retention":True,"execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_discriminator_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
