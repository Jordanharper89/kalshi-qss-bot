from __future__ import annotations
import json, os, re, subprocess, sys, time
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
COOLDOWN=float(os.getenv("QARB_PAPER_COOLDOWN_SECONDS","2.0"))
EXTRA_FRICTION_BPS=float(os.getenv("QARB_PAPER_EXTRA_FRICTION_BPS","25"))
STATE_REL=Path("runtime_state/qseries/qarb_clean_bot/paper_pnl_state.json")
TRADES_REL=Path("runtime_state/qseries/qarb_clean_bot/paper_trades.jsonl")

RX=re.compile(
    r"\[HOT_SIGNAL(?:_INITIAL)?\].*?token=(?P<token>\S+).*?"
    r"(?:buy=(?P<buy>\S+)\s+sell=(?P<sell>\S+)|dir=(?P<direction>\S+)).*?"
    r"size=(?P<size>[-+0-9.]+).*?net=(?P<net>[-+0-9.]+)\s*SOL.*?"
    r"bps=(?P<bps>[-+0-9.]+)"
)

def parse_signal(line):
    m=RX.search(line)
    if not m: return None
    d=m.groupdict()
    direction=d.get("direction")
    if not direction and d.get("buy") and d.get("sell"):
        direction=d["buy"]+"->"+d["sell"]
    return {
        "token":d["token"],"direction":direction,
        "size_sol":float(d["size"]),"quoted_net_sol":float(d["net"]),
        "quoted_bps":float(d["bps"])
    }

class Ledger:
    def __init__(self,root):
        self.root=Path(root); self.last={}; self.trades=[]
        self.net=0.0; self.peak=0.0; self.max_dd=0.0
        self.wins=0; self.losses=0; self.skipped_duplicates=0

    def admit(self,sig,now=None):
        now=time.time() if now is None else float(now)
        key=(sig["token"],sig["direction"],round(sig["size_sol"],9))
        prev=self.last.get(key)
        if prev is not None and now-prev<COOLDOWN:
            self.skipped_duplicates+=1
            return None
        self.last[key]=now

        friction=sig["size_sol"]*(EXTRA_FRICTION_BPS/10000.0)
        paper_net=sig["quoted_net_sol"]-friction
        row=dict(sig)
        row.update({
            "paper_net_sol":paper_net,
            "extra_friction_sol":friction,
            "extra_friction_bps":EXTRA_FRICTION_BPS,
            "opened_at_unix":now,
            "closed_at_unix":now,
            "holding_seconds":0.0,
            "paper_only":True,
            "execution_authority":False,
        })
        self.trades.append(row)
        self.net+=paper_net
        if paper_net>0: self.wins+=1
        else: self.losses+=1
        self.peak=max(self.peak,self.net)
        self.max_dd=max(self.max_dd,self.peak-self.net)
        self.persist(row)
        return row

    def summary(self):
        n=self.wins+self.losses
        return {
            "trades":n,"wins":self.wins,"losses":self.losses,
            "win_rate":0.0 if not n else self.wins/n,
            "paper_net_sol":self.net,"peak_paper_net_sol":self.peak,
            "max_drawdown_sol":self.max_dd,
            "skipped_duplicates":self.skipped_duplicates,
            "extra_friction_bps":EXTRA_FRICTION_BPS,
            "paper_only":True,"execution_authority":False,
        }

    def persist(self,row):
        p=self.root/TRADES_REL; p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        s=self.root/STATE_REL
        tmp=s.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.summary(),sort_keys=True,indent=2),encoding="utf-8")
        tmp.replace(s)

def runner_path(root):
    p=Path(root)/"run_qarb_022d_persistent_mriya_style_profit_runtime.py"
    if not p.is_file():
        raise RuntimeError("QARB_022D_RUNNER_MISSING:"+str(p))
    return p

def run(root):
    root=Path(root)
    ledger=Ledger(root)
    child=[sys.executable,str(runner_path(root))]
    print("[QARB-026] 022D PAPER PNL LEDGER",flush=True)
    print("[SOURCE] existing QARB-022D stdout HOT_SIGNAL stream",flush=True)
    print("[ACCOUNTING] HOT_SIGNAL net minus %.2f extra friction bps"%EXTRA_FRICTION_BPS,flush=True)
    print("[DEDUP] same token/route/size cooldown=%.2fs"%COOLDOWN,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE | Ctrl+C stops both",flush=True)

    p=subprocess.Popen(child,cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       text=True,bufsize=1)
    try:
        assert p.stdout is not None
        for line in p.stdout:
            print(line,end="",flush=True)
            sig=parse_signal(line)
            if not sig: continue
            row=ledger.admit(sig)
            if row is None: continue
            s=ledger.summary()
            print("[PAPER_TRADE] token=%s route=%s size=%.6f quoted=%+.9f friction=-%.9f paper_net=%+.9f SOL"%(
                row["token"][:10],row["direction"],row["size_sol"],row["quoted_net_sol"],
                row["extra_friction_sol"],row["paper_net_sol"]),flush=True)
            print("[PAPER_SCORE] trades=%d wins=%d losses=%d win_rate=%.1f%% net=%+.9f SOL max_dd=%.9f dupes=%d"%(
                s["trades"],s["wins"],s["losses"],s["win_rate"]*100.0,
                s["paper_net_sol"],s["max_drawdown_sol"],s["skipped_duplicates"]),flush=True)
    except KeyboardInterrupt:
        print("\n[STOP] paper ledger stopping",flush=True)
        p.terminate()
    finally:
        try: p.wait(timeout=5)
        except Exception:
            p.kill()
    print("[FINAL_PAPER_SCORE] "+json.dumps(ledger.summary(),sort_keys=True),flush=True)
    return ledger.summary()

def main():
    run(Path.cwd())

if __name__=="__main__":
    main()
