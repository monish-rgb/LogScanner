ENTRIES_PER_CHUNK = 500


def chunk_log_entries(entries, max_entries=ENTRIES_PER_CHUNK):
    return [entries[i:i + max_entries] for i in range(0, len(entries), max_entries)]


def format_entries_for_prompt(entries):
    lines = []
    for entry in entries:
        lines.append(
            f"[Line {entry.line_number}] "
            f"ts={entry.timestamp} "
            f"src={entry.source_ip} "
            f"url={entry.destination_url} "
            f"user={entry.user} "
            f"action={entry.action} "
            f"category={entry.category} "
            f"risk={entry.risk_score} "
            f"bytes={entry.bytes_transferred} "
            f"resp_ms={entry.response_time_ms}"
        )
    return "\n".join(lines)
