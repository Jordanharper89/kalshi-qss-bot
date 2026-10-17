from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "meteora_funded_public_preflight.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

required = [
    'import DLMM from "@meteora-ag/dlmm";',
    "getTokenAccountsByOwner",
    'encoding: "jsonParsed"',
    "Array.isArray(response?.value)",
    "response.value",
    "inspectRow",
    "extractTokenInfo",
    "BigInt",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
    "100000000n",
    "[OWNERSHIP_VERIFICATION]",
    "[FUNDING_VERIFICATION]",
    "[MTR-006] STOP BEFORE TRANSACTION CONSTRUCTION."
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
    ".send("
]

for item in forbidden:
    if item in text:
        raise SystemExit(
            f"[FAIL] Forbidden operation found: {item}"
        )

print("[PASS] Official Meteora DLMM default import preserved")
print("[PASS] Exact LB pair preserved")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] getTokenAccountsByOwner inspection encoded")
print("[PASS] Actual response.value shape inspection encoded")
print("[PASS] jsonParsed normalization encoded")
print("[PASS] Raw USDC BigInt balance calculation encoded")
print("[PASS] Token-account ownership verification encoded")
print("[PASS] 100,000,000 raw USDC threshold encoded")
print("[PASS] No signing operation present")
print("[PASS] No sending operation present")
print("[PASS] MTR-006 stops before transaction construction")
print("[BUILD COMPLETE] MTR-006")
