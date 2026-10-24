"""Tests aligned with the five mandatory situations in the project guide."""
from pathlib import Path
import unittest
from dfa_engine import TermDFA
from document_reader import extract_text
from reporting import plain_report, summarize
from terms import GENDER_TERMS

BASE = Path(__file__).resolve().parent.parent
SAMPLES = BASE / "samples"


class AssignmentRequirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dfa = TermDFA(GENDER_TERMS)

    def test_01_known_terms(self):
        data = extract_text(SAMPLES / "test_01_known_terms.txt")
        found = self.dfa.scan(data)
        self.assertEqual([x.term for x in found],
                         ["chairman", "stewardess", "policeman", "fireman"])
        self.assertEqual(len(found), 4)

    def test_02_repeated_case_insensitive(self):
        data = extract_text(SAMPLES / "test_02_case_repeated.txt")
        found = self.dfa.scan(data)
        self.assertEqual([x.original for x in found],
                         ["Chairman", "CHAIRMAN", "chairman", "chairman"])
        self.assertEqual(summarize(found)[0]["count"], 4)

    def test_03_no_match_and_whole_word(self):
        data = extract_text(SAMPLES / "test_03_no_match.txt")
        found = self.dfa.scan(data)
        self.assertEqual(found, [])
        message = plain_report(str(SAMPLES / "test_03_no_match.txt"), found,
                               self.dfa.state_count, data)
        self.assertIn("No predefined gender-specific terms were detected.", message)
        self.assertIsNone(self.dfa.recognize("the"))

    def test_04_empty_txt_file(self):
        data = extract_text(SAMPLES / "test_04_empty.txt")
        self.assertEqual(data, "")
        # The GUI's analyze action warns and stops on this condition.
        self.assertFalse(bool(data.strip()))

    def test_05_unsupported_file(self):
        with self.assertRaisesRegex(ValueError, r"Please choose a \.txt, \.docx or \.pdf document"):
            extract_text(SAMPLES / "test_05_unsupported.dat")


if __name__ == "__main__":
    unittest.main()
