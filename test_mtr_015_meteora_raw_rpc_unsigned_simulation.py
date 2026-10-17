from pathlib import Path

harness = Path(
    "tools/meteora_funded_public_preflight/"
    "mtr_015_meteora_raw_rpc_unsigned_simulation.mjs"
)

text = harness.read_text(encoding="utf-8")

checks = [
    ("import DLMM from \"@meteora-ag/dlmm\";", "Official Meteora DLMM import"),
    ("import BN from \"bn.js\";", "BN import"),
    ("const INPUT_RAW_USDC = new BN(\"100000000\");", "Input amount uses BN"),
    ("const SLIPPAGE_BPS = new BN(\"50\");", "Slippage uses BN"),
    ("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo", "Correct Meteora program ID"),
    ("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR", "Exact public candidate"),
    ("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Exact USDC mint"),
    ("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "Exact USDT mint"),
    ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "Exact Token Program"),
    ("6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5", "Exact funded USDC account"),
    ("getAccountInfo(fundedAccount", "Raw funded-account verification"),
    ("getAssociatedTokenAddressSync(", "Canonical ATA derivation"),
    ("getBinArrayForSwap(", "Official bin-array lookup"),
    ("swapQuote(", "Official swap quote"),
    ("pool.swap({", "Official swap builder"),
    ("414b3f4ceb5b5b88", "Swap2 discriminator"),
    ("replaceOnlyInputAccount(", "Swap2 account binding"),
    ("canonicalUsdcAta", "Canonical input account check"),
    ("fundedAccount", "Funded input binding"),
    ("serialize({", "Unsigned serialization"),
    ("requireAllSignatures: false", "Unsigned serialization disabled"),
    ("verifySignatures: false", "Signature verification disabled"),
    ("simulateTransaction", "Raw RPC simulation"),
    ("encoding: \"base64\"", "Raw RPC base64 encoding"),
    ("sigVerify: false", "Raw RPC signature verification disabled"),
    ("replaceRecentBlockhash: true", "Raw RPC recent blockhash replacement"),
    ("await fetch(RPC_URL", "Direct JSON-RPC transport"),
    ("[SIGNING] DISABLED", "Signing disabled"),
    ("[BROADCAST] DISABLED", "Broadcast disabled"),
    ("[PRIVATE_KEY] NOT USED", "Private key not used"),
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
    print(f"[PASS] Forbidden operation/reference absent: {forbidden}")

assert "Connection.simulateTransaction" not in text
print("[PASS] Problematic Connection.simulateTransaction wrapper absent")

assert "LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo" in text
print("[PASS] Exact Meteora program spelling preserved")

print("[BUILD TEST COMPLETE] MTR-015")
