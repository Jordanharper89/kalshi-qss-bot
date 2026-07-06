from services.service_registry import registry
from services.market_data_service import market_data_service
from services.order_manager import order_manager
from services.position_service import position_service
from services.trade_journal import trade_journal
from services.notification_service import notification_service
from services.oracle_watchlist import oracle_watchlist


def start_services():
    registry.register("market_data", market_data_service)
    registry.register("order_manager", order_manager)
    registry.register("position_service", position_service)
    registry.register("trade_journal", trade_journal)
    registry.register("notification_service", notification_service)
    registry.register("oracle_watchlist", oracle_watchlist)

    registry.start_all()

    print("Services started.")
    print(service_diagnostics())


def stop_services():
    registry.stop_all()
    print("Services stopped.")


def get_service(name):
    return registry.get(name)


def service_diagnostics():
    diagnostics = registry.diagnostics()

    lines = ["SERVICE DIAGNOSTICS", ""]

    if not diagnostics:
        lines.append("No services registered.")
        return "\n".join(lines)

    for name, info in diagnostics.items():
        lines.append(f"{name}: {info.get('health')}")
        lines.append(f"running: {info.get('running')}")
        lines.append(f"thread_alive: {info.get('thread_alive')}")
        lines.append(f"registered_tickers: {info.get('registered_tickers')}")
        lines.append(f"api_calls: {info.get('api_calls')}")
        lines.append(f"errors: {info.get('errors')}")
        lines.append(f"preview_count: {info.get('preview_count')}")
        lines.append(f"buy_count: {info.get('buy_count')}")
        lines.append(f"sell_count: {info.get('sell_count')}")
        lines.append(f"limit_count: {info.get('limit_count')}")
        lines.append(f"positions_count: {info.get('positions_count')}")
        lines.append(f"load_count: {info.get('load_count')}")
        lines.append(f"save_count: {info.get('save_count')}")
        lines.append(f"update_count: {info.get('update_count')}")
        lines.append(f"journal_events: {info.get('events')}")
        lines.append(f"journal_reads: {info.get('reads')}")
        lines.append(f"journal_writes: {info.get('writes')}")
        lines.append(f"notification_queue: {info.get('queue_size')}")
        lines.append(f"notification_sent: {info.get('sent_count')}")
        lines.append(f"notification_queued: {info.get('queued_count')}")
        lines.append(f"notification_dropped: {info.get('dropped_count')}")
        lines.append(f"notification_has_sender: {info.get('has_sender')}")
        lines.append(f"oracle_watch_count: {info.get('watch_count')}")
        lines.append(f"oracle_watch_reads: {info.get('reads')}")
        lines.append(f"oracle_watch_writes: {info.get('writes')}")
        lines.append("")

    return "\n".join(lines).strip()


if __name__ == "__main__":
    start_services()
    stop_services()