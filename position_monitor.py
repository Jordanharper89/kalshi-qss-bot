import time
import threading

from services.position_service import position_service


_running = False
_thread = None
_interval = 5.0


def check_positions_once():
    return position_service.refresh_all_positions()


def monitor_loop():
    global _running

    while _running:
        try:
            check_positions_once()
        except Exception as e:
            print(f"Position monitor error: {e}")

        time.sleep(_interval)


def start_position_monitor(send_message_fn=None, chat_id=None, interval=5.0):
    global _running, _thread, _interval

    if _running:
        return

    _interval = float(interval)
    _running = True

    _thread = threading.Thread(target=monitor_loop, daemon=True)
    _thread.start()

    print(f"Position monitor started. Interval: {_interval}s")


def stop_position_monitor():
    global _running

    _running = False
    print("Position monitor stopped.")


def position_monitor_status():
    return {
        "running": _running,
        "interval": _interval,
        "thread_alive": _thread.is_alive() if _thread else False,
    }


if __name__ == "__main__":
    updates = check_positions_once()
    print("Position updates:")
    for ticker, item in updates.items():
        print(ticker, item)