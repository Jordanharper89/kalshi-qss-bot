from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "tools" / "meteora_funded_public_preflight" / "mtr_009_meteora_public_swap_simulation.mjs"

text = HARNESS.read_text(encoding="utf-8")

required = [
    'import DLMM from "@meteora-ag/dlmm";',
    'ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq',
    'CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR',
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
    'getTokenAccountsByOwner',
    'getBinArrayForSwap',
    'swapQuote',
    'pool.swap',
    'simulateTransaction',
    'sigVerify: false',
    'requireAllSignatures: false',
    'verifySignatures: false',
    'INPUT_RAW_USDC = 100_000_000',
    'SLIPPAGE_BPS = 50',
    '[BROADCAST] DISABLED',
    '[SIGNATURES] NONE',
]

for item in required:
    assert item in text, f"missing required construct: {item}"

forbidden = [
    "QSB_SOLANA_PRIVATE_KEY",
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "signTransaction",
    "fromSecretKey",
    "Keypair.from",
    "sendTransaction",
    ".sign(",
    ".partialSign(",
    "ATokenGP",
]

for item in forbidden:
    assert item not in text, f"forbidden construct present: {item}"

assert "simulateTransaction" in text
assert "new PublicKey(" in text
assert "new Connection(" in text
assert "new Transaction" not in text

print("[PASS] Official Meteora DLMM default import preserved")
print("[PASS] Exact LB pair preserved")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] Exact USDT mint preserved")
print("[PASS] Exact Token Program preserved")
print("[PASS] Direct raw funding verification preserved")
print("[PASS] Verified funded token account required")
print("[PASS] Official getBinArrayForSwap encoded")
print("[PASS] Official swapQuote encoded")
print("[PASS] Official pool.swap encoded")
print("[PASS] Unsigned transaction serialization encoded")
print("[PASS] simulateTransaction encoded")
print("[PASS] No ATA-program assumption present")
print("[PASS] No private-key reference present")
print("[PASS] No signing operation present")
print("[PASS] No broadcast operation present")
print("[PASS] No canonical executor reference present")
print("[BUILD TEST COMPLETE] MTR-009")
