from pathlib import Path
import sys

sys.stdout.reconfigure(
    encoding="utf-8",
    errors="backslashreplace"
)

ROOT=Path.cwd()

SDK=(
    ROOT/
    "qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qsb059d_pump_native"/
    "node_modules"/
    "@pump-fun"/
    "pump-swap-sdk"
)

if not SDK.is_dir():
    raise RuntimeError(
        "PUMPSWAP_SDK_DIRECTORY_MISSING"
    )

needles=(
    "BuybackFeeRecipientMissing",
    "buybackFeeRecipient",
    "buyback_fee_recipient",
    "buyExactQuoteIn",
    "buy_exact_quote_in",
    "poolV2",
    "pool_v2",
)

hits=0

for p in SDK.rglob("*"):
    if not p.is_file():
        continue

    if p.suffix.lower() not in (
        ".js",".mjs",".cjs",".ts",".json"
    ):
        continue

    s=p.read_text(
        encoding="utf-8",
        errors="replace"
    )

    lines=s.splitlines()

    for i,line in enumerate(lines):
        if not any(x in line for x in needles):
            continue

        hits+=1

        print(
            "\n[SAE009C_FILE]",
            p.relative_to(ROOT)
        )

        print(
            "[SAE009C_LINE]",
            i+1
        )

        for n in range(
            max(0,i-6),
            min(len(lines),i+9)
        ):
            print(
                "%06d | %s"%(
                    n+1,
                    lines[n]
                )
            )

print(
    "\n[SAE009C_MATCHES]",
    hits
)

if hits==0:
    raise RuntimeError(
        "PUMPSWAP_CONTRACT_MATCHES_ZERO"
    )

print(
    "[PASS] SAE-009C PumpSwap contract audit complete"
)