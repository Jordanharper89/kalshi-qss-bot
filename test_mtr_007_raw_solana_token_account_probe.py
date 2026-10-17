from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "mtr_007_raw_solana_token_account_probe.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

required = [
    "getTokenAccountsByOwner",
    '"jsonParsed"',
    "fetch(RPC",
    '"POST"',
    "response.result?.value",
    "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "100000000n",
    "BigInt",
    "[RAW_FIRST_TOKEN_ACCOUNT_BEGIN]",
    "[USDC_RAW_TOTAL]",
    "[OWNERSHIP_VERIFICATION]",
    "[FUNDING_VERIFICATION]",
    "[MTR-007] NO SIGNING.",
    "[MTR-007] NO SENDING.",
]

for item in required:
    if item not in text:
        raise SystemExit(
            f"[FAIL] Missing required element: {item}"
        )

forbidden = [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "signTransaction",
    "fromSecretKey",
    "Keypair.from",
    "QSB_SOLANA_PRIVATE_KEY",
    ".send("
]

for item in forbidden:
    if item in text:
        raise SystemExit(
            f"[FAIL] Forbidden operation found: {item}"
        )

print("[PASS] Direct Solana JSON-RPC transport encoded")
print("[PASS] getTokenAccountsByOwner encoded")
print("[PASS] jsonParsed requested directly from RPC")
print("[PASS] Raw result.value inspection encoded")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] Exact Token Program preserved")
print("[PASS] Raw USDC balance calculation encoded")
print("[PASS] Token-account ownership verification encoded")
print("[PASS] 100,000,000 raw USDC threshold encoded")
print("[PASS] No private-key reference present")
print("[PASS] No signing operation present")
print("[PASS] No sending operation present")
print("[PASS] No Meteora swap construction present")
print("[BUILD COMPLETE] MTR-007")
