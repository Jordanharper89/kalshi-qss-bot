from pathlib import Path
from .core import run
def main():
    print("[QSB-049] ATOMIC METEORA->PUMPSWAP SIMULATED PNL",flush=True)
    print("[MODE] ONE transaction / simulate only / execution_authority=FALSE",flush=True)
    try:run(Path.cwd())
    except Exception as e:
        print("[FAIL] %s: %s"%(type(e).__name__,e),flush=True)
if __name__=="__main__":main()
