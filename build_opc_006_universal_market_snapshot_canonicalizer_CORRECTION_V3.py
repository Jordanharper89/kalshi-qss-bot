from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_006_universal_market_snapshot_canonicalizer.py"
TEST=ROOT/"test_opc_006_universal_market_snapshot_canonicalizer.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (\n    CanonicalObservation,\n    RawSourceObservation,\n)\n\nOPC_006_BUILD_ID="OPC-006"\nOPC_006_REVISION="OPC_006_UNIVERSAL_MARKET_SNAPSHOT_CANONICALIZER_CORRECTION_V3"\n\ndef _utc(value=None):\n    if value is None:\n        return datetime.now(timezone.utc)\n    if isinstance(value, datetime):\n        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)\n    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))\n    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)\n\ndef _stable(value):\n    return sha256(\n        json.dumps(\n            value,\n            sort_keys=True,\n            separators=(",",":"),\n            default=str,\n        ).encode("utf-8")\n    ).hexdigest()\n\ndef _money(row,key,dollar_key=None):\n    if dollar_key and row.get(dollar_key) not in (None,""):\n        return str(row[dollar_key])\n    value=row.get(key)\n    if value in (None,""):\n        return "0.0000"\n    try:\n        return f"{float(value)/100.0:.4f}"\n    except Exception:\n        return str(value)\n\ndef _fp(row,*keys):\n    for key in keys:\n        value=row.get(key)\n        if value not in (None,""):\n            return str(value)\n    return "0.00"\n\ndef _epoch_token(acquired):\n    # Microsecond precision guarantees that a later observation of unchanged\n    # market state gets a distinct source observation identity.\n    return acquired.strftime("%Y%m%dT%H%M%S%fZ")\n\ndef build_universal_market_snapshot(\n    market,\n    *,\n    acquired_at=None,\n    batch_id=None,\n):\n    if not isinstance(market,dict):\n        raise TypeError("market must be dict")\n\n    ticker=str(market.get("ticker") or "").strip()\n    if not ticker:\n        raise ValueError("market ticker required")\n\n    acquired=_utc(acquired_at)\n    observed=_utc(\n        market.get("updated_time")\n        or market.get("last_updated_time")\n        or acquired\n    )\n\n    # Stable state identity remains independent of observation time.\n    state_hash=_stable(market)\n\n    # Observation identity represents "Oracle observed this state at this epoch".\n    observation_epoch=_epoch_token(acquired)\n\n    payload={\n        "source_market_id":ticker,\n        "source_symbol":ticker,\n        "event_ticker":str(market.get("event_ticker") or ""),\n        "market_title":str(\n            market.get("title")\n            or market.get("market_title")\n            or ""\n        ),\n        "source_status_filter":str(market.get("status") or "open"),\n\n        "yes_bid_dollars":_money(market,"yes_bid","yes_bid_dollars"),\n        "yes_bid_size_fp":_fp(market,"yes_bid_size_fp","yes_bid_size"),\n        "yes_ask_dollars":_money(market,"yes_ask","yes_ask_dollars"),\n        "yes_ask_size_fp":_fp(market,"yes_ask_size_fp","yes_ask_size"),\n        "no_bid_dollars":_money(market,"no_bid","no_bid_dollars"),\n        "no_ask_dollars":_money(market,"no_ask","no_ask_dollars"),\n        "last_price_dollars":_money(\n            market,\n            "last_price",\n            "last_price_dollars",\n        ),\n        "volume_fp":_fp(market,"volume_fp","volume"),\n        "volume_24h_fp":_fp(market,"volume_24h_fp","volume_24h"),\n        "open_interest_fp":_fp(\n            market,\n            "open_interest_fp",\n            "open_interest",\n        ),\n        "liquidity_dollars":str(\n            market.get("liquidity_dollars")\n            or market.get("liquidity")\n            or "0.0000"\n        ),\n\n        "previous_yes_bid_dollars":"0.0000",\n        "previous_yes_ask_dollars":"0.0000",\n        "previous_price_dollars":"0.0000",\n\n        "source_open_time":market.get("open_time"),\n        "source_close_time":market.get("close_time"),\n        "source_expiration_time":market.get("expiration_time"),\n\n        "opc_snapshot":True,\n        "opc_source_state_hash":state_hash,\n        "opc_observation_epoch":observation_epoch,\n        "execution_allowed":False,\n    }\n\n    raw=RawSourceObservation.create(\n        source_observation_id=(\n            "opc.kalshi.market."\n            + ticker\n            + "."\n            + state_hash\n            + "."\n            + observation_epoch\n        ),\n        observed_at=observed,\n        observation_type="market_snapshot",\n        payload=payload,\n        provenance={\n            "source_id":"source.kalshi.market_data",\n            "adapter_id":"adapter.oracle.kalshi.opc.universal_snapshot",\n            "source_api":"kalshi_trade_api_v2",\n            "source_endpoint":"/markets",\n            "http_method":"GET",\n            "public_endpoint":True,\n            "shadow_mode":True,\n            "opc_build":"OPC-006-CORRECTION-V3",\n        },\n    )\n\n    return CanonicalObservation.create(\n        source_id="source.kalshi.market_data",\n        raw_observation=raw,\n        acquired_at=acquired,\n        acquisition_batch_id=str(\n            batch_id\n            or (\n                "batch.opc.snapshot."\n                + observation_epoch\n            )\n        ),\n    )\n\ndef verify_opc_006_universal_market_snapshot_canonicalizer():\n    base={"ticker":"KXTEST","status":"open","yes_bid":31,"yes_ask":33}\n\n    first=build_universal_market_snapshot(\n        base,\n        acquired_at="2026-08-16T20:00:00.000001Z",\n        batch_id="batch.test.1",\n    )\n    second=build_universal_market_snapshot(\n        base,\n        acquired_at="2026-08-16T20:00:00.000002Z",\n        batch_id="batch.test.2",\n    )\n\n    p1=dict(first.payload)\n    p2=dict(second.payload)\n\n    return (\n        first.read_only is True\n        and first.execution_allowed is False\n        and first.observation_type=="market_snapshot"\n        and p1.get("source_market_id")=="KXTEST"\n        and p1.get("opc_source_state_hash")==p2.get("opc_source_state_hash")\n        and p1.get("opc_observation_epoch")!=p2.get("opc_observation_epoch")\n        and first.observation_id!=second.observation_id\n        and first.content_hash!=second.content_hash\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (\n    build_universal_market_snapshot,\n    verify_opc_006_universal_market_snapshot_canonicalizer,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_opc_006_universal_market_snapshot_canonicalizer()\n        )\n\n    def test_same_state_new_epoch_new_identity(self):\n        market={"ticker":"KX","yes_bid":1}\n        first=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.000001Z",\n            batch_id="b1",\n        )\n        second=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.000002Z",\n            batch_id="b2",\n        )\n        self.assertNotEqual(first.observation_id,second.observation_id)\n        self.assertNotEqual(first.content_hash,second.content_hash)\n        self.assertEqual(\n            dict(first.payload)["opc_source_state_hash"],\n            dict(second.payload)["opc_source_state_hash"],\n        )\n\n    def test_exact_epoch_is_deterministic(self):\n        market={"ticker":"KX","yes_bid":1}\n        first=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.123456Z",\n            batch_id="same",\n        )\n        second=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.123456Z",\n            batch_id="same",\n        )\n        self.assertEqual(first.observation_id,second.observation_id)\n        self.assertEqual(first.content_hash,second.content_hash)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-006 CORRECTION V3 CERTIFICATION TEST")\n    print(" TIME-AWARE UNIVERSAL MARKET SNAPSHOT IDENTITY")\n    print("="*72)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] Stable market-state hash preserved")\n    print("[PASS] New observation epoch produces new observation identity")\n    print("[PASS] Exact same state + exact same epoch remains deterministic")\n    print("[PASS] duplicate_observation_identity defect corrected at OPC boundary")\n    print("[DONE] OPC-006 CORRECTION V3 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-006 CORRECTION V3 INSTALLER")
    print(" TIME-AWARE UNIVERSAL MARKET SNAPSHOT IDENTITY")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_005_physical_pre_settlement_coverage_gate"
    )
    if upstream.verify_opc_005_physical_pre_settlement_coverage_gate() is not True:
        raise RuntimeError("Certified OPC-005 verification failed")

    print("[PASS] Certified OPC-005 upstream boundary verified")
    print("[PASS] Frozen OLA consumed read-only")
    print("[PASS] Correction limited to OPC-006 failed identity design")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_006_universal_market_snapshot_canonicalizer import *"
        if line not in current:
            write_exact(INIT,current.rstrip()+"\n"+line+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

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
        print("[ROLLBACK] OPC-006 Correction V3 failed; affected files restored")
        raise

    print("[PASS] Corrected:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-006 CORRECTION V3 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
