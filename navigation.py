import copy
import time
from typing import Any, Dict, List, Optional

_MAX_HISTORY = 20
_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
_CURRENT: Dict[str, Dict[str, Any]] = {}

_TRANSIENT_WORDS = [
    "SUBMITTING",
    "RUNNING",
    "Loading orders",
    "Refreshing orders",
    "Sending order",
    "Sending cancel",
    "Status:\nRunning",
    "Status:\nLoading",
]


def _chat(chat_id) -> str:
    return str(chat_id or "")


def _text(value) -> str:
    return str(value or "")


def _is_home_text(text: str) -> bool:
    return _text(text).strip().upper().startswith("MAIN MENU")


def _is_transient(text: str) -> bool:
    text = _text(text)
    return any(word in text for word in _TRANSIENT_WORDS)


def _button_text(button: Dict[str, Any]) -> str:
    return str(button.get("text") or "").strip()


def _button_callback(button: Dict[str, Any]) -> str:
    return str(button.get("callback_data") or "").strip()


def _is_nav_row(row: List[Dict[str, Any]]) -> bool:
    if not row:
        return True

    labels = [_button_text(button).lower() for button in row]
    callbacks = [_button_callback(button) for button in row]

    # Remove old standalone back/home rows. Real action rows like Buy/Sell/View are preserved.
    if len(row) <= 2 and all(
        label in {"back", "home", "main menu", "back to main menu", "back to positions", "back to settings", "back to sell settings", "back to risk settings"}
        or label.startswith("back to")
        or callback in {"nav_back", "main_menu"}
        for label, callback in zip(labels, callbacks)
    ):
        return True

    return False


def _strip_old_nav(reply_markup: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not reply_markup or not isinstance(reply_markup, dict):
        return reply_markup

    rows = reply_markup.get("inline_keyboard")
    if not isinstance(rows, list):
        return copy.deepcopy(reply_markup)

    cleaned = []
    for row in rows:
        if not isinstance(row, list):
            continue
        if _is_nav_row(row):
            continue
        cleaned.append(copy.deepcopy(row))

    return {"inline_keyboard": cleaned}


def prepare_keyboard(chat_id, text: str, reply_markup: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Normalize every screen to use Back/Home navigation."""
    if not reply_markup:
        return reply_markup

    prepared = _strip_old_nav(reply_markup)
    rows = prepared.setdefault("inline_keyboard", [])

    if _is_home_text(text):
        return prepared

    rows.append([{"text": "Back", "callback_data": "nav_back"}])
    rows.append([{"text": "Home", "callback_data": "main_menu"}])
    return prepared


def _signature(state: Dict[str, Any]) -> str:
    return f"{state.get('text','')}|{state.get('reply_markup')}"


def record_screen(chat_id, text: str, reply_markup: Optional[Dict[str, Any]], push: bool = True) -> None:
    """Record a rendered screen and optionally push the previous screen onto history."""
    chat = _chat(chat_id)
    if not chat:
        return

    state = {
        "text": _text(text),
        "reply_markup": copy.deepcopy(reply_markup),
        "time": time.time(),
    }

    if _is_home_text(state["text"]):
        _CURRENT[chat] = state
        return

    old = _CURRENT.get(chat)

    if push and old and not _is_transient(state["text"]):
        if _signature(old) != _signature(state):
            stack = _HISTORY.setdefault(chat, [])
            if not stack or _signature(stack[-1]) != _signature(old):
                stack.append(copy.deepcopy(old))
            if len(stack) > _MAX_HISTORY:
                del stack[:-_MAX_HISTORY]

    _CURRENT[chat] = state


def pop_back_screen(chat_id) -> Optional[Dict[str, Any]]:
    chat = _chat(chat_id)
    stack = _HISTORY.get(chat) or []

    while stack:
        state = stack.pop()
        if state and not _is_transient(state.get("text", "")):
            _CURRENT[chat] = copy.deepcopy(state)
            return state

    return None


def clear_navigation(chat_id) -> None:
    chat = _chat(chat_id)
    _HISTORY.pop(chat, None)
    _CURRENT.pop(chat, None)


def navigation_status(chat_id) -> str:
    chat = _chat(chat_id)
    stack = _HISTORY.get(chat) or []
    current = _CURRENT.get(chat) or {}
    title = (current.get("text") or "").strip().splitlines()[0] if current.get("text") else "None"

    return f"""NAVIGATION STATUS

Current:
{title}

Back Stack:
{len(stack)} screen(s)

Controls:
Back = previous screen
Home = main menu""".strip()
