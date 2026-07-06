def trim(text, limit=3900):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit - 80] + "\n\n...shortened..."


def home_text():
    return """🏠 Q SERIES V2

Oracle finds the Plays.
Q Series executes the Plays.

Choose a section:"""


def home_keyboard():
    return {"inline_keyboard": [
        [{"text": "🔥 Live Plays", "callback_data": "live_plays"}],
        [{"text": "⚡ Top Scalp Plays", "callback_data": "plays_scalp"}],
        [{"text": "🎯 Same-Day Plays", "callback_data": "plays_same_day"}],
        [{"text": "💎 Top Value Plays", "callback_data": "plays_value"}],
        [{"text": "🧠 Oracle Snapshot", "callback_data": "oracle_snapshot"}],
        [{"text": "🏈 Sports", "callback_data": "cat_sports"}],
        [{"text": "🌦 Weather", "callback_data": "cat_weather"}],
        [{"text": "₿ Bitcoin / Crypto", "callback_data": "cat_bitcoin"}],
    ]}


def back_keyboard():
    return {"inline_keyboard": [[{"text": "🏠 Home", "callback_data": "home"}]]}


def format_play_card(play):
    return f"""🔥 PLAY CARD

Mission: {play.get('mission')}
Ticker: {play.get('ticker')}
Market: {play.get('title')}

Category: {play.get('category')}
Type: {play.get('play_type')}
Side: {play.get('side')}

Edge: {play.get('edge')}
Confidence: {play.get('confidence')}%
Grade: {play.get('grade')}

Reason:
{play.get('reason')}
""".strip()


def format_play_list(title, plays):
    lines = [title, ""]
    if not plays:
        lines.append("No Plays found.")
        return "\n".join(lines)

    for i, p in enumerate(plays, 1):
        lines.append(f"{i}. {p.get('mission')} | {p.get('ticker')}")
        lines.append(f"   {p.get('title')}")
        lines.append(f"   Edge: {p.get('edge')} | Conf: {p.get('confidence')} | Grade: {p.get('grade')}")
        if p.get("reason"):
            lines.append(f"   {str(p.get('reason'))[:180]}")
        lines.append("")
    return trim("\n".join(lines))


def format_snapshot(snapshot):
    lines = ["🧠 ORACLE SNAPSHOT", ""]
    for k, v in snapshot.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)
