"""
core/thresholds.py
Central Single Source of Truth for Academic Mastery and Progression Thresholds.

Definitions:
- PREREQ_UNLOCK: Minimum mastery required in a prerequisite topic before dependent topics can be unlocked (60.0%).
- ASSESSMENT_PASS: Passing percentage for quizzes, diagnostics, and practice assessments (60.0%).
- TOPIC_MASTERY: Minimum mastery required for a topic to be classified as MASTERED / COMPLETED (80.0%).
- CO_ACHIEVED_DEFAULT: Default target attainment percentage for Course Outcomes (70.0%).
"""

PREREQ_UNLOCK: float = 60.0
ASSESSMENT_PASS: float = 60.0
TOPIC_MASTERY: float = 80.0
CO_ACHIEVED_DEFAULT: float = 70.0
AT_RISK_MASTERY: float = 50.0
INACTIVE_DAYS: int = 7
COMMON_GAP_PCT: float = 25.0

