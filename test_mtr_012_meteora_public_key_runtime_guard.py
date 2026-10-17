from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "mtr_012_meteora_public_key_runtime_guard.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

checks = [
    ('import DLMM from "@meteora-ag/dlmm";',
     "Official Meteora DLMM import present"),

    ('ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq',
     "Exact LB pair present"),

    ('LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo',
     "Exact Meteora program present"),

    ('CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR',
     "Exact public candidate present"),

    ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
     "Exact USDC mint present"),

    ('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
     "Exact USDT mint present"),

    ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
     "Exact Token Program present"),

    ('6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5',
     "Exact funded USDC account present"),

    ('function provePublicKey',
     "Runtime PublicKey guard present"),

    ('getAccountInfo',
     "Funded account RPC verification present"),

    ('getAssociatedTokenAddressSync',
     "Canonical ATA derivation present"),

    ('getBinArrayForSwap',
     "Official bin-array method present"),

    ('swapQuote',
     "Official quote method present"),

    ('pool.swap',
     "Official swap builder present"),

    ('414b3f4ceb5b5b88',
     "Swap2 discriminator present"),

    ('swapInstruction.keys',
     "Swap2 account metas inspected"),

    ('CANONICAL_INPUT_META_COUNT',
     "Canonical input account check present"),

    ('FUNDED_INPUT_BINDING',
     "Funded input binding present"),

    ('simulateTransaction',
     "Simulation present"),

    ('sigVerify: false',
     "Simulation signature verification disabled"),

    ('requireAllSignatures: false',
     "Unsigned serialization present"),

    ('verifySignatures: false',
     "Unsigned serialization verification disabled"),

    ('[SIGNING] DISABLED',
     "Signing disabled"),

    ('[BROADCAST] DISABLED',
     "Broadcast disabled"),
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
print("[PASS] Private-key environment reference absent")

assert "ATokenGPvbdGVxr1b4h1mZ8GQfG2r7FhYbGfG6q3m6wG6q" not in text
print("[PASS] Invalid ATA program constant absent")

print("[BUILD TEST COMPLETE] MTR-012")
