from __future__ import annotations

import base64
import json
from collections import Counter
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp

STATE = Path("runtime_state/oracle/solana_atomic_executor/canonical_alt.json")
REPORT = Path("runtime_state/oracle/solana_atomic_executor/canonical_alt_coverage_diagnostic.json")
MAX_TX_BYTES = 1232

# Diagnostic only. No create/extend/send path exists in this module.
EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REAL_MONEY_MOVED = False


def _save(payload):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tmp = REPORT.with_suffix(REPORT.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(REPORT)


def _state_alt_address():
    if not STATE.exists():
        raise RuntimeError("CANONICAL_ALT_STATE_MISSING:" + str(STATE))

    obj = json.loads(STATE.read_text(encoding="utf-8"))

    preferred = (
        "address",
        "alt_address",
        "lookup_table",
        "lookup_table_address",
        "table",
    )

    for key in preferred:
        value = obj.get(key) if isinstance(obj, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                y = walk(v)
                if y:
                    return y
        elif isinstance(x, list):
            for v in x:
                y = walk(v)
                if y:
                    return y
        elif isinstance(x, str):
            s = x.strip()
            try:
                if len(r.q87.c.b58d(s)) == 32:
                    return s
            except Exception:
                pass
        return None

    found = walk(obj)
    if not found:
        raise RuntimeError("CANONICAL_ALT_ADDRESS_NOT_FOUND")
    return found


def _onchain_alt(alt_address):
    value = r.q87.c.rpc(
        "getAccountInfo",
        [alt_address, {"encoding": "base64", "commitment": "processed"}],
    ).get("value")

    if not isinstance(value, dict):
        raise RuntimeError("CANONICAL_ALT_ONCHAIN_MISSING:" + alt_address)

    owner = str(value.get("owner") or "")
    data_row = value.get("data") or []
    if not isinstance(data_row, list) or not data_row:
        raise RuntimeError("CANONICAL_ALT_BAD_ACCOUNT_DATA")

    raw = base64.b64decode(data_row[0])
    if len(raw) < 56 or (len(raw) - 56) % 32:
        raise RuntimeError("CANONICAL_ALT_BAD_BINARY_LENGTH:" + str(len(raw)))

    addresses = [
        raw[i:i + 32]
        for i in range(56, len(raw), 32)
    ]

    return {
        "owner": owner,
        "raw": raw,
        "bytes": addresses,
        "addresses": [r.q87.c.b58e(x) for x in addresses],
    }


def _instruction_meta(payer, instructions):
    order = []
    meta = {}

    def touch(pk, signer=False, writable=False, program=False):
        pk = str(pk)
        if pk not in meta:
            order.append(pk)
            meta[pk] = {
                "signer": bool(signer),
                "writable": bool(writable),
                "program": bool(program),
            }
        else:
            meta[pk]["signer"] |= bool(signer)
            meta[pk]["writable"] |= bool(writable)
            meta[pk]["program"] |= bool(program)

    touch(payer, True, True, False)

    for ix in instructions:
        touch(ix["programId"], False, False, True)
        for a in ix.get("accounts") or []:
            touch(
                a["pubkey"],
                a.get("isSigner", False),
                a.get("isWritable", False),
                False,
            )

    return order, meta


def _warm_frequency():
    per_token = {}

    for token, template in r.TEMPLATES.items():
        bucket = per_token.setdefault(str(token), set())
        for ix in template.get("instructions") or []:
            bucket.add(str(ix.get("programId")))
            for a in ix.get("accounts") or []:
                bucket.add(str(a.get("pubkey")))

    for token, template in r.METEORA_TEMPLATES.items():
        bucket = per_token.setdefault(str(token), set())
        bucket.add(str(r.q87.c.DLMM))
        for row in template.get("fixed_accounts") or []:
            if row:
                bucket.add(str(row[0]))

    freq = Counter()
    for bucket in per_token.values():
        freq.update(bucket)

    return freq, len(per_token)


def _compile_size_with_synthetic_alt(
    payer,
    instructions,
    alt_key,
    alt_addresses,
    blockhash,
):
    c = r.q87.c
    pb = c.b58d(payer)
    order_b = []
    meta_b = {}

    def touch(pk, signer=False, writable=False, program=False):
        b = c.b58d(str(pk))
        if b not in meta_b:
            order_b.append(b)
            meta_b[b] = {
                "s": bool(signer),
                "w": bool(writable),
                "p": bool(program),
            }
        else:
            meta_b[b]["s"] |= bool(signer)
            meta_b[b]["w"] |= bool(writable)
            meta_b[b]["p"] |= bool(program)

    touch(payer, True, True, False)

    for ix in instructions:
        touch(ix["programId"], False, False, True)
        for a in ix.get("accounts") or []:
            touch(
                a["pubkey"],
                a.get("isSigner", False),
                a.get("isWritable", False),
                False,
            )

    if any(v["s"] and k != pb for k, v in meta_b.items()):
        raise RuntimeError("EXTRA_SIGNER")

    arr = [c.b58d(x) if isinstance(x, str) else bytes(x) for x in alt_addresses]
    pos = {b: i for i, b in enumerate(arr)}
    chosen = {}
    wr = []
    ro = []

    for b in order_b:
        m = meta_b[b]
        if b == pb or m["s"] or m["p"] or b not in pos:
            continue
        i = pos[b]
        if i > 255:
            continue
        chosen[b] = (i, m["w"])
        (wr if m["w"] else ro).append(i)

    static = [b for b in order_b if b not in chosen]
    sw = [b for b in static if meta_b[b]["s"] and meta_b[b]["w"] and b != pb]
    sr = [b for b in static if meta_b[b]["s"] and not meta_b[b]["w"]]
    uw = [b for b in static if not meta_b[b]["s"] and meta_b[b]["w"]]
    ur = [b for b in static if not meta_b[b]["s"] and not meta_b[b]["w"]]
    static = [pb] + sw + sr + uw + ur

    loaded_w = [arr[i] for i in wr]
    loaded_r = [arr[i] for i in ro]
    keys = static + loaded_w + loaded_r
    idx = {b: i for i, b in enumerate(keys)}

    msg = bytearray(
        b"\x80"
        + bytes([1, 0, len(ur)])
        + c.shortvec(len(static))
        + b"".join(static)
        + c.b58d(blockhash)
        + c.shortvec(len(instructions))
    )

    for ix in instructions:
        ac = [idx[c.b58d(a["pubkey"])] for a in ix.get("accounts") or []]
        dat = base64.b64decode(ix.get("data") or "")
        msg += (
            bytes([idx[c.b58d(ix["programId"])]])
            + c.shortvec(len(ac))
            + bytes(ac)
            + c.shortvec(len(dat))
            + dat
        )

    if wr or ro:
        msg += c.shortvec(1)
        msg += c.b58d(alt_key)
        msg += c.shortvec(len(wr)) + bytes(wr)
        msg += c.shortvec(len(ro)) + bytes(ro)
    else:
        msg += c.shortvec(0)

    raw = c.shortvec(1) + b"\0" * 64 + bytes(msg)

    return {
        "bytes": len(raw),
        "loaded_writable": len(wr),
        "loaded_readonly": len(ro),
        "loaded_total": len(wr) + len(ro),
    }


def _candidate_instructions(route):
    rows = list(r.q87.repaired_candidates(route))
    for row in rows:
        if str(row.get("name")) == "FULL":
            return "FULL", list(row["instructions"])

    for row in rows:
        if "PUMP_METEORA_ONLY" not in str(row.get("name", "")):
            return str(row.get("name", "UNKNOWN")), list(row["instructions"])

    raise RuntimeError("NO_FORWARD_CANDIDATE")


def analyze_route(user, route):
    alt_address = _state_alt_address()
    chain = _onchain_alt(alt_address)
    candidate_name, instructions = _candidate_instructions(route)
    blockhash = r.BLOCKHASH.get()

    order, meta = _instruction_meta(user, instructions)
    freq, warmed_tokens = _warm_frequency()
    existing = set(chain["addresses"])

    baseline = _compile_size_with_synthetic_alt(
        user,
        instructions,
        alt_address,
        chain["addresses"],
        blockhash,
    )

    rows = []
    eligible = []

    for pk in order:
        m = meta[pk]
        if pk in existing:
            category = "ALREADY_IN_ALT"
            eligible_now = False
        elif m["signer"]:
            category = "SIGNER"
            eligible_now = False
        elif m["program"]:
            category = "PROGRAM_ID"
            eligible_now = False
        elif pk == user:
            category = "NON_ALT_ELIGIBLE"
            eligible_now = False
        elif freq.get(pk, 0) >= 2:
            category = "STATIC_SHARED_CANDIDATE"
            eligible_now = True
        else:
            category = "PAIR_SPECIFIC"
            eligible_now = True

        rows.append({
            "pubkey": pk,
            "category": category,
            "signer": bool(m["signer"]),
            "program_id": bool(m["program"]),
            "writable": bool(m["writable"]),
            "warm_pair_frequency": int(freq.get(pk, 0)),
            "already_in_alt": pk in existing,
            "alt_eligible": bool(eligible_now),
        })

        if eligible_now:
            eligible.append(pk)

    shared = [
        pk for pk in eligible
        if freq.get(pk, 0) >= 2
    ]
    shared.sort(
        key=lambda pk: (
            -int(freq.get(pk, 0)),
            -int(bool(meta[pk]["writable"])),
            pk,
        )
    )

    pair_specific = [
        pk for pk in eligible
        if freq.get(pk, 0) < 2
    ]
    pair_specific.sort(
        key=lambda pk: (
            -int(bool(meta[pk]["writable"])),
            pk,
        )
    )

    current = list(chain["addresses"])
    shared_steps = []
    previous_size = baseline["bytes"]

    for pk in shared:
        if pk in current:
            continue
        projected = _compile_size_with_synthetic_alt(
            user,
            instructions,
            alt_address,
            current + [pk],
            blockhash,
        )
        shared_steps.append({
            "pubkey": pk,
            "frequency": int(freq.get(pk, 0)),
            "marginal_savings_bytes": int(previous_size - projected["bytes"]),
            "projected_bytes": int(projected["bytes"]),
        })
        current.append(pk)
        previous_size = projected["bytes"]

    universal_projection = _compile_size_with_synthetic_alt(
        user,
        instructions,
        alt_address,
        current,
        blockhash,
    )

    universal_add = [x["pubkey"] for x in shared_steps]
    strategy_a_pass = universal_projection["bytes"] <= MAX_TX_BYTES

    fallback_current = list(current)
    fallback_steps = []
    fallback_previous = universal_projection["bytes"]

    if not strategy_a_pass:
        for pk in pair_specific:
            if pk in fallback_current:
                continue
            projected = _compile_size_with_synthetic_alt(
                user,
                instructions,
                alt_address,
                fallback_current + [pk],
                blockhash,
            )
            fallback_steps.append({
                "pubkey": pk,
                "marginal_savings_bytes": int(fallback_previous - projected["bytes"]),
                "projected_bytes": int(projected["bytes"]),
            })
            fallback_current.append(pk)
            fallback_previous = projected["bytes"]
            if projected["bytes"] <= MAX_TX_BYTES:
                break

    fallback_projection = _compile_size_with_synthetic_alt(
        user,
        instructions,
        alt_address,
        fallback_current,
        blockhash,
    )

    report = {
        "status": (
            "STRATEGY_A_UNIVERSAL_ALT_PROJECTION_PASS"
            if strategy_a_pass
            else (
                "STRATEGY_B_ROUTE_CLASS_REQUIRED"
                if fallback_projection["bytes"] <= MAX_TX_BYTES
                else "NO_PROJECTED_ALT_SOLUTION"
            )
        ),
        "execution_authority": False,
        "paper_only": True,
        "broadcast": False,
        "mutation_performed": False,
        "candidate": candidate_name,
        "token": str(route.get("token") or ""),
        "canonical_alt": alt_address,
        "canonical_alt_owner": chain["owner"],
        "canonical_alt_address_count": len(chain["addresses"]),
        "canonical_alt_addresses": chain["addresses"],
        "warmed_token_count": warmed_tokens,
        "baseline_bytes_with_real_alt_contents": int(baseline["bytes"]),
        "max_tx_bytes": MAX_TX_BYTES,
        "excess_bytes": max(0, int(baseline["bytes"]) - MAX_TX_BYTES),
        "route_accounts": rows,
        "universal_shared_additions": universal_add,
        "universal_shared_steps": shared_steps,
        "universal_projected_bytes": int(universal_projection["bytes"]),
        "strategy_a_pass": bool(strategy_a_pass),
        "route_specific_fallback_steps": fallback_steps,
        "fallback_projected_bytes": int(fallback_projection["bytes"]),
        "strategy_b_physically_required_for_this_route": bool(
            (not strategy_a_pass)
            and fallback_projection["bytes"] <= MAX_TX_BYTES
        ),
    }

    _save(report)

    print(
        "[ALT_COVERAGE] table=%s onchain=%d route_accounts=%d warmed_tokens=%d"
        % (
            alt_address,
            len(chain["addresses"]),
            len(order),
            warmed_tokens,
        ),
        flush=True,
    )

    for row in rows:
        print(
            "[ALT_ACCOUNT] category=%s freq=%d signer=%s program=%s writable=%s pubkey=%s"
            % (
                row["category"],
                row["warm_pair_frequency"],
                row["signer"],
                row["program_id"],
                row["writable"],
                row["pubkey"],
            ),
            flush=True,
        )

    for row in shared_steps:
        print(
            "[ALT_SHARED_CANDIDATE] freq=%d save=%+d projected=%d pubkey=%s"
            % (
                row["frequency"],
                row["marginal_savings_bytes"],
                row["projected_bytes"],
                row["pubkey"],
            ),
            flush=True,
        )

    print(
        "[ALT_PROJECTION] baseline=%d universal=%d max=%d pass=%s additions=%d"
        % (
            baseline["bytes"],
            universal_projection["bytes"],
            MAX_TX_BYTES,
            strategy_a_pass,
            len(universal_add),
        ),
        flush=True,
    )

    if strategy_a_pass:
        print(
            "[ALT_STRATEGY_A_PASS] exact_projected_bytes=%d no_onchain_mutation=True"
            % universal_projection["bytes"],
            flush=True,
        )
    else:
        print(
            "[ALT_STRATEGY_A_HOLD] exact_projected_bytes=%d"
            % universal_projection["bytes"],
            flush=True,
        )
        print(
            "[ALT_STRATEGY_B_DIAGNOSTIC] fallback_projected_bytes=%d pair_specific_needed=%d"
            % (
                fallback_projection["bytes"],
                len(fallback_steps),
            ),
            flush=True,
        )

    print("[REPORT] %s" % REPORT, flush=True)
    print("[BROADCAST] disabled", flush=True)
    print("[ALT_MUTATION] disabled", flush=True)

    return report


def main():
    captured = {}
    original_compile = r.compile_current

    def diagnostic_compile(user, route):
        captured["report"] = analyze_route(user, route)
        return {
            "ok": False,
            "reason": "ALT_COVERAGE_DIAGNOSTIC_COMPLETE",
            "attempts": [],
        }

    r.compile_current = diagnostic_compile
    try:
        entry = getattr(cp, "main", None) or getattr(cp, "run", None)
        if entry is None:
            raise RuntimeError("CHECKPOINT2_ENTRYPOINT_MISSING")
        result = entry()
    finally:
        r.compile_current = original_compile

    if "report" not in captured:
        raise RuntimeError("CHECKPOINT2_DID_NOT_MATERIALIZE_ROUTE")

    return 0 if captured["report"]["status"] != "NO_PROJECTED_ALT_SOLUTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
