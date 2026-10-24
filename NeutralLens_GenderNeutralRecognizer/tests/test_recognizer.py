"""Run from the project root: python -m unittest discover -s tests -v"""
import unittest

from dfa_engine import TermDFA
from document_reader import extract_text
from reporting import csv_report, plain_report, summarize
from terms import GENDER_TERMS


class DFATests(unittest.TestCase):
    def setUp(self):
        self.dfa = TermDFA(GENDER_TERMS)

    def test_transitions_accept_only_complete_term(self):
        self.assertIsNotNone(self.dfa.recognize("chairman"))
        self.assertIsNotNone(self.dfa.recognize("CHAIRMAN"))
        self.assertIsNone(self.dfa.recognize("chair"))
        self.assertIsNone(self.dfa.recognize("chairxyz"))

    def test_word_boundaries_and_positions(self):
        text = "He spoke. thechairman remained. Chairman, chairman!"
        matches = self.dfa.scan(text)
        self.assertEqual([m.term for m in matches], ["he", "chairman", "chairman"])
        self.assertEqual([m.original for m in matches], ["He", "Chairman", "chairman"])

    def test_multiword_phrases_and_punctuation(self):
        text = "A working mother spoke. Working, mother does not match. Ladies and gentlemen!"
        matches = self.dfa.scan(text)
        self.assertEqual([m.term for m in matches], ["working mother", "ladies and gentlemen"])

    def test_clear_message_and_csv(self):
        text = "The team met today."
        findings = self.dfa.scan(text)
        self.assertEqual(findings, [])
        report = plain_report("test.txt", findings, self.dfa.state_count, text)
        self.assertIn("No predefined gender-specific terms were detected.", report)
        self.assertIn("Term,Original,Suggested replacement", csv_report(findings))

    def test_report_counts(self):
        findings = self.dfa.scan("He spoke to the chairman. He spoke again.")
        data = summarize(findings)
        self.assertEqual(data[0]["term"], "he")
        self.assertEqual(data[0]["count"], 2)

    def test_txt_reader(self):
        text = extract_text("samples/sample_with_gender_terms.txt")
        self.assertIn("chairman", text)


if __name__ == "__main__":
    unittest.main()
