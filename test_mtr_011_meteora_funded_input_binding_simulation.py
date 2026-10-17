from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "mtr_011_meteora_funded_input_binding_simulation.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

checks = [
    ('import DLMM from "@meteora-ag/dlmm";',
     "Official Meteora DLMM import missing"),

    ('ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq',
     "LB pair missing"),

    ('CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR',
     "Public candidate missing"),

    ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
     "USDC mint missing"),

    ('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
     "USDT mint missing"),

    ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
     "Token program missing"),

    ('6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5',
     "Verified funded USDC account missing"),

    ('getAccountInfo',
     "Raw funded-account verification missing"),

    ('getAssociatedTokenAddressSync',
     "Canonical ATA derivation missing"),

    ('ASSOCIATED_TOKEN_PROGRAM_ID',
     "Official associated-token program constant missing"),

    ('TOKEN_PROGRAM_ID',
     "Official token-program constant missing"),

    ('getBinArrayForSwap',
     "Official getBinArrayForSwap missing"),

    ('swapQuote',
     "Official swapQuote missing"),

    ('pool.swap',
     "Official pool.swap missing"),

    ('414b3f4ceb5b5b88',
     "Swap2 discriminator missing"),

    ('swapInstruction.keys',
     "Swap2 account-meta inspection missing"),

    ('canonicalAtaIndexes',
     "Canonical ATA account binding check missing"),

    ('fundedUsdcAccount',
     "Funded input binding missing"),

    ('simulateTransaction',
     "simulateTransaction missing"),

    ('sigVerify: false',
     "sigVerify false missing"),

    ('requireAllSignatures: false',
     "Unsigned serialization guard missing"),

    ('verifySignatures: false',
     "Signature verification disabled for unsigned proof missing"),

    ('[SIGNING] DISABLED',
     "Signing-disabled marker missing"),

    ('[BROADCAST] DISABLED',
     "Broadcast-disabled marker missing"),
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

assert "new PublicKey(" in text
print("[PASS] PublicKey construction present")

print("[BUILD TEST COMPLETE] MTR-011")
