from pathlib import Path

HARNESS = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_019_pumpswap_dependency_resolution_preflight.mjs"
)

text = HARNESS.read_text(
    encoding="utf-8"
)

checks = [
    (
        "PumpSwap dependency resolver",
        "function resolvePackage(",
    ),
    (
        "Solana web3 dependency resolution",
        '"@solana/web3.js"',
    ),
    (
        "Solana SPL dependency resolution",
        '"@solana/spl-token"',
    ),
    (
        "PumpSwap SDK dependency resolution",
        '"@pump-fun/pump-swap-sdk"',
    ),
    (
        "BN dependency resolution",
        '"bn.js"',
    ),
    (
        "Node require.resolve",
        "require.resolve(",
    ),
    (
        "Exact PumpSwap program ID",
        "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
    ),
    (
        "Exact public candidate",
        "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
    ),
    (
        "Native SOL",
        "NATIVE_MINT",
    ),
    (
        "0.010 SOL input",
        'new BN("10000000")',
    ),
    (
        "Official pool state",
        "swapSolanaState",
    ),
    (
        "Official buy quote",
        "buyQuoteInput",
    ),
    (
        "Pool owner verification",
        "POOL_PROGRAM_OWNER",
    ),
    (
        "User binding",
        "STATE_USER_BINDING",
    ),
    (
        "Unsigned serialization",
        "requireAllSignatures: false",
    ),
    (
        "Signature verification disabled",
        "verifySignatures: false",
    ),
    (
        "Raw RPC simulation",
        '"simulateTransaction"',
    ),
    (
        "Base64 encoding",
        '"base64"',
    ),
    (
        "Signature verification false",
        "sigVerify: false",
    ),
    (
        "Recent blockhash replacement",
        "replaceRecentBlockhash: true",
    ),
    (
        "Signing disabled",
        "[SIGNING] DISABLED",
    ),
    (
        "Broadcast disabled",
        "[BROADCAST] DISABLED",
    ),
    (
        "Private key unused",
        "[PRIVATE_KEY] NOT USED",
    ),
]

for label, needle in checks:
    assert needle in text, (
        f"{label}: missing"
    )

    print(
        f"[PASS] {label}"
    )

for needle in [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "sendTransaction(",
    "Keypair.fromSecretKey",
    "signTransaction",
    "signAllTransactions",
    "QSB_SOLANA_PRIVATE_KEY",
    "Connection.simulateTransaction",
]:
    assert needle not in text, (
        f"Forbidden operation/reference present: {needle}"
    )

    print(
        "[PASS] Forbidden operation/reference absent: "
        f"{needle}"
    )

print(
    "[TEST COMPLETE] "
    "MTR-019 static safety and construction checks PASS"
)
