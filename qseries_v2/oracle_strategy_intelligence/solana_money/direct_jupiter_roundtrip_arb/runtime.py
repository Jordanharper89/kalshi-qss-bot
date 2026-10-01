import argparse,time
from pathlib import Path
from .core import build
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=2.0);a=ap.parse_args()
    print("[QSB-045] DIRECT JUPITER ROUNDTRIP ARBITRAGE HUNTER",flush=True)
    print("[BYPASS] no Raydium/Meteora/Orca getTransaction/getBlock hydration dependency",flush=True)
    print("[FLOW] fresh live tokens -> WSOL/token executable order -> token/WSOL executable order -> after-cost PnL",flush=True)
    print("[MODE] execution_authority=FALSE atomic=FALSE",flush=True)
    while True:
        try:build(Path.cwd())
        except KeyboardInterrupt:print("[STOP]",flush=True);break
        except Exception as e:print("[CYCLE_ERROR] %s: %s"%(type(e).__name__,e),flush=True)
        if a.once:break
        time.sleep(max(.5,a.sleep))
if __name__=="__main__":main()
