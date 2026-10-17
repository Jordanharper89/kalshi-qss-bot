
from pathlib import Path
import subprocess
import sys


ROOT = (
    Path("tools")
    / "meteora_official_swap2_proof"
)

PROOF = (
    ROOT
    / "meteora_official_swap2_proof.mjs"
)

PACKAGE = ROOT / "package.json"


if not PROOF.exists():
    print("[FAIL] proof harness missing")
    sys.exit(1)

if not PACKAGE.exists():
    print("[FAIL] package.json missing")
    sys.exit(1)


source = PROOF.read_text(
    encoding="utf-8"
)


forbidden = (
    "QSB_SOLANA_PRIVATE_KEY",
    "Keypair.fromSecretKey",
    "sendAndConfirmTransaction",
)


for item in forbidden:
    if item in source:
        print(
            f"[FAIL] forbidden live/private-key path: {item}"
        )
        sys.exit(1)


print(
    "[PASS] isolated proof harness present"
)

print(
    "[PASS] no private-key path"
)

print(
    "[PASS] no live-send path"
)

print(
    "[RUN] official Meteora SDK simulation"
)


result = subprocess.run(
    [
        "node",
        str(PROOF),
    ],
    check=False,
)


if result.returncode != 0:
    print(
        "[FAIL] official Meteora Swap2 simulation failed"
    )
    sys.exit(
        result.returncode
    )


print(
    "[PASS] official Meteora Swap2 standalone simulation"
)
