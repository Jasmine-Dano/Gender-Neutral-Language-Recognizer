"""Finite-state recognition engine.

A deterministic character-transition automaton is constructed from the
predefined vocabulary. It is a trie-shaped DFA. Every transition consumes one
character; accepting states represent complete terms. Missing transitions
lead to an implicit dead/rejecting state.

Tokenization is used only to determine whole-word / phrase boundaries. The
actual classification of a candidate happens via the DFA, not direct string
membership in the source vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Optional


# Letter sequences with optional internal apostrophe or hyphen.
TOKEN_PATTERN = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.UNICODE)


@dataclass(frozen=True)
class Detection:
    term: str
    original: str
    suggestion: str
    start: int  # 0-based character offset in the extracted text
    end: int    # exclusive character offset
    line: int   # 1-based line number


class TermDFA:
    """Deterministic finite-state recognizer backed by a character trie."""

    DEAD_STATE = -1

    def __init__(self, vocabulary: Dict[str, str]):
        # State 0 = initial state. Each state has at most one outgoing edge
        # per input character, which establishes determinism.
        self.transitions: List[Dict[str, int]] = [{}]
        self.accepting: Dict[int, tuple[str, str]] = {}
        self.max_tokens = 1
        self.term_count = len(vocabulary)

        for term, suggestion in vocabulary.items():
            canonical = self.normalize(term)
            self.max_tokens = max(self.max_tokens, len(canonical.split()))
            self.add(canonical, suggestion)

    @staticmethod
    def normalize(text: str) -> str:
        return " ".join(text.casefold().split())

    def add(self, term: str, suggestion: str) -> None:
        state = 0
        for symbol in term:
            if symbol not in self.transitions[state]:
                self.transitions[state][symbol] = len(self.transitions)
                self.transitions.append({})
            state = self.transitions[state][symbol]
        self.accepting[state] = (term, suggestion)

    def transition(self, state: int, symbol: str) -> int:
        if state == self.DEAD_STATE:
            return self.DEAD_STATE
        return self.transitions[state].get(symbol, self.DEAD_STATE)

    def recognize(self, candidate: str) -> Optional[tuple[str, str]]:
        """Run the candidate, character by character, through DFA states."""
        state = 0
        for symbol in self.normalize(candidate):
            state = self.transition(state, symbol)
            if state == self.DEAD_STATE:
                return None
        return self.accepting.get(state)

    @property
    def state_count(self) -> int:
        # Includes the implicit rejecting sink state.
        return len(self.transitions) + 1

    def scan(self, text: str) -> list[Detection]:
        tokens = list(TOKEN_PATTERN.finditer(text))
        findings: list[Detection] = []
        i = 0

        while i < len(tokens):
            accepted = None
            consumed = 0

            # Prefer the longest known phrase ("working mother" before
            # the single word "mother", for instance).
            for width in range(min(self.max_tokens, len(tokens) - i), 0, -1):
                window = tokens[i:i + width]
                # Multi-word phrases must be separated by whitespace, not
                # punctuation such as commas or sentence boundaries.
                if width > 1 and any(
                    not text[prev.end():nxt.start()].isspace()
                    for prev, nxt in zip(window, window[1:])
                ):
                    continue

                candidate = " ".join(token.group() for token in window)
                accepted = self.recognize(candidate)
                if accepted:
                    consumed = width
                    term, suggestion = accepted
                    start = window[0].start()
                    end = window[-1].end()
                    findings.append(
                        Detection(
                            term=term,
                            original=text[start:end],
                            suggestion=suggestion,
                            start=start,
                            end=end,
                            line=text.count("\n", 0, start) + 1,
                        )
                    )
                    break

            i += consumed or 1
        return findings
