from pathlib import Path

P=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/alt_manager.py"
)

s=P.read_text(encoding="utf-8")

old='''    kp,user=r.q87.c.keypair()
    r.USER=user
'''

new='''    kp=r.q87.c.keypair()
    user=str(kp.pubkey())
    r.USER=user
'''

if old not in s:
    raise RuntimeError(
        "CANONICAL_ALT_KEYPAIR_SEAM_NOT_FOUND"
    )

s=s.replace(old,new,1)

P.write_text(
    s,
    encoding="utf-8"
)

print("[PASS] canonical ALT keypair contract repaired")
print("[KEYPAIR] single solders Keypair -> pubkey derived locally")
print("[BROADCAST] default remains disabled")