"""
Class Code Generation & Validation Module
Handles cryptographically secure code generation and anti-guessability validation.
"""

import re
import secrets
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from models import ClassModel

# Characters excluding visually ambiguous glyphs: 0, O, 1, I
SAFE_ALPHANUM = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

# Disallowed obvious patterns and common prefixes
COMMON_WEAK_PATTERNS = {
    "CLASS", "CLASS1", "CLASS123", "DSA123", "DSA101", "DSA201",
    "TEST", "TEST1", "TEST123", "DEMO", "DEMO123", "ADMIN",
    "COURSE", "COURSE1", "STUDENT", "FACULTY", "SECRET", "PASSWORD",
    "WELCOME", "CS101", "CS201", "AI101", "AI201", "SAMPLE", "TEMP123",
    "1234", "12345", "123456", "12345678", "654321", "0000", "1111", "9999",
    "ABCD", "ABCDE", "ABCDEF", "QWERTY", "ASDFGH", "ZXCVBN"
}

def generate_random_class_code(length: int = 6) -> str:
    """Generates a random code using uppercase letters and digits without 0/O/1/I."""
    return "".join(secrets.choice(SAFE_ALPHANUM) for _ in range(length))

def generate_unique_class_code(db: Session, length: int = 6, max_attempts: int = 100) -> str:
    """Generates a random class code guaranteed to be unique in the database."""
    for _ in range(max_attempts):
        code = generate_random_class_code(length)
        exists = db.query(ClassModel).filter(ClassModel.class_code == code).first()
        if not exists:
            return code
    raise RuntimeError("Failed to generate a unique class code after multiple attempts.")

def validate_custom_code(custom_code: str, suggested_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a teacher-provided custom code.
    Rules:
    - 6 to 12 alphanumeric characters
    - Must contain both letters and digits (rejects short/guessable codes like 'PON12')
    - Not all-same characters
    - Not a known weak/guessable pattern (e.g. 'DSA123', 'CLASS1')
    - Returns (is_valid, error_message_if_invalid)
    """
    code = custom_code.strip().upper()

    if len(code) < 6 or len(code) > 12:
        return False, (
            f"Class code must be between 6 and 12 characters in length. "
            f"Suggested code: '{suggested_code}'."
        )

    if not re.match(r"^[A-Z0-9]+$", code):
        return False, (
            f"Class code must only contain letters and numbers (no special characters). "
            f"Suggested code: '{suggested_code}'."
        )

    has_letter = bool(re.search(r"[A-Z]", code))
    has_digit = bool(re.search(r"[0-9]", code))
    if not (has_letter and has_digit):
        return False, (
            f"Class code must contain both letters and digits (at least 6 characters). "
            f"Suggested code: '{suggested_code}'."
        )

    # Check for all same characters (e.g., 'AAAAAA', '888888')
    if len(set(code)) == 1:
        return False, (
            f"Class code '{custom_code}' is too simple (all identical characters). "
            f"Please choose a stronger code or use the suggested code: '{suggested_code}'."
        )

    # Check against known weak patterns
    if code in COMMON_WEAK_PATTERNS:
        return False, (
            f"Class code '{custom_code}' is trivially guessable and not allowed. "
            f"Please choose a more secure code or use the suggested code: '{suggested_code}'."
        )

    # Check if starts with common prefix like CLASS1, TEST1, DSA123
    for weak in ["CLASS", "TEST", "DEMO", "SAMPLE", "DSA1"]:
        if code.startswith(weak) and len(code) <= len(weak) + 3:
            return False, (
                f"Class code '{custom_code}' is trivially guessable. "
                f"Please choose a more secure code or use the suggested code: '{suggested_code}'."
            )

    return True, None
