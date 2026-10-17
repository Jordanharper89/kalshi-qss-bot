from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "tools" / "meteora_funded_public_preflight" / "mtr_010_meteora_funded_input_binding_simulation.mjs"

text = HARNESS.read_text(encoding="utf-8")

checks = [
    ('from "@meteora-ag/dlmm"', "Official Meteora DLMM import missing"),
    ('ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq', "LB pair missing"),
    ('CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR', "Public candidate missing"),
    ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', "USDC mint missing"),
    ('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', "USDT mint missing"),
    ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', "Token program missing"),
    ('6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5', "Funded USDC account missing"),
    ('getAccountInfo', "Direct account verification missing"),
    ('getAssociatedTokenAddressSync', "Canonical ATA derivation missing"),
    ('getBinArrayForSwap', "Official bin-array path missing"),
    ('swapQuote', "Official swap quote missing"),
    ('pool.swap', "Official pool.swap missing"),
    ('414b3f4ceb5b5b88', "Swap2 discriminator guard missing"),
    ('swapInstruction.keys', "Swap2 account-meta inspection missing"),
    ('FUNDED_INPUT_BINDING', "Funded input binding missing"),
    ('simulateTransaction', "Simulation missing"),
    ('sigVerify: false', "sigVerify=false missing"),
    ('requireAllSignatures: false', "Unsigned serialization missing"),
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
    "QSB_SOLANA_PRIVATE_KEY",
]:
    assert forbidden not in text, f"Forbidden operation/reference present: {forbidden}"
    print(f"[PASS] No {forbidden} present")

print("[BUILD TEST COMPLETE] MTR-010")
