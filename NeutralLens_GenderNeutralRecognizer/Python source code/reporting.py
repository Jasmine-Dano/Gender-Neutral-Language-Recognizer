"""Create reports and structured summaries from DFA findings."""

from collections import Counter
from pathlib import Path
import csv
from io import StringIO

from dfa_engine import Detection, TOKEN_PATTERN


def summarize(findings: list[Detection]) -> list[dict]:
    counts = Counter(item.term for item in findings)
    by_term = {}
    for item in findings:
        if item.term not in by_term:
            by_term[item.term] = {
                "term": item.term,
                "suggestion": item.suggestion,
                "lines": set(),
            }
        by_term[item.term]["lines"].add(item.line)

    output = []
    for term, values in by_term.items():
        output.append({
            "term": term,
            "suggestion": values["suggestion"],
            "count": counts[term],
            "lines": sorted(values["lines"]),
        })
    return sorted(output, key=lambda row: (-row["count"], row["term"]))


def word_count(text: str) -> int:
    return sum(1 for _ in TOKEN_PATTERN.finditer(text))


def plain_report(path: str, findings: list[Detection], states: int, text: str) -> str:
    stats = summarize(findings)
    lines = [
        "GENDER-NEUTRAL LANGUAGE RECOGNIZER",
        "Analysis report · Finite State Automaton (DFA)",
        "=" * 60,
        f"Document: {Path(path).name}",
        f"Words scanned: {word_count(text):,}",
        f"DFA states (including rejecting sink): {states}",
        f"Total occurrences: {len(findings)}",
        f"Unique recognized terms: {len(stats)}",
        "",
    ]
    if not findings:
        lines.extend([
            "No predefined gender-specific terms were detected.",
            "",
            "Note: No terms from the predefined vocabulary were detected.",
        ])
        return "\n".join(lines)

    lines.extend(["TERM SUMMARY", "-" * 60])
    for row in stats:
        lines.extend([
            f"Term: {row['term']}",
            f"Occurrences: {row['count']}",
            f"Suggestion: {row['suggestion']}",
            f"Line(s): {', '.join(map(str, row['lines']))}",
            "",
        ])

    lines.extend(["INDIVIDUAL DETECTIONS", "-" * 60])
    for idx, item in enumerate(findings, start=1):
        lines.append(
            f"{idx:>3}. Line {item.line}: {item.original!r} → {item.suggestion}"
        )
    lines.extend([
        "",
        "NOTE",
        "Suggestions are context-dependent and are not automatic edits.",
        "This vocabulary-based scanner cannot determine whether an individual",
        "reference or a grammatical sentence actually needs to be changed.",
    ])
    return "\n".join(lines)


def csv_report(findings: list[Detection]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["Term", "Original", "Suggested replacement", "Line", "Start offset", "End offset"])
    for item in findings:
        writer.writerow([item.term, item.original, item.suggestion, item.line, item.start, item.end])
    return buffer.getvalue()
