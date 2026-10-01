from pathlib import Path
import py_compile
import re

P=Path(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

if not P.is_file():
    raise SystemExit("[FAIL] ORACLE-003 missing")

s=P.read_text(encoding="utf-8")

pat=re.compile(
    r'def pump_min_base_out\('
    r'[\s\S]*?'
    r'(?=\n\ndef net_received\()'
)

new=r'''def pump_min_base_out(
    pump_ix
):
    raw=base64.b64decode(
        pump_ix.get("data") or ""
    )

    BUY=bytes([
        102,6,61,18,
        1,218,235,234
    ])

    BUY_EXACT=bytes([
        198,46,21,82,
        180,217,232,112
    ])

    if len(raw)<24:
        raise RuntimeError(
            "PUMP_DATA_TOO_SHORT"
        )

    disc=raw[:8]

    a=int.from_bytes(
        raw[8:16],
        "little"
    )

    b=int.from_bytes(
        raw[16:24],
        "little"
    )

    if disc==BUY:
        # Published PumpSwap BUY:
        # a = exact base_amount_out
        # b = max_quote_amount_in
        #
        # Successful execution guarantees the
        # requested base output. Refuse any route
        # whose maximum SOL spend exceeds the
        # 0.001 SOL canary cap.
        base_amount_out=a
        max_quote_amount_in=b

        if max_quote_amount_in>MICRO_LAMPORTS:
            raise RuntimeError(
                "PUMP_MAX_QUOTE_EXCEEDS_MICRO_CAP:"
                +str(max_quote_amount_in)
            )

        if base_amount_out<=0:
            raise RuntimeError(
                "PUMP_BASE_AMOUNT_ZERO"
            )

        return base_amount_out

    if disc==BUY_EXACT:
        # Published BUY_EXACT_QUOTE_IN:
        # a = spendable_quote_in
        # b = min_base_amount_out
        spendable_quote_in=a
        min_base_amount_out=b

        if spendable_quote_in>MICRO_LAMPORTS:
            raise RuntimeError(
                "PUMP_SPEND_EXCEEDS_MICRO_CAP:"
                +str(spendable_quote_in)
            )

        if min_base_amount_out<=0:
            raise RuntimeError(
                "PUMP_MINIMUM_ZERO"
            )

        return min_base_amount_out

    raise RuntimeError(
        "PUMP_UNKNOWN_BUY_DISCRIMINATOR:"
        +disc.hex()
    )
'''

if not pat.search(s):
    raise SystemExit(
        "[FAIL] pump parser seam missing"
    )

s=pat.sub(
    new.rstrip(),
    s,
    count=1
)

P.write_text(
    s,
    encoding="utf-8"
)

py_compile.compile(
    str(P),
    doraise=True
)

print("[PASS] ORACLE-003B Pump instruction contract repaired")
print("[PUMP] buy + buy_exact_quote_in both supported")
print("[BUY] base_amount_out treated as guaranteed output")
print("[EXACT] min_base_amount_out treated as guaranteed output")
print("[CAP] maximum Pump quote spend <= 0.001 SOL")
print("[STRATEGY] PumpSwap -> Meteora DLMM unchanged")
print("[MODE] physical paper first; no broadcast")