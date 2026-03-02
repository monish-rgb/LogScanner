# /**
#  * AI USAGE: This file uses the Anthropic Claude API (claude-sonnet-4-20250514) for
#   - Analyzing batches of parsed log entries for security anomalies
#   - Returns anomaly classifications with anomaly_type, severity, confidence_score, and explanations as JSON
#  */

import json
import re
import time

import anthropic
from flask import current_app

from app.extensions import db
from app.models.log_file import LogFile
from app.models.log_entry import LogEntry
from app.models.analysis_result import AnalysisResult
from app.utils.chunking import chunk_log_entries, format_entries_for_prompt

SYSTEM_PROMPT = """You are a Security Operations Center (SOC) analyst AI assistant.
You analyze web proxy log entries to detect security anomalies.

For each anomaly you detect, respond with a JSON array of objects:
[
  {
    "line_number": <int>,
    "anomaly_type": "<string: one of data_exfiltration, suspicious_url, brute_force, unusual_traffic_volume, policy_violation, malware_communication, credential_stuffing, dns_tunneling, unauthorized_access>",
    "confidence_score": <float 0.0-1.0>,
    "severity": "<string: low|medium|high|critical>",
    "explanation": "<string: 1-2 sentence explanation of why this is anomalous>"
  }
]

If no anomalies are found, return an empty array: []

Focus on:
- Unusually large data transfers (bytes_transferred)
- Connections to suspicious/uncategorized URLs
- Blocked actions that repeat from the same source
- High risk scores
- Abnormal response times
- Access to high-risk URL categories
- Patterns suggesting data exfiltration
- Unusual number of requests from a single IP in a short time frame
- Repeated failed/blocked attempts from the same user or IP

IMPORTANT:
- Return at most ONE anomaly per line_number. If a single log entry matches multiple anomaly types, report only the MOST severe/relevant one.
- Respond ONLY with the JSON array. No other text."""


def analyze_log_file(log_file_id):
    log_file = LogFile.query.get(log_file_id)
    if not log_file:
        raise ValueError("Log file not found")

    log_file.analysis_status = "analyzing"
    db.session.commit()

    try:
        entries = (
            LogEntry.query
            .filter_by(log_file_id=log_file_id)
            .order_by(LogEntry.line_number)
            .all()
        )

        if not entries:
            log_file.analysis_status = "completed"
            db.session.commit()
            return []

        chunks = chunk_log_entries(entries)
        all_results = []

        api_key = current_app.config.get("ANTHROPIC_API_KEY")
        model = current_app.config.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        client = anthropic.Anthropic(api_key=api_key)

        for chunk_index, chunk in enumerate(chunks):
            formatted = format_entries_for_prompt(chunk)
            print("Formatted entries:", formatted,flush=True)
            message = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Analyze these web proxy log entries for security anomalies:\n\n{formatted}",
                }],
            )

            response_text = message.content[0].text
            anomalies = parse_claude_response(response_text)

            # Deduplicate: keep only the highest confidence anomaly per line
            best_per_line = {}
            for anomaly in anomalies:
                line_num = anomaly.get("line_number")
                existing = best_per_line.get(line_num)
                if not existing or float(anomaly.get("confidence_score", 0)) > float(existing.get("confidence_score", 0)):
                    best_per_line[line_num] = anomaly
            anomalies = list(best_per_line.values())

            entry_map = {e.line_number: e for e in chunk}

            for anomaly in anomalies:
                line_num = anomaly.get("line_number")
                entry = entry_map.get(line_num)

                result = AnalysisResult(
                    log_file_id=log_file_id,
                    log_entry_id=entry.id if entry else None,
                    anomaly_type=anomaly.get("anomaly_type", "unknown"),
                    confidence_score=min(max(float(anomaly.get("confidence_score", 0.5)), 0.0), 1.0),
                    explanation=anomaly.get("explanation", "No explanation provided"),
                    severity=anomaly.get("severity", "medium"),
                )
                print("AI result",result,flush=True)
                db.session.add(result)
                all_results.append(result)

                if entry:
                    entry.is_anomalous = True

            db.session.commit()

            # Rate limiting between chunks
            if chunk_index < len(chunks) - 1:
                time.sleep(1)

        log_file.analysis_status = "completed"
        db.session.commit()
        return all_results

    except Exception as e:
        log_file.analysis_status = "failed"
        db.session.commit()
        raise e


def parse_claude_response(response_text):
    text = response_text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        anomalies = json.loads(text)
        if isinstance(anomalies, list):
            return anomalies
        return []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return []
        return []
