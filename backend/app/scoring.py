"""Score calculation engine. Takes raw value + event definition, returns earned score (1-10)."""

from .models import SportEvent, ScoringStandard, InputFormat

def parse_value(raw: str, input_format: InputFormat) -> float:
    """Convert raw input string to a comparable numeric value."""
    if input_format == InputFormat.time_ms:
        parts = raw.replace('"', '').split("'")
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
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

    return 1
