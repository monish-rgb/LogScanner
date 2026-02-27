import re
import json
import csv
import io
from datetime import datetime

from .base_parser import BaseParser


class ZScalerParser(BaseParser):
    ZSCALER_KV_FIELDS = {
        "reason", "action", "event_id", "protocol", "transactionsize",
        "responsesize", "requestsize", "urlcategory", "serverip",
        "clienttranstime", "requestmethod", "refererURL", "useragent",
        "product", "location", "ClientIP", "status", "url", "login",
        "department", "threatname", "threatclass", "dlpdictionaries",
        "fileclass", "filetype", "pagerisk", "devicename",
    }

    ZSCALER_JSON_FIELDS = {
        "ClientIP", "action", "datetime", "urlcategory", "url",
        "login", "department", "protocol", "requestmethod",
        "serverip", "transactionsize", "responsesize", "requestsize",
    }

    FIELD_MAP = {
        "clientip": "source_ip",
        "src": "source_ip",
        "sourceip": "source_ip",
        "url": "destination_url",
        "eurl": "destination_url",
        "destination_url": "destination_url",
        "login": "user",
        "suser": "user",
        "usrname": "user",
        "user": "user",
        "action": "action",
        "reason": "action",
        "urlcategory": "category",
        "urlcat": "category",
        "category": "category",
        "pagerisk": "risk_score",
        "risk_score": "risk_score",
        "riskscore": "risk_score",
        "transactionsize": "bytes_transferred",
        "bytes_transferred": "bytes_transferred",
        "bytestransferred": "bytes_transferred",
        "clienttranstime": "response_time_ms",
        "response_time_ms": "response_time_ms",
        "responsetime": "response_time_ms",
        "datetime": "timestamp",
        "timestamp": "timestamp",
    }

    TIMESTAMP_PATTERN = re.compile(
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"
    )
    KV_PATTERN = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|[^\s]+)')

    CSV_HEADERS = [
        "timestamp", "source_ip", "action", "destination_url",
        "user", "category", "risk_score", "bytes_transferred",
        "response_time_ms",
    ]

    def can_parse(self, sample_lines):
        if not sample_lines:
            return False
        for line in sample_lines:
            if not line:
                continue
            if self._detect_format(line):
                return True
        return False

    def _detect_format(self, line):
        line = line.strip()
        if not line:
            return None

        # JSON format
        if line.startswith("{"):
            try:
                data = json.loads(line)
                zscaler_keys = {"ClientIP", "action", "urlcategory", "url", "login", "datetime"}
                if len(set(data.keys()) & zscaler_keys) >= 2:
                    return "json"
                if len(data.keys()) >= 3:
                    return "json"
            except json.JSONDecodeError:
                pass

        # Key-value format (with or without leading timestamp)
        kv_matches = self.KV_PATTERN.findall(line)
        if len(kv_matches) >= 3:
            keys = {m[0].lower() for m in kv_matches}
            if keys & {"action", "clientip", "url", "reason", "protocol", "product", "urlcategory"}:
                return "kv"
            if len(kv_matches) >= 5:
                return "kv"

        # CSV format
        if "," in line:
            try:
                reader = csv.reader(io.StringIO(line))
                fields = next(reader)
                if len(fields) >= 5:
                    return "csv"
            except csv.Error:
                pass

        return None

    def parse_line(self, line, line_number):
        fmt = self._detect_format(line)
        if fmt == "json":
            parsed = self._parse_json_line(line)
        elif fmt == "kv":
            parsed = self._parse_kv_line(line)
        elif fmt == "csv":
            parsed = self._parse_csv_line(line)
        else:
            parsed = {}

        parsed["line_number"] = line_number
        return parsed

    def _parse_json_line(self, line):
        data = json.loads(line)
        return self._map_fields({k.lower(): v for k, v in data.items()})

    def _parse_kv_line(self, line):
        result = {}

        # Extract leading timestamp if present
        ts_match = self.TIMESTAMP_PATTERN.match(line)
        if ts_match:
            result["timestamp"] = ts_match.group(1)

        # Extract key=value pairs
        kv_matches = self.KV_PATTERN.findall(line)
        raw = {}
        for key, value in kv_matches:
            value = value.strip('"')
            raw[key.lower()] = value

        mapped = self._map_fields(raw)
        if "timestamp" not in mapped and "timestamp" in result:
            mapped["timestamp"] = result["timestamp"]
        return mapped

    def _parse_csv_line(self, line):
        reader = csv.reader(io.StringIO(line))
        fields = next(reader)
        raw = {}
        for i, value in enumerate(fields):
            if i < len(self.CSV_HEADERS):
                raw[self.CSV_HEADERS[i]] = value.strip()
            else:
                raw[f"field_{i}"] = value.strip()
        return self._map_fields(raw)

    def _map_fields(self, raw):
        result = {}
        for raw_key, value in raw.items():
            mapped_key = self.FIELD_MAP.get(raw_key)
            if mapped_key:
                result[mapped_key] = self._convert_value(mapped_key, value)
        return result

    def _convert_value(self, field, value):
        if value is None or value == "" or value == "None" or value == "none":
            return None

        if field == "timestamp":
            return self._parse_timestamp(value)
        elif field in ("risk_score", "bytes_transferred", "response_time_ms"):
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return str(value)

    def _parse_timestamp(self, value):
        if isinstance(value, datetime):
            return value

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %Y %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        # Try Unix timestamp
        try:
            ts = float(value)
            if ts > 1e12:
                ts = ts / 1000
            return datetime.utcfromtimestamp(ts)
        except (ValueError, TypeError, OSError):
            pass

        return None
