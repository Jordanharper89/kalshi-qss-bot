from pathlib import Path
import json
import re

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

root=Path.cwd()

with connect(root,autocommit=False) as c:
    with c.cursor() as q:

        q.execute("SET TRANSACTION READ ONLY")
        q.execute("SET LOCAL statement_timeout='10000ms'")

        q.execute(
            """
            SELECT
                sequence_number,
                observed_at,
                canonical_observation_json
            FROM public.oracle_canonical_observations
            WHERE source_id='source.kalshi.market_data'
            ORDER BY sequence_number DESC
            LIMIT 50000
            """
        )

        rows=q.fetchall() or []

    c.rollback()

found={}

for seq,ts,obj in rows:

    try:
        d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:
        continue

    text=json.dumps(d,separators=(",",":"))

    tickers=re.findall(
        r'KXBTC15M-[A-Z0-9-]+',
        text.upper(),
    )

    for ticker in tickers:
        if ticker not in found:
            found[ticker]=(seq,ts,d)

print("[RECENT_KALSHI_ROWS_SCANNED]",len(rows))
print("[BTC15M_TICKERS]",len(found))

for ticker,(seq,ts,d) in list(found.items())[:20]:

    print(
        "[BTC15M]",
        ticker,
        "sequence=",seq,
        "observed_at=",ts,
    )

    payload={}

    if isinstance(d,dict):
        raw=d.get("raw_observation",{})
        if isinstance(raw,dict):
            payload=raw.get("payload",{}) or {}

    if isinstance(payload,dict):

        view={
            k:payload.get(k)
            for k in (
                "ticker",
                "event_ticker",
                "title",
                "subtitle",
                "yes_bid",
                "yes_ask",
                "last_price",
                "close_time",
                "expiration_time",
                "status",
            )
            if k in payload
        }

        print("[PAYLOAD]",view)

assert found,"no recent KXBTC15M ticker found in latest Kalshi canonical observations"

print("[PASS] OPA-010 exact BTC15M discovery from current Kalshi stream complete")
