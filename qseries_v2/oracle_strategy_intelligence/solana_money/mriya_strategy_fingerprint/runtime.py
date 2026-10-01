from pathlib import Path
from .extractor import run
def main():
    print("[QSB-035] MRIYA STRATEGY FINGERPRINT EXTRACTOR",flush=True)
    print("[PURPOSE] finish missed captured slots + convert exact wins/fails into reusable route fingerprints",flush=True)
    print("[RATE] 2.6s minimum block fetch spacing + bounded 429 backoff/retry",flush=True)
    print("[METRICS] venue chain, size, gross bps, fee drag, compute, SOL-equivalent net where exact",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    run(Path.cwd())
if __name__=="__main__":main()
