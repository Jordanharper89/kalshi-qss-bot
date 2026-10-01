import argparse,time
from pathlib import Path
from .core import build
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=3.0)
    a=ap.parse_args()
    print("[QSB-046] DEX-PINNED CROSS-VENUE ARBITRAGE ENGINE",flush=True)
    print("[STRATEGY] BUY LOW ON DEX A -> SELL HIGH ON DIFFERENT DEX B -> RETURN TO WSOL",flush=True)
    print("[ROUTING] Jupiter direct-route quotes pinned to one named DEX per leg",flush=True)
    print("[MODE] execution_authority=FALSE atomic=FALSE",flush=True)
    while True:
        try: build(Path.cwd())
        except KeyboardInterrupt:
            print("[STOP]",flush=True);break
        except Exception as e:
            print("[CYCLE_ERROR] %s: %s"%(type(e).__name__,e),flush=True)
        if a.once:break
        time.sleep(max(.5,a.sleep))
if __name__=="__main__":main()
