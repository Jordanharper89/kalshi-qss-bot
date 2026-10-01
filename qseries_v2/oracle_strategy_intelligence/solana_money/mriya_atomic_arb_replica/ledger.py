from __future__ import annotations
from .persistence import read_json,write_json
class OpportunityLedger:
    def __init__(self,path):
        self.path=path;self.data=read_json(path,{"opportunities":[]});self.seen={x["fingerprint"] for x in self.data["opportunities"]}
    def record(self,o):
        fp=str((o["anchor"],tuple((x["signature"],x["src"],x["dst"]) for x in o["route"])))
        if fp in self.seen:return False
        self.seen.add(fp);x={"fingerprint":fp,"anchor":o["anchor"],"hops":o["hops"],"net_bps":o["net_bps"],
                            "venues":o["venues"],"motif_match":o["motif_match"],"time_spread_seconds":o["time_spread_seconds"],
                            "paper_only":True,"execution_authority":False,"basis":"EXECUTED_SWAP_IMPLIED_RATE"}
        self.data["opportunities"].append(x);self.data["opportunities"]=self.data["opportunities"][-10000:];return True
    def save(self):return write_json(self.path,self.data)
