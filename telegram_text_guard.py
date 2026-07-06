
"""
KQ-020 Telegram Text Guard

Prevents Telegram edit/send failures caused by oversized messages.
Telegram text limit is roughly 4096 chars, so we cap at 3900.
"""

MAX_TEXT = 3900
_INSTALLED = False


def _shorten(text):
    text = str(text or "")
    if len(text) <= MAX_TEXT:
        return text
    footer = "\n\n⚠️ Message shortened by KQ-020 Telegram guard.\nUse CMD terminal for full output."
    return text[: MAX_TEXT - len(footer)] + footer


def install():
    global _INSTALLED
    if _INSTALLED:
        return

    try:
        import requests
    except Exception:
        return

    original_post = requests.post

    def guarded_post(url, *args, **kwargs):
        try:
            data = kwargs.get("data")
            js = kwargs.get("json")

            target = str(url or "")
            is_telegram_text = (
                "api.telegram.org" in target
                and (
                    "sendMessage" in target
                    or "editMessageText" in target
                    or "sendPhoto" in target
                    or "editMessageCaption" in target
                )
            )

            if is_telegram_text:
                if isinstance(js, dict):
                    if "text" in js:
                        js["text"] = _shorten(js.get("text"))
                    if "caption" in js:
                        js["caption"] = _shorten(js.get("caption"))
                    kwargs["json"] = js

                if isinstance(data, dict):
                    if "text" in data:
                        data["text"] = _shorten(data.get("text"))
                    if "caption" in data:
                        data["caption"] = _shorten(data.get("caption"))
                    kwargs["data"] = data

        except Exception:
            pass

        return original_post(url, *args, **kwargs)

    requests.post = guarded_post
    _INSTALLED = True
