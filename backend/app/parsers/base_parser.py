from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, sample_lines):
        pass

    @abstractmethod
    def parse_line(self, line, line_number):
        pass

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
