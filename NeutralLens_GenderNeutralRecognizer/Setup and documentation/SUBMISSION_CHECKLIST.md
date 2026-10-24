# Submission checklist — BISU Automata & Language Theory

The code, sample files, test results, screenshots, and draft documentation are included.

## Before submitting

- [ ] Run the app on your own Windows computer (`RUN_ME.bat` or `python main.py`).
- [ ] Review `PROJECT_DOCUMENTATION.docx` for names and spelling.
- [ ] Fill in the **individual contributions** of each group member in section 6 (not supplied in the instructor template).
- [ ] Upload the project source to a **public GitHub repository** and replace the placeholder public URL in section 3 of the Word document.
- [ ] Review references and AI-assistance acknowledgment with your instructor's submission rules.
- [ ] Include or demonstrate the screenshots from the updated application.

## Test commands

```bat
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py
```

## Required five tests

1. `samples/test_01_known_terms.txt` — 4 detected terms.
2. `samples/test_02_case_repeated.txt` — four case-insensitive matches for chairman.
3. `samples/test_03_no_match.txt` — zero matches, no false detection of `he` within `the`.
4. `samples/test_04_empty.txt` — warning about missing readable text.
5. `samples/test_05_unsupported.dat` — clear unsupported-format error.

The recognizer is offline and vocabulary-based. Its output is suggestions for review, not automatic rewriting.
