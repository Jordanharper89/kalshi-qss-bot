from pathlib import Path

HARNESS = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_016_pumpswap_public_unsigned_preflight.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

checks = [
    ("PumpSwap SDK import", "@pump-fun/pump-swap-sdk"),
    ("Online Pump AMM SDK", "OnlinePumpAmmSdk"),
    ("Pump AMM SDK", "PUMP_AMM_SDK"),
    ("Exact PumpSwap program ID",
     "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),
    ("Exact public candidate",
     "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR"),
    ("Native SOL input", "NATIVE_MINT"),
    ("BN input", 'new BN("10000000")'),
    ("Official buyQuoteInput", "buyQuoteInput"),
    ("Online pool state", "swapSolanaState"),
    ("Raw account verification", "getAccountInfo"),
    ("Unsigned serialization", "requireAllSignatures: false"),
    ("Signature verification disabled", "verifySignatures: false"),
    ("Raw RPC simulation", '"simulateTransaction"'),
    ("Base64 encoding", '"base64"'),
    ("Signature verification false", "sigVerify: false"),
    ("Recent blockhash replacement", "replaceRecentBlockhash: true"),
    ("Signing disabled", "[SIGNING] DISABLED"),
    ("Broadcast disabled", "[BROADCAST] DISABLED"),
    ("Private key unused", "[PRIVATE_KEY] NOT USED"),
]

for label, needle in checks:
    assert needle in text, f"{label}: missing"
    print(f"[PASS] {label}")

forbidden = [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "sendTransaction(",
    "Keypair.fromSecretKey",
    "signTransaction",
    "signAllTransactions",
    "QSB_SOLANA_PRIVATE_KEY",
    "Connection.simulateTransaction",
]

for needle in forbidden:
    assert needle not in text, (
        f"Forbidden operation/reference present: {needle}"
    )
    print(f"[PASS] Forbidden operation/reference absent: {needle}")

print("[TEST COMPLETE] MTR-016 static safety and construction checks PASS")
