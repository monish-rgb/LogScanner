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
            f"resp_ms={entry.response_time_ms} "
            f"dept={entry.department} "
            f"location={entry.location} "
            f"proto={entry.protocol} "
            f"method={entry.request_method} "
            f"server={entry.server_ip} "
            f"resp_size={entry.response_size} "
            f"req_size={entry.request_size} "
            f"status={entry.status_code} "
            f"content_type={entry.content_type} "
            f"ua={entry.user_agent} "
            f"threat={entry.threat_name} "
            f"threat_class={entry.threat_class} "
            f"threat_cat={entry.threat_category} "
            f"threat_sev={entry.threat_severity} "
            f"file_type={entry.file_type} "
            f"file_class={entry.file_class}"
        )
    return "\n".join(lines)
