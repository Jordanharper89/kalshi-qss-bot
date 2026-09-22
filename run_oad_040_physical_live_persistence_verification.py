from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import run_kalshi_persistence_bridge

def main():
    print("="*72,flush=True);print(" OAD-040 PHYSICAL LIVE PERSISTENCE VERIFICATION",flush=True);print("="*72,flush=True)
    r=run_kalshi_persistence_bridge(Path.cwd(),max_persisted=3,progress=lambda x:print(x,flush=True))
    if r.persisted_observations!=3:
        raise SystemExit("[FAIL] Expected 3 persisted observations")
    print("[PASS] Real Kalshi events persisted through certified OLA PostgreSQL router",flush=True)
    print("[DONE] OAD-040 PHYSICAL PERSISTENCE VERIFIED",flush=True)
if __name__=="__main__": main()
