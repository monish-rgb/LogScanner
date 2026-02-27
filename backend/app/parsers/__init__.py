from .zscaler_parser import ZScalerParser


def get_parser(filepath):
    sample_lines = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            sample_lines.append(line.strip())

    parser = ZScalerParser()
    if parser.can_parse(sample_lines):
        return parser

    raise ValueError("Unsupported log format. Please upload ZScaler web proxy logs.")
