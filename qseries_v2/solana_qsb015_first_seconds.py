from __future__ import annotations
import json, os, time
from collections import defaultdict, deque
from pathlib import Path

REVISION="QSB-015-FIRST-SECONDS-LAUNCH-IMPULSE-V1"
FAST_FAMILIES={"RAYDIUM_CPMM","RAYDIUM_CLMM","RAYDIUM_V4","RAYDIUM_LAUNCHLAB",
               "METEORA_DBC","METEORA_DAMM","METEORA_DLMM","PUMP_FUN","PUMP_SWAP","ORCA"}

class FirstSecondsLane:
    def __init__(self,root:Path):
        self.root=Path(root).resolve()
        self.state=self.root/"runtime_state/qseries/qsb015_first_seconds"
        self.state.mkdir(parents=True,exist_ok=True)
        self.pos_path=self.state/"positions.json"
        self.ledger_path=self.state/"ledger.json"
        self.sig_path=self.state/"signal_history.json"
        self.notional=float(os.getenv("QSB015_NOTIONAL_USDC","5"))
        self.stop=float(os.getenv("QSB015_STOP_LOSS","0.10"))
        self.tp=float(os.getenv("QSB015_TAKE_PROFIT","0.30"))
        self.trail=float(os.getenv("QSB015_TRAILING_STOP","0.12"))
        self.max_hold=float(os.getenv("QSB015_MAX_HOLD_SECONDS","120"))
        self.friction=float(os.getenv("QSB015_ROUNDTRIP_FRICTION","0.03"))
        self.min_liq=float(os.getenv("QSB015_MIN_LIQUIDITY_USD","2500"))
        self.min_hits=int(os.getenv("QSB015_MIN_SIGNATURE_HITS","1"))
        self.max_open=int(os.getenv("QSB015_MAX_OPEN","3"))
        self.positions=self._load(self.pos_path,{"positions":[]})
        self.ledger=self._load(self.ledger_path,{"trades":[]})
        self.history=self._load(self.sig_path,{})

    def _load(self,p,d):
        try:return json.loads(p.read_text(encoding="utf-8"))
        except Exception:return d

    def _save(self,p,x):
        p.write_text(json.dumps(x,indent=2,sort_keys=True,default=str),encoding="utf-8")

    def _open(self):
        return [p for p in self.positions["positions"] if p.get("status")=="OPEN"]

    def manage(self,price_by_market):
        closed=[]
        for p in self.positions["positions"]:
            if p.get("status")!="OPEN":continue
            px=price_by_market.get(p["market"])
            if px is None:continue
            entry=float(p["entry_price"])
            p["high_water_price"]=max(float(p["high_water_price"]),float(px))
            ret=float(px)/entry-1
            trail=float(px)/float(p["high_water_price"])-1
            age=time.time()-float(p["opened_unix"])
            reason=None
            if ret<=-self.stop:reason="STOP_LOSS"
            elif ret>=self.tp:reason="TAKE_PROFIT"
            elif float(p["high_water_price"])>=entry*1.10 and trail<=-self.trail:reason="TRAILING_STOP"
            elif age>=self.max_hold:reason="MAX_HOLD"
            if not reason:continue
            half=self.friction/2
            exit_px=float(px)*(1-half)
            gross=float(p["qty"])*float(px)-self.notional
            net=float(p["qty"])*exit_px-self.notional
            p.update({"status":"CLOSED","closed_unix":time.time(),"reference_exit_price":float(px),
                      "exit_price":exit_px,"exit_reason":reason,"gross_pnl_usdc":gross,
                      "net_pnl_usdc":net,"modeled_friction_usdc":gross-net+float(p["entry_friction_usdc"])})
            self.ledger["trades"].append(dict(p));closed.append(dict(p))
        self._save(self.pos_path,self.positions);self._save(self.ledger_path,self.ledger)
        return closed

    def evaluate(self,burst,rows):
        now=time.time();entries=[]
        hot={x.get("mint"):int(x.get("signature_hits") or 0) for x in burst.get("hot_mints") or []}
        by_token=defaultdict(list)
        for r in rows:
            if r.get("token_mint"):by_token[str(r["token_mint"])].append(r)

        open_tokens={p.get("token") for p in self._open()}
        for mint,hits in hot.items():
            if hits<self.min_hits or mint in open_tokens:continue
            pools=by_token.get(mint) or []
            pools.sort(key=lambda r:float(r.get("liquidity_usd") or 0),reverse=True)
            if not pools:continue
            r=pools[0]
            fam=str(r.get("family") or "UNKNOWN").upper()
            if fam not in FAST_FAMILIES:continue
            liq=float(r.get("liquidity_usd") or 0)
            if liq<self.min_liq:continue

            h=self.history.setdefault(mint,[])
            h.append({"t":now,"hits":hits,"price":float(r["last_price"]),"family":fam,"market":r["market_address"]})
            h[:]=h[-6:]
            if len(self._open())>=self.max_open:continue

            # first-seconds impulse: on-chain activity + fresh pool + no waiting for 8+ price bars
            score=min(1.0,0.45+0.15*min(hits,3)+0.20*min(1,liq/25000))
            if score<0.60:continue

            half=self.friction/2;ref=float(r["last_price"]);entry=ref*(1+half)
            p={"position_id":f"QSB015-{mint[:8]}-{int(now*1000)}","status":"OPEN","mode":"PAPER",
               "strategy":"FIRST_SECONDS_LAUNCH_IMPULSE","selection_lane":"FAST_LAUNCH",
               "family":fam,"market":r["market_address"],"token":mint,"opened_unix":now,
               "reference_entry_price":ref,"entry_price":entry,"high_water_price":entry,
               "notional_usdc":self.notional,"qty":self.notional/entry,
               "entry_friction_usdc":self.notional*half,"signal_score":score,
               "signature_hits":hits,"liquidity_usd":liq}
            self.positions["positions"].append(p);entries.append(dict(p));open_tokens.add(mint)

        self._save(self.pos_path,self.positions);self._save(self.sig_path,self.history)
        return entries

    def status(self):
        trades=self.ledger["trades"];wins=sum(float(t.get("net_pnl_usdc") or 0)>0 for t in trades)
        net=sum(float(t.get("net_pnl_usdc") or 0) for t in trades)
        return {"closed":len(trades),"wins":wins,"losses":len(trades)-wins,
                "win_rate":wins/len(trades) if trades else None,"net":net,"open":len(self._open())}
