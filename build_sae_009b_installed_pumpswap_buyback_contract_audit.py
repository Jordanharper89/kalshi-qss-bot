from pathlib import Path

ROOT=Path.cwd()
BASE=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native"
NODE=BASE/"node_modules"

if not NODE.is_dir():
    raise RuntimeError("QSB059D_NODE_MODULES_MISSING")

needles=(
    "BuybackFeeRecipientMissing",
    "buybackFeeRecipient",
    "buyback_fee_recipient",
    "buyExactQuoteIn",
    "buy_exact_quote_in",
    "poolV2",
    "pool_v2",
)

hits=[]

for p in NODE.rglob("*"):
    if not p.is_file():
        continue
    if "pump" not in str(p).lower():
        continue
    if p.suffix.lower() not in (".js",".mjs",".cjs",".ts",".json"):
        continue

    try:
        s=p.read_text(encoding="utf-8",errors="ignore")
    except Exception:
        continue

    lines=s.splitlines()

    for i,line in enumerate(lines):
        if not any(x in line for x in needles):
            continue

        print("\n[SAE009B_FILE]",p.relative_to(ROOT))
        print("[SAE009B_LINE]",i+1)

        for n in range(max(0,i-5),min(len(lines),i+8)):
            print("%06d | %s"%(n+1,lines[n]))

        hits.append((str(p),i+1))

print("\n[SAE009B_MATCHES]",len(hits))

if not hits:
    raise RuntimeError("PUMPSWAP_BUYBACK_CONTRACT_NOT_FOUND")

print("[PASS] SAE-009B installed PumpSwap contract exposed")
print("[BASE]",BASE)
print("[RUNTIME] unchanged")
print("[BROADCAST] disabled")