from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json

from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import kalshi_rest_get, build_auth_headers
from .oad_026_persistent_stream_runner import (
    build_persistent_stream_config,
    next_reconnect_delay,
)

OAD_032_BUILD_ID = "OAD-032"
OAD_032_REVISION = "OAD_032_PERSISTENT_REAL_KALSHI_MESSAGE_LOOP_LIVENESS_CORRECTION_V3"

@dataclass(frozen=True)
class PersistentKalshiLoopSummary:
    connections: int
    reconnects: int
    subscription_acks: int
    market_messages: int
    last_message_type: str
    stopped_by_limit: bool

async def _run(credentials, max_market_messages, connect_timeout_seconds, progress):
    try:
        import websockets
        from websockets.exceptions import ConnectionClosed
    except Exception as e:
        raise RuntimeError("websockets package required") from e

    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
    from .oad_011_websocket_foundation import build_subscribe_command

    foundation = build_kalshi_adapter_foundation()

    market_response = kalshi_rest_get(
        credentials,
        "/markets",
        {"limit": 1000, "status": "open"},
        connect_timeout_seconds,
    )
    tickers = tuple(
        str(m["ticker"])
        for m in market_response.body.get("markets", ())
        if m.get("ticker")
    )[:100]

    if not tickers:
        raise RuntimeError("No open markets for persistent stream")

    connections = 0
    reconnects = 0
    subscription_acks = 0
    market_messages = 0
    last_message_type = ""
    reconnect_attempt = 0
    config = build_persistent_stream_config()

    def limit_reached():
        return (
            max_market_messages is not None
            and market_messages >= int(max_market_messages)
        )

    while not limit_reached():
        headers = build_auth_headers(
            credentials,
            "GET",
            "/trade-api/ws/v2",
        )

        # IMPORTANT:
        # Do not treat a quiet market-data interval as a failed connection.
        # websockets handles WebSocket Ping/Pong control frames automatically.
        kwargs = {
            "open_timeout": float(connect_timeout_seconds),
            "ping_interval": 20.0,
            "ping_timeout": 20.0,
            "close_timeout": 10.0,
        }

        try:
            try:
                connection = websockets.connect(
                    foundation.predictions_ws_url,
                    additional_headers=headers,
                    **kwargs,
                )
            except TypeError:
                connection = websockets.connect(
                    foundation.predictions_ws_url,
                    extra_headers=headers,
                    **kwargs,
                )

            async with connection as ws:
                connections += 1
                reconnect_attempt = 0

                await ws.send(
                    json.dumps(
                        build_subscribe_command(
                            1,
                            ("ticker", "trade"),
                            tickers,
                        ),
                        separators=(",", ":"),
                    )
                )

                progress(
                    f"[KALSHI] connected markets={len(tickers)} "
                    f"connections={connections}"
                )

                async for raw in ws:
                    msg = json.loads(raw)
                    message_type = str(msg.get("type", ""))
                    last_message_type = message_type

                    if message_type in ("subscribed", "ok"):
                        subscription_acks += 1
                        progress(
                            f"[KALSHI] subscription_ack={subscription_acks}"
                        )

                    elif message_type in (
                        "ticker",
                        "trade",
                        "orderbook_snapshot",
                        "orderbook_delta",
                    ):
                        market_messages += 1
                        progress(
                            f"[KALSHI] market_event={market_messages} "
                            f"type={message_type}"
                        )

                        if limit_reached():
                            break

                    elif message_type == "error":
                        progress(
                            "[KALSHI] server_message=error "
                            + str(msg.get("msg", {}))
                        )

        except asyncio.CancelledError:
            raise

        except KeyboardInterrupt:
            raise

        except ConnectionClosed as exc:
            reconnects += 1
            delay = next_reconnect_delay(reconnect_attempt, config)
            reconnect_attempt += 1
            progress(
                f"[KALSHI] websocket_closed code={getattr(exc, 'code', None)}; "
                f"reconnects={reconnects}; reconnecting in {delay:.1f}s"
            )
            await asyncio.sleep(delay)

        except Exception as exc:
            reconnects += 1
            delay = next_reconnect_delay(reconnect_attempt, config)
            reconnect_attempt += 1
            progress(
                f"[KALSHI] connection_failure={type(exc).__name__}; "
                f"reconnects={reconnects}; reconnecting in {delay:.1f}s"
            )
            await asyncio.sleep(delay)

    return PersistentKalshiLoopSummary(
        connections,
        reconnects,
        subscription_acks,
        market_messages,
        last_message_type,
        max_market_messages is not None,
    )

def run_persistent_kalshi_loop(
    root=None,
    max_market_messages=None,
    connect_timeout_seconds=15,
    progress=print,
):
    credentials = load_kalshi_credentials(root=root)
    return asyncio.run(
        _run(
            credentials,
            max_market_messages,
            connect_timeout_seconds,
            progress,
        )
    )

def verify_oad_032_persistent_real_kalshi_message_loop():
    import inspect

    sig = inspect.signature(run_persistent_kalshi_loop)
    source = inspect.getsource(_run)

    return (
        sig.parameters["max_market_messages"].default is None
        and "async for raw in ws" in source
        and "wait_for(ws.recv" not in source
        and OAD_032_REVISION.endswith("LIVENESS_CORRECTION_V3")
    )
