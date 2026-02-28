import json
import csv
import io
import re
from datetime import datetime

class ZScalerParser:
    FIELD_MAP = {
        "clientip": "source_ip",
        "url": "destination_url",
        "host": "destination_url",
        "login": "user",
        "user": "user",
        "action": "action",
        "urlcategory": "category",
        "pagerisk": "risk_score",
        "transactionsize": "bytes_transferred",
        "clienttranstime": "response_time_ms",
        "datetime": "timestamp",
        "department": "department",
        "location": "location",
        "protocol": "protocol",
        "requestmethod": "request_method",
        "serverip": "server_ip",
        "responsesize": "response_size",
        "requestsize": "request_size",
        "statuscode": "status_code",
        "status": "status_code",
        "contenttype": "content_type",
        "useragent": "user_agent",
        "threatname": "threat_name",
        "threatclass": "threat_class",
        "threatcategory": "threat_category",
        "threatseverity": "threat_severity",
        "filetype": "file_type",
        "fileclass": "file_class",
    }

    # Full ZScaler CSV format (27 fields)
    LOG_FIELDS = [
        "date", "time", "action", "login", "department", "location",
        "clientip", "host", "protocol", "statuscode", "requestmethod",
        "contenttype", "requestsize", "responsesize", "urlcategory",
        "pagerisk", "transactionsize", "clienttranstime", "serverip",
        "threatname", "threatclass", "threatcategory", "threatseverity",
        "filetype", "fileclass", "useragent", "url",
    ]

    # Compact ZScaler CSV format
    LOG_FIELDS_COMPACT = [
        "date", "time", "action", "login", "department", "location",
        "clientip", "host", "protocol", "statuscode", "requestmethod",
        "contenttype", "requestsize", "responsesize", "urlcategory",
        "pagerisk", "useragent", "url",
    ]

    #field validators for csv format
    FIELD_VALIDATORS = {
        "date":            lambda v: bool(re.match(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}", v)),
        "time":            lambda v: bool(re.match(r"\d{2}:\d{2}:\d{2}", v)),
        "action":          lambda v: v.upper() in ("ALLOWED", "BLOCKED", "ISOLATED", "ICAP_RESPONSE"),
        "login":           lambda v: "@" in v or v == "-",
        "clientip":        lambda v: bool(re.match(r"\d{1,3}(\.\d{1,3}){3}", v)),
        "statuscode":      lambda v: v.isdigit() and 100 <= int(v) <= 599,
        "requestmethod":   lambda v: v.upper() in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "CONNECT"),
        "requestsize":     lambda v: v.isdigit(),
        "responsesize":    lambda v: v.isdigit(),
        "pagerisk":        lambda v: v.isdigit() and 0 <= int(v) <= 100,
        "serverip":        lambda v: bool(re.match(r"\d{1,3}(\.\d{1,3}){3}", v)) or v == "-",
        "url":             lambda v: v.startswith("http://") or v.startswith("https://") or v == "-",
        "protocol":        lambda v: v.upper() in ("HTTP", "HTTPS", "FTP", "TUNNEL"),
    }

    def parse_file(self, filepath, log_file_id):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        stripped = content.strip()

        # Try multi-line JSON parsing first (array, single object, or concatenated objects)
        if stripped.startswith("[") or stripped.startswith("{"):
            json_entries = list(self._parse_json_content(content, log_file_id))
            if json_entries:
                yield from json_entries
                return

        # Fall back to CSV parsing — join continuation lines (ending with comma)
        accumulated = ""
        entry_number = 0

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            accumulated = accumulated + line if accumulated else line

            # Line ends with comma → continuation, keep accumulating
            if accumulated.endswith(","):
                continue

            # Complete record ready to parse
            entry_number += 1
            try:
                parsed = self.parse_line(accumulated, entry_number)
                parsed["log_file_id"] = log_file_id
                parsed["raw_line"] = accumulated
                yield parsed
            except Exception:
                yield {
                    "log_file_id": log_file_id,
                    "line_number": entry_number,
                    "raw_line": accumulated,
                }
            accumulated = ""

        # Handle any remaining accumulated line
        if accumulated:
            entry_number += 1
            try:
                parsed = self.parse_line(accumulated, entry_number)
                parsed["log_file_id"] = log_file_id
                parsed["raw_line"] = accumulated
                yield parsed
            except Exception:
                yield {
                    "log_file_id": log_file_id,
                    "line_number": entry_number,
                    "raw_line": accumulated,
                }

    def _parse_json_content(self, content, log_file_id):
        """Parse JSON content: array, single object, or concatenated multi-line objects."""
        # Remove trailing commas before } or ] (common in ZScaler exports)
        cleaned = re.sub(r',\s*([}\]])', r'\1', content.strip())

        # Try as a single JSON document (array or object)
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                for i, obj in enumerate(data, start=1):
                    if isinstance(obj, dict):
                        parsed = self._map_fields({k.lower(): v for k, v in obj.items()})
                        parsed["line_number"] = i
                        parsed["log_file_id"] = log_file_id
                        parsed["raw_line"] = json.dumps(obj)
                        yield parsed
                return
            elif isinstance(data, dict):
                parsed = self._map_fields({k.lower(): v for k, v in data.items()})
                parsed["line_number"] = 1
                parsed["log_file_id"] = log_file_id
                parsed["raw_line"] = json.dumps(data)
                yield parsed
                return
        except json.JSONDecodeError:
            pass

        # Try concatenated JSON objects (multiple objects not wrapped in an array)
        decoder = json.JSONDecoder()
        pos = 0
        entry_num = 0
        while pos < len(cleaned):
            # Skip whitespace
            while pos < len(cleaned) and cleaned[pos] in ' \t\n\r':
                pos += 1
            if pos >= len(cleaned):
                break
            if cleaned[pos] != '{':
                pos += 1
                continue
            try:
                obj, end_pos = decoder.raw_decode(cleaned, pos)
                entry_num += 1
                if isinstance(obj, dict):
                    parsed = self._map_fields({k.lower(): v for k, v in obj.items()})
                    parsed["line_number"] = entry_num
                    parsed["log_file_id"] = log_file_id
                    parsed["raw_line"] = json.dumps(obj)
                    yield parsed
                pos = end_pos
            except json.JSONDecodeError:
                pos += 1

    def can_parse(self, sample_lines):
        if not sample_lines:
            return False
        for line in sample_lines:
            if not line:
                continue
            fmt = self._detect_format(line)
            if fmt:
                return True
        return False

    def _detect_format(self, line):
        line = line.strip()
        if not line:
            return None

        # JSON format - single-line object or start of multi-line object/array
        if line.startswith("{") or line.startswith("["):
            return "json"

        # CSV format
        if "," in line:
            return "csv"

        return None

    def parse_line(self, line, line_number):
        fmt = self._detect_format(line)
        if fmt == "json":
            parsed = self._parse_json_line(line)
        elif fmt == "csv":
            parsed = self._parse_csv_line(line)
        else:
            parsed = {}

        parsed["line_number"] = line_number
        return parsed

    def _parse_json_line(self, line):
        data = json.loads(line)
        return self._map_fields({k.lower(): v for k, v in data.items()})


    # ─── Validate a single parsed row dict ────────────────────
    def _validate_csv_row(self, raw: dict) -> tuple[bool, list[str]]:
        """
        Returns (is_valid, list_of_issues).
        Skips validation for empty/dash/None values — they are optional fields.
        """
        issues = []
        for field, validator in self.FIELD_VALIDATORS.items():
            value = raw.get(field, "").strip()
            if not value or value in ("-", "None", "N/A"):
                continue  # skip missing/optional fields
            try:
                if not validator(value):
                    issues.append(f"Field '{field}' has unexpected value: '{value}'")
            except Exception as e:
                issues.append(f"Field '{field}' validator error: {e}")
        return (len(issues) == 0), issues

    # ─── detect CSV fields by value patterns ──────────────
    def _detect_csv_fields(self, fields):
        """Fallback: identify fields by their values when positional mapping fails."""
        raw = {}
        used = set()
        ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        ua_hints = ("mozilla", "curl", "chrome", "safari", "firefox", "edge", "bot", "python", "wget")

        for i, value in enumerate(fields):
            v = value.strip()
            if not v or v in ("None", "N/A", "-", "NA"):
                continue

            # Action
            if "action" not in raw and v.upper() in ("ALLOWED", "BLOCKED", "ISOLATED", "ICAP_RESPONSE"):
                raw["action"] = v; used.add(i); continue
            # HTTP method
            if "requestmethod" not in raw and v.upper() in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "CONNECT"):
                raw["requestmethod"] = v; used.add(i); continue
            # Protocol
            if "protocol" not in raw and v.upper() in ("HTTP", "HTTPS", "HTTP_PROXY", "FTP", "TUNNEL", "SSL"):
                raw["protocol"] = v; used.add(i); continue
            # Status code (3-digit, 100-599)
            if "statuscode" not in raw and v.isdigit() and len(v) == 3 and 100 <= int(v) <= 599:
                raw["statuscode"] = v; used.add(i); continue
            # Email → login/user
            if "login" not in raw and "@" in v and "." in v.split("@")[-1]:
                raw["login"] = v; used.add(i); continue
            # IP addresses (first = client, second = server)
            if ip_re.match(v):
                if "clientip" not in raw:
                    raw["clientip"] = v; used.add(i); continue
                elif "serverip" not in raw:
                    raw["serverip"] = v; used.add(i); continue
            # User agent
            if "useragent" not in raw and any(h in v.lower() for h in ua_hints):
                raw["useragent"] = v; used.add(i); continue

        # Detect timestamp (try parsing each unused field)
        for i, value in enumerate(fields):
            if i in used:
                continue
            v = value.strip()
            if v and self._parse_timestamp(v) is not None:
                raw["datetime"] = v; used.add(i); break

        # Detect URL (domain-like pattern with dots)
        url_re = re.compile(r"^https?://|^[\w.-]+\.\w{2,}")
        for i, value in enumerate(fields):
            if i in used:
                continue
            v = value.strip()
            if v and v not in ("None", "N/A", "-") and url_re.match(v):
                raw["url"] = v; used.add(i); break

        return raw

    # ─── CSV line parser with validation ──────────────────────
    def _parse_csv_line(self, line):
        reader = csv.reader(io.StringIO(line))
        fields = next(reader)

        # Pick field list based on column count
        field_list = self.LOG_FIELDS if len(fields) > len(self.LOG_FIELDS_COMPACT) else self.LOG_FIELDS_COMPACT

        raw = {}
        for i, value in enumerate(fields):
            if i < len(field_list):
                raw[field_list[i]] = value.strip()
            else:
                raw[f"field_{i}"] = value.strip()

        # ── Validate before any further processing ────────────
        is_valid, issues = self._validate_csv_row(raw)
        if not is_valid:
            # Positional mapping failed — try auto-detection by value
            auto_raw = self._detect_csv_fields(fields)
            if auto_raw:
                return self._map_fields(auto_raw)

        # Combine separate date and time fields into timestamp
        if "date" in raw and "time" in raw:
            raw["datetime"] = f"{raw['date']} {raw['time']}"
            del raw["date"]
            del raw["time"]

        return self._map_fields(raw)

    def _map_fields(self, raw):
        result = {}
        for raw_key, value in raw.items():
            mapped_key = self.FIELD_MAP.get(raw_key)
            if mapped_key:
                result[mapped_key] = self._convert_value(mapped_key, value)
        return result

    def _convert_value(self, field, value):
        if(value is None or value == "" or value == "None"):
            return None

        if field == "timestamp":
            return self._parse_timestamp(value)
        elif field in ("risk_score", "bytes_transferred", "response_time_ms", "response_size", "request_size", "status_code"):
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
            "%m/%d/%Y %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %Y %H:%M:%S",
            "%a %b %d %H:%M:%S %Y",
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
