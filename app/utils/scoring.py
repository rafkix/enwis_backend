# app/utils/scoring.py
from typing import List, Any
import difflib

def normalize(s: str) -> str:
    return " ".join(s.lower().strip().split())

def score_question(question: Any, submitted: List[str]) -> int:
    """
    question.expected is a list of correct answers (lowercased normalized).
    submitted is list of answers strings or option labels.
    Returns points awarded (question.points maximum).
    """
    max_points = getattr(question, "points", 1) or 1
    expected = question.expected or []
    if expected and isinstance(expected, list):
        # normalize both sides
        expected_norm = [normalize(x) for x in expected]
        submitted_norm = [normalize(x) for x in (submitted or [])]
        # exact match
        for s in submitted_norm:
            if s in expected_norm:
                return max_points
        # fuzzy match: allow close matches (useful for sentence completion)
        for s in submitted_norm:
            for e in expected_norm:
                ratio = difflib.SequenceMatcher(None, s, e).ratio()
                if ratio > 0.85:
                    return max_points
        return 0
    else:
        # If no expected answers (MCQ stored via options.is_correct flag), handle externally
        return 0

def score_mcq(question: Any, submitted_labels: List[str]) -> int:
    # question.options available
    correct = [opt.label for opt in question.options if opt.is_correct]
    if not correct:
        return 0
    # If single-correct
    if len(correct) == 1:
        return question.points if submitted_labels and submitted_labels[0] == correct[0] else 0
    # if multiple correct - compare sets
    if set(correct) == set(submitted_labels or []):
        return question.points
    # partial credit could be implemented
    return 0
