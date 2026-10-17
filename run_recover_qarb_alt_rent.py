import getpass
import json
import os
import subprocess
from pathlib import Path

from solders.keypair import Keypair

ROOT=Path.cwd()

NODE_DIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

ALTS=[
    "7b9VvPqnD1WHNjkocoyz5BoL9YEmShTrQc7ypNbNW1PZ",
    "CP9FueydzmtxtUrhFuuDPsfKtscuG3iLHPhapaXuFZvv",
]

secret=getpass.getpass(
    "Private key (hidden): "
).strip()

try:
    if secret.startswith("["):
        kp=Keypair.from_bytes(
            bytes(
                json.loads(secret)
            )
        )
    else:
        kp=Keypair.from_base58_string(
            secret
        )
except Exception as exc:
    raise SystemExit(
        "[FAIL] private key format: "
        +str(exc)
    )

payload={
    "rpc":
        os.getenv(
            "SOLANA_RPC_URL",
            "https://api.mainnet-beta.solana.com"
        ),

    "secretBytes":
        list(bytes(kp)),

    "alts":
        ALTS,
}

p=subprocess.run(
    [
        "node",
        "recover_qarb_alt_rent.mjs"
    ],
    cwd=NODE_DIR,
    input=json.dumps(payload),
    text=True
)

raise SystemExit(
    p.returncode
)
