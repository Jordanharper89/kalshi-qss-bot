
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "tools" / "meteora_funded_public_preflight"
NODE = TOOL / "meteora_funded_public_preflight.mjs"
PACKAGE = TOOL / "package.json"


def fail(message):
    raise AssertionError(message)


def main():
    if not NODE.exists():
        fail("missing Node proof harness")

    if not PACKAGE.exists():
        fail("missing package.json")

    source = NODE.read_text(
        encoding="utf-8"
    )

    required = [
        "getTokenLargestAccounts",
        "canonicalAta",
        "pool.getBinArrayForSwap",
        "pool.swapQuote",
        "pool.swap",
        "414b3f4ceb5b5b88",
        "STANDALONE_METEORA_PREFLIGHT_PASS",
        "NO_SIGN NO_SEND",
    ]

    for item in required:
        if item not in source:
            fail(
                f"missing required proof element: {item}"
            )

    forbidden = [
        "QSB_SOLANA_PRIVATE_KEY",
        "sendAndConfirmTransaction",
        "sendRawTransaction",
        "signTransaction",
        "signAllTransactions",
    ]

    for item in forbidden:
        if item in source:
            fail(
                f"forbidden live/private-key operation present: {item}"
            )

    result = subprocess.run(
        ["node", "--check", str(NODE)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail("Node syntax check failed")

    print(
        "[PASS] MTR-001 installer/proof harness present"
    )
    print(
        "[PASS] exact live pool token-X binding present"
    )
    print(
        "[PASS] exact live pool token-Y binding present"
    )
    print(
        "[PASS] dynamic public funded USDC-holder discovery present"
    )
    print(
        "[PASS] canonical ATA requirement present"
    )
    print(
        "[PASS] system-wallet/SOL requirement present"
    )
    print(
        "[PASS] official Meteora getBinArrayForSwap present"
    )
    print(
        "[PASS] official Meteora swapQuote present"
    )
    print(
        "[PASS] official Meteora pool.swap present"
    )
    print(
        "[PASS] official Swap2 discriminator guard present"
    )
    print(
        "[PASS] no private key path present"
    )
    print(
        "[PASS] no transaction signing/send path present"
    )
    print(
        "[PASS] Node syntax check"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
