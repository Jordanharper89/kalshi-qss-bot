from __future__ import annotations
from .persistence import read_json,write_json
class Ledger:
    def __init__(self,path):
        self.path=path;self.data=read_json(path,{"observed_cycles":[],"target_transactions":[]})
        self.seen={x["fingerprint"] for x in self.data["observed_cycles"]}
    def add_cycle(self,o,slot):
        fp=str((slot,o["anchor"],tuple((x["signature"],x["src"],x["dst"]) for x in o["route"])))
        if fp in self.seen:return False
        self.seen.add(fp);self.data["observed_cycles"].append({
          "fingerprint":fp,"slot":int(slot),"anchor":o["anchor"],"hops":o["hops"],"net_bps":o["net_bps"],
          "venues":o["venues"],"classification":"OBSERVED_BLOCK_ARB_PATTERN",
          "actionable_live_quote":False,"paper_only":True,"execution_authority":False})
        self.data["observed_cycles"]=self.data["observed_cycles"][-10000:];return True
    def add_targets(self,rows):
        self.data["target_transactions"].extend(rows);self.data["target_transactions"]=self.data["target_transactions"][-5000:]
    def save(self):return write_json(self.path,self.data)
