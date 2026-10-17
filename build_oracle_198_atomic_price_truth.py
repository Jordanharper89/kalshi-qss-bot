
"""ORACLE-198: inspect real PumpSwap execution bounds, no broadcast."""
import argparse
import base64
import os
import struct


def decode_bounds(ix):
    raw = base64.b64decode(ix.get("data", ""), validate=True)
    if len(raw) < 24:
        raise RuntimeError("ORACLE198_INVALID_PUMP_DATA")
    return (
        int(struct.unpack_from("<Q", raw, 8)[0]),
        int(struct.unpack_from("<Q", raw, 16)[0]),
    )


def test():
    raw = bytes(8) + struct.pack("<QQ", 12_345, 67_890)
    ix = {"data": base64.b64encode(raw).decode()}
    assert decode_bounds(ix) == (12_345, 67_890)
    print("[TEST PASS] ORACLE198 exact u64 buy/sell bound decoding")
    print("[SCOPE] no quote modifications; no broadcast")


def run():
    if os.getenv("QSB_LIVE_ARM", "").upper() == "YES":
        raise RuntimeError("ORACLE198_ARMED_REFUSED")

    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    helius = vault.load(db, vault.HELIUS)
    wallet = vault.load(db, vault.SOLANA)

    if not helius or not wallet:
        raise RuntimeError("ORACLE198_CREDENTIALS_MISSING")

    os.environ["QSB_SOLANA_PRIVATE_KEY"] = wallet
    os.environ["SOLANA_RPC_URL"] = (
        "https://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    os.environ["SOLANA_WS_URL"] = (
        "wss://mainnet.helius-rpc.com/?api-key="
        + vault.quote(helius, safe="")
    )
    os.environ["QSB_LIVE_ARM"] = "NO"

    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle197_reverse_bin_array_execution as execution
    )

    armed = getattr(r, "_live_010_armed", None)
    if not callable(armed) or armed():
        raise RuntimeError("ORACLE198_DISARM_NOT_CERTIFIED")

    original_sell = r.rewrite_pump_sell_bounds
    original_buy = r.rewrite_pump_buy_bounds
    original_reverse = r.same_snapshot_reverse_route

    def sell_bound(ix, base_in, min_quote):
        result = original_sell(ix, base_in, min_quote)
        actual_base, actual_min = decode_bounds(result)
        if actual_base != int(base_in) or actual_min != int(min_quote):
            raise RuntimeError("ORACLE198_SELL_BOUND_ENCODING_DRIFT")

        print(
            "[ORACLE198_SELL_BOUND] "
            "base_in_raw=%d min_quote_lamports=%d "
            "min_quote_sol=%.9f broadcast=FALSE"
            % (actual_base, actual_min, actual_min / 1e9),
            flush=True,
        )
        return result

    def buy_bound(ix, spend, minimum):
        result = original_buy(ix, spend, minimum)
        actual_spend, actual_min = decode_bounds(result)
        if actual_spend != int(spend) or actual_min != int(minimum):
            raise RuntimeError("ORACLE198_BUY_BOUND_ENCODING_DRIFT")

        print(
            "[ORACLE198_BUY_BOUND] "
            "spend_lamports=%d min_token_raw=%d broadcast=FALSE"
            % (actual_spend, actual_min),
            flush=True,
        )
        return result

    def reverse_route(user, snap, opportunity):
        start = int(opportunity.get("start") or 0)
        expected = int(opportunity.get("local_net") or 0)
        minimum = int(opportunity.get("local_min_end") or 0)
        minimum_net = int(opportunity.get("local_min_net") or 0)
        token_input = int(opportunity.get("net_token") or 0)

        print(
            "[ORACLE198_REVERSE_ECON] "
            "start_lamports=%d predicted_net=%d "
            "min_end_lamports=%d min_net=%d token_input_raw=%d"
            % (start, expected, minimum, minimum_net, token_input),
            flush=True,
        )

        if start <= 0 or minimum <= 0 or token_input <= 0:
            raise RuntimeError("ORACLE198_INVALID_ECONOMIC_BOUND")

        return original_reverse(user, snap, opportunity)

    r.rewrite_pump_sell_bounds = sell_bound
    r.rewrite_pump_buy_bounds = buy_bound
    r.same_snapshot_reverse_route = reverse_route

    try:
        print(
            "[ORACLE198_PATH] "
            "ORACLE197_FUNDED_REVERSE -> METEORA_SWAP2 "
            "-> PUMP_SELL -> SIGNED_SIM broadcast=FALSE",
            flush=True,
        )
        execution.worker()
    finally:
        r.rewrite_pump_sell_bounds = original_sell
        r.rewrite_pump_buy_bounds = original_buy
        r.same_snapshot_reverse_route = original_reverse

    print("[ORACLE198_COMPLETE] broadcast=FALSE", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.test:
        test()
    else:
        run()
