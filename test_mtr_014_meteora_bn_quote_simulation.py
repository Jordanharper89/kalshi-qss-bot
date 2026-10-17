from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "mtr_014_meteora_bn_quote_simulation.mjs"
)

text = HARNESS.read_text(
    encoding="utf-8"
)

checks = [
    (
        'import BN from "bn.js";',
        "BN import present"
    ),
    (
        'new BN("100000000")',
        "Input amount uses BN"
    ),
    (
        'new BN("50")',
        "Slippage uses BN"
    ),
    (
        'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo',
        "Correct Meteora program ID present"
    ),
    (
        'CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR',
        "Exact public candidate present"
    ),
    (
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        "Exact USDC mint present"
    ),
    (
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        "Exact USDT mint present"
    ),
    (
        'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
        "Exact Token Program present"
    ),
    (
        '6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5',
        "Exact funded USDC account present"
    ),
    (
        'getAssociatedTokenAddressSync',
        "Canonical ATA derivation present"
    ),
    (
        'getBinArrayForSwap',
        "Official bin-array lookup present"
    ),
    (
        'swapQuote',
        "Official swap quote present"
    ),
    (
        'pool.swap',
        "Official swap builder present"
    ),
    (
        '414b3f4ceb5b5b88',
        "Swap2 discriminator present"
    ),
    (
        'swapInstruction.keys',
        "Swap2 account binding present"
    ),
    (
        'CANONICAL_INPUT_META_COUNT',
        "Canonical input account check present"
    ),
    (
        'FUNDED_INPUT_BINDING',
        "Funded input binding present"
    ),
    (
        'simulateTransaction',
        "Physical simulation present"
    ),
    (
        'sigVerify: false',
        "Signature verification disabled"
    ),
    (
        'requireAllSignatures: false',
        "Unsigned serialization present"
    ),
    (
        'verifySignatures: false',
        "Unsigned verification disabled"
    ),
    (
        '[SIGNING] DISABLED',
        "Signing disabled"
    ),
    (
        '[BROADCAST] DISABLED',
        "Broadcast disabled"
    ),
]

for needle, message in checks:
    assert needle in text, message
    print(f"[PASS] {message}")

for forbidden in [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "sendTransaction(",
    "Keypair.fromSecretKey",
    "signTransaction",
    "signAllTransactions",
]:
    assert forbidden not in text, (
        f"Forbidden operation present: {forbidden}"
    )
    print(
        f"[PASS] Forbidden operation absent: {forbidden}"
    )

assert "QSB_SOLANA_PRIVATE_KEY" not in text
print(
    "[PASS] Private-key environment reference absent"
)

assert (
    "LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo"
    not in text
)
print(
    "[PASS] Incorrect Meteora program ID absent"
)

assert (
    "ATokenGPvbdGVxr1b4h1mZ8GQfG2r7FhYbGfG6q3m6wG6q"
    not in text
)
print(
    "[PASS] Invalid ATA program constant absent"
)

print(
    "[BUILD TEST COMPLETE] MTR-014"
)
