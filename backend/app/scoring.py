"""Score calculation engine. Takes raw value + event definition, returns earned score (1-10)."""

import re
from .models import SportEvent, ScoringStandard, InputFormat

def normalize_time_ms(raw: str) -> str:
    """Normalize various time formats to standard 3'30 format.
    Accepts: 3分30, 3分30秒, 3'30, 3'30\", 3.30, 330"""
    raw = raw.strip().replace('"', '').replace('\"', '')
    # 3分30秒 or 3分30
    m = re.match(r'^(\d+)\s*分\s*(\d+(?:\.\d+)?)\s*(?:秒)?$', raw)
    if m:
        return f"{m.group(1)}'{int(float(m.group(2)))}"
    # 3'30
    if "'" in raw:
        parts = raw.split("'")
        return f"{parts[0]}'{int(float(parts[1]))}"
    # Plain number like 330 (3分30) or 3.30
    val = float(raw)
    if val >= 100:  # e.g. 330 = 3分30秒
        minutes = int(val // 100)
        seconds = int(val % 100)
        return f"{minutes}'{seconds}"
    elif val >= 1:  # e.g. 3.30 → 3'30
        minutes = int(val)
        seconds = round((val - minutes) * 100)
        return f"{minutes}'{seconds}"
    return raw

def parse_value(raw: str, input_format: InputFormat) -> float:
    """Convert raw input string to a comparable numeric value."""
    if input_format == InputFormat.time_ms:
        raw = normalize_time_ms(raw)
        parts = raw.split("'")
        minutes = int(parts[0])
        seconds = int(float(parts[1])) if len(parts) > 1 else 0
        return minutes * 60 + seconds
    elif input_format == InputFormat.decimal_seconds:
        return float(raw)
    elif input_format == InputFormat.decimal_meters:
        return float(raw)
    elif input_format == InputFormat.integer:
        return int(raw)
    raise ValueError(f"Unknown input_format: {input_format}")

def parse_standard_value(val: str, input_format: InputFormat) -> float:
    """Parse a standard value string the same way as parse_value."""
    return parse_value(val, input_format)

def calculate_score(raw_value: str, event: SportEvent, standards: list[ScoringStandard], student_gender: str = None) -> int:
    """Calculate earned score (1-10) using lower-score-when-between rule. Filters standards by student gender."""
    parsed = parse_value(raw_value, event.input_format)

    # Filter standards by student gender
    if student_gender:
        filtered = [s for s in standards if s.gender.value == student_gender or s.gender.value == "both"]
    else:
        filtered = standards

    std_pairs = []
    for s in filtered:
        std_pairs.append((s.score, parse_standard_value(s.standard_value, event.input_format)))

    std_pairs.sort(key=lambda x: x[0], reverse=True)

    if event.higher_better:
        for score, std_val in std_pairs:
            if parsed >= std_val:
                return score
    else:
        for score, std_val in std_pairs:
            if parsed <= std_val:
                return score

    return 0
