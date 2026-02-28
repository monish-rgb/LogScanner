import json
import csv
import io
from datetime import datetime

class ZScalerParser:
    FIELD_MAP = {
        "clientip": "source_ip",
        "url": "destination_url",
        "host": "destination_url",
        "login": "user",
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
        "contenttype": "content_type",
        "useragent": "user_agent",
        "threatname": "threat_name",
        "threatclass": "threat_class",
        "threatcategory": "threat_category",
        "threatseverity": "threat_severity",
        "filetype": "file_type",
        "fileclass": "file_class",
    }

    LOG_FIELDS = [
        "date", "time", "action", "login", "department", "location",
        "clientip", "host", "protocol", "statuscode", "requestmethod",
        "contenttype", "requestsize", "responsesize", "urlcategory",
        "pagerisk", "transactionsize", "clienttranstime", "serverip",
        "threatname", "threatclass", "threatcategory", "threatseverity",
        "filetype", "fileclass", "useragent", "url",
    ]

    #field validators for csv format
    FIELD_VALIDATORS = {
        "date":            lambda v: bool(re.match(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}", v)),
        "time":            lambda v: bool(re.match(r"\d{2}:\d{2}:\d{2}", v)),
        "action":          lambda v: v.upper() in ("ALLOWED", "BLOCKED", "ISOLATED", "ICAP_RESPONSE"),
        "login":           lambda v: "@" in v or v == "-",
        "clientip":        lambda v: bool(re.match(r"\d{1,3}(\.\d{1,3}){3}", v)),
        "statuscode":      lambda v: v.isdigit() and 100 <= int(v) <= 599,
        "requestmethod":   lambda v: v.upper() in ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"),
        "requestsize":     lambda v: v.isdigit(),
        "responsesize":    lambda v: v.isdigit(),
        "pagerisk":        lambda v: v.isdigit() and 0 <= int(v) <= 100,
        "serverip":        lambda v: bool(re.match(r"\d{1,3}(\.\d{1,3}){3}", v)) or v == "-",
        "url":             lambda v: v.startswith("http://") or v.startswith("https://") or v == "-",
        "protocol":        lambda v: v.upper() in ("HTTP", "HTTPS", "FTP", "TUNNEL"),
    }

    def parse_file(self, filepath, log_file_id):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = self.parse_line(line, line_number)
                    parsed["log_file_id"] = log_file_id
                    parsed["raw_line"] = line
                    yield parsed
                except Exception:
                    yield {
                        "log_file_id": log_file_id,
                        "line_number": line_number,
                        "raw_line": line,
                    }

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
               return "json"
            except json.JSONDecodeError:
                pass

        # CSV format
        if "," in line:
            try:
                return "csv"
            except csv.Error:
                pass

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

    # def _parse_csv_line(self, line):
    #     reader = csv.reader(io.StringIO(line))
    #     fields = next(reader)
    #     raw = {}
    #     for i, value in enumerate(fields):
    #         if i < len(self.LOG_FIELDS):
    #             raw[self.LOG_FIELDS[i]] = value.strip()
    #         else:
    #             raw[f"field_{i}"] = value.strip()

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

    # ─── CSV line parser with validation ──────────────────────
    def _parse_csv_line(self, line):
        reader = csv.reader(io.StringIO(line))
        fields = next(reader)

        raw = {}
        for i, value in enumerate(fields):
            if i < len(self.LOG_FIELDS):
                raw[self.LOG_FIELDS[i]] = value.strip()
            else:
                raw[f"field_{i}"] = value.strip()

        # ── Validate before any further processing ────────────
        is_valid, issues = self._validate_csv_row(raw)
        if not is_valid:
            # Attach validation issues to result so caller can log/store them
            result = self._map_fields(raw)
            result["_validation_errors"] = issues
            result["_is_valid"] = False
            return result

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
