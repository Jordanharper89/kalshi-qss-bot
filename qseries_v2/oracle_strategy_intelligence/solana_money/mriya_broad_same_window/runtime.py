from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_executable_requote.gate import build
def main():
    print("[QSB-044] BROAD SAME-WINDOW EXECUTABLE HUNTER",flush=True)
    print("[DISCOVERY] exact token-token + fee-adjusted native-SOL signer deltas",flush=True)
    print("[VALIDATION] every surfaced route must survive QSB-042 executable Jupiter leg re-quote",flush=True)
    print("[MODE] execution_authority=FALSE",flush=True)
    build(Path.cwd())
if __name__=="__main__":main()
