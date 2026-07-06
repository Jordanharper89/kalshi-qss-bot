from services.notification_service import notification_service


def notification_text():
    pending = notification_service.pending()
    diag = notification_service.diagnostics()

    lines = [
        "NOTIFICATION CENTER",
        "",
        f"Status: {diag.get('health')}",
        f"Queue: {diag.get('queue_size')}",
        f"Sent: {diag.get('sent_count')}",
        f"Queued: {diag.get('queued_count')}",
        f"Dropped: {diag.get('dropped_count')}",
        f"Sender Connected: {diag.get('has_sender')}",
        "",
    ]

    if not pending:
        lines.append("No pending notifications.")
        return "\n".join(lines).strip()

    lines.append("Pending:")
    lines.append("")

    for item in pending[-10:]:
        lines.append(f"- {item.get('title')} | {item.get('ticker') or 'N/A'}")

    return "\n".join(lines).strip()


def notification_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Flush Notifications", "callback_data": "notifications_flush"}],
            [{"text": "Refresh", "callback_data": "notifications"}],
            [{"text": "Back", "callback_data": "main_menu"}],
        ]
    }