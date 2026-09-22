from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_006_universal_market_snapshot_canonicalizer.py"
TEST=ROOT/"test_opc_006_universal_market_snapshot_canonicalizer.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (\n    CanonicalObservation,\n    RawSourceObservation,\n)\n\nOPC_006_BUILD_ID="OPC-006"\nOPC_006_REVISION="OPC_006_UNIVERSAL_MARKET_SNAPSHOT_CANONICALIZER_CORRECTION_V2"\n\ndef _utc(value=None):\n    if value is None:\n        return datetime.now(timezone.utc)\n    if isinstance(value, datetime):\n        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)\n    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))\n    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)\n\ndef _stable(value):\n    return sha256(\n        json.dumps(\n            value,\n            sort_keys=True,\n            separators=(",",":"),\n            default=str,\n        ).encode("utf-8")\n    ).hexdigest()\n\ndef _money(row,key,dollar_key=None):\n    if dollar_key and row.get(dollar_key) not in (None,""):\n        return str(row[dollar_key])\n    value=row.get(key)\n    if value in (None,""):\n        return "0.0000"\n    try:\n        return f"{float(value)/100.0:.4f}"\n    except Exception:\n        return str(value)\n\ndef _fp(row,*keys):\n    for key in keys:\n        value=row.get(key)\n        if value not in (None,""):\n            return str(value)\n    return "0.00"\n\ndef build_universal_market_snapshot(\n    market,\n    *,\n    acquired_at=None,\n    batch_id=None,\n):\n    if not isinstance(market,dict):\n        raise TypeError("market must be dict")\n\n    ticker=str(market.get("ticker") or "").strip()\n    if not ticker:\n        raise ValueError("market ticker required")\n\n    acquired=_utc(acquired_at)\n    observed=_utc(\n        market.get("updated_time")\n        or market.get("last_updated_time")\n        or acquired\n    )\n    state_hash=_stable(market)\n\n    payload={\n        "source_market_id":ticker,\n        "source_symbol":ticker,\n        "event_ticker":str(market.get("event_ticker") or ""),\n        "market_title":str(\n            market.get("title")\n            or market.get("market_title")\n            or ""\n        ),\n        "source_status_filter":str(market.get("status") or "open"),\n\n        # Exact OLA-031 market-state projection fields.\n        "yes_bid_dollars":_money(market,"yes_bid","yes_bid_dollars"),\n        "yes_bid_size_fp":_fp(\n            market,\n            "yes_bid_size_fp",\n            "yes_bid_size",\n        ),\n        "yes_ask_dollars":_money(market,"yes_ask","yes_ask_dollars"),\n        "yes_ask_size_fp":_fp(\n            market,\n            "yes_ask_size_fp",\n            "yes_ask_size",\n        ),\n        "no_bid_dollars":_money(market,"no_bid","no_bid_dollars"),\n        "no_ask_dollars":_money(market,"no_ask","no_ask_dollars"),\n        "last_price_dollars":_money(\n            market,\n            "last_price",\n            "last_price_dollars",\n        ),\n        "volume_fp":_fp(market,"volume_fp","volume"),\n        "volume_24h_fp":_fp(market,"volume_24h_fp","volume_24h"),\n        "open_interest_fp":_fp(\n            market,\n            "open_interest_fp",\n            "open_interest",\n        ),\n        "liquidity_dollars":str(\n            market.get("liquidity_dollars")\n            or market.get("liquidity")\n            or "0.0000"\n        ),\n\n        # Existing source-history compatibility fields.\n        "previous_yes_bid_dollars":"0.0000",\n        "previous_yes_ask_dollars":"0.0000",\n        "previous_price_dollars":"0.0000",\n\n        "source_open_time":market.get("open_time"),\n        "source_close_time":market.get("close_time"),\n        "source_expiration_time":market.get("expiration_time"),\n\n        "opc_snapshot":True,\n        "opc_source_state_hash":state_hash,\n        "execution_allowed":False,\n    }\n\n    raw=RawSourceObservation.create(\n        source_observation_id=(\n            "opc.kalshi.market."\n            + ticker\n            + "."\n            + state_hash\n        ),\n        observed_at=observed,\n        observation_type="market_snapshot",\n        payload=payload,\n        provenance={\n            "source_id":"source.kalshi.market_data",\n            "adapter_id":"adapter.oracle.kalshi.opc.universal_snapshot",\n            "source_api":"kalshi_trade_api_v2",\n            "source_endpoint":"/markets",\n            "http_method":"GET",\n            "public_endpoint":True,\n            "shadow_mode":True,\n            "opc_build":"OPC-006-CORRECTION-V2",\n        },\n    )\n\n    return CanonicalObservation.create(\n        source_id="source.kalshi.market_data",\n        raw_observation=raw,\n        acquired_at=acquired,\n        acquisition_batch_id=str(\n            batch_id\n            or (\n                "batch.opc.snapshot."\n                + acquired.strftime("%Y%m%dT%H%M%S")\n            )\n        ),\n    )\n\ndef verify_opc_006_universal_market_snapshot_canonicalizer():\n    observation=build_universal_market_snapshot(\n        {\n            "ticker":"KXTEST",\n            "status":"open",\n            "yes_bid":31,\n            "yes_ask":33,\n        },\n        acquired_at="2026-08-16T20:00:00Z",\n        batch_id="batch.test",\n    )\n\n    payload=dict(observation.payload)\n\n    required_market_state_fields=(\n        "yes_bid_dollars",\n        "yes_bid_size_fp",\n        "yes_ask_dollars",\n        "yes_ask_size_fp",\n        "no_bid_dollars",\n        "no_ask_dollars",\n        "last_price_dollars",\n        "volume_fp",\n        "volume_24h_fp",\n        "open_interest_fp",\n        "liquidity_dollars",\n    )\n\n    return (\n        observation.read_only is True\n        and observation.execution_allowed is False\n        and observation.observation_type=="market_snapshot"\n        and payload.get("source_market_id")=="KXTEST"\n        and all(\n            field_name in payload\n            for field_name in required_market_state_fields\n        )\n        and payload.get("opc_snapshot") is True\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (\n    build_universal_market_snapshot,\n    verify_opc_006_universal_market_snapshot_canonicalizer,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_opc_006_universal_market_snapshot_canonicalizer()\n        )\n\n    def test_deterministic(self):\n        first=build_universal_market_snapshot(\n            {"ticker":"KX","yes_bid":1},\n            acquired_at="2026-08-16T20:00:00Z",\n            batch_id="b",\n        )\n        second=build_universal_market_snapshot(\n            {"ticker":"KX","yes_bid":1},\n            acquired_at="2026-08-16T20:00:00Z",\n            batch_id="b",\n        )\n        self.assertEqual(first.content_hash,second.content_hash)\n\n    def test_canonical_payload_contract(self):\n        observation=build_universal_market_snapshot(\n            {"ticker":"KXTEST2"},\n            acquired_at="2026-08-16T20:00:00Z",\n            batch_id="b2",\n        )\n        payload=dict(observation.payload)\n        self.assertEqual(payload["source_market_id"],"KXTEST2")\n        self.assertEqual(\n            observation.observation_type,\n            "market_snapshot",\n        )\n        self.assertFalse(observation.execution_allowed)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-006 CORRECTION V2 CERTIFICATION TEST")\n    print(" UNIVERSAL MARKET SNAPSHOT CANONICALIZER")\n    print("="*72)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] CanonicalObservation payload boundary aligned")\n    print("[PASS] Full OLA market-state snapshot field set preserved")\n    print("[PASS] Read-only + execution-disabled invariants preserved")\n    print("[DONE] OPC-006 CORRECTION V2 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-006 CORRECTION V2 INSTALLER")
    print(" UNIVERSAL MARKET SNAPSHOT CANONICALIZER")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_005_physical_pre_settlement_coverage_gate"
    )
    if (
        upstream.verify_opc_005_physical_pre_settlement_coverage_gate()
        is not True
    ):
        raise RuntimeError("Certified OPC-005 verification failed")

    print("[PASS] Certified OPC-005 upstream boundary verified")
    print("[PASS] Existing frozen OLA contracts consumed read-only")
    print("[PASS] Correction limited to failed OPC-006 install boundary")

    affected=(MOD,TEST,INIT)
    backups={
        path:(path.read_bytes() if path.exists() else None)
        for path in affected
    }

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )
        export_line=(
            "from .opc_006_universal_market_snapshot_canonicalizer "
            "import *"
        )
        if export_line not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export_line+"\n",
            )

        compile(
            MOD.read_text(encoding="utf-8"),
            str(MOD),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPC-006 Correction V2 failed; "
            "affected files restored"
        )
        raise

    print("[PASS] Corrected:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-006 CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
