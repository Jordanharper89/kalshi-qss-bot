from pathlib import Path

ROOT=Path.cwd()
NODE=ROOT/"node_modules"

if not NODE.is_dir():
    raise RuntimeError("NODE_MODULES_MISSING")

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
    if not any(x in s for x in needles):
        continue

    lines=s.splitlines()

    for i,line in enumerate(lines):
        if not any(x in line for x in needles):
            continue

        lo=max(0,i-4)
        hi=min(len(lines),i+7)

        print("\n[SAE009_FILE]",p.relative_to(ROOT))
        print("[SAE009_LINE]",i+1)

        for n in range(lo,hi):
            print("%06d | %s"%(n+1,lines[n]))

        hits.append((str(p),i+1))

print("\n[SAE009_MATCHES]",len(hits))

if not hits:
    raise RuntimeError("NO_INSTALLED_PUMP_BUYBACK_CONTRACT_FOUND")

print("[PASS] SAE-009 installed PumpSwap contract physically exposed")
print("[RUNTIME] unchanged")
print("[BROADCAST] disabled")