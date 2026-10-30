"""
Sanitization and Validation Utilities for Class Communication
Enforces plain text, control character stripping, max lengths, and safe URL schemes.
"""

import re
import urllib.parse
from fastapi import HTTPException, status

ALLOWED_RESOURCE_TYPES = {"video", "article", "notes", "practice", "other"}
ALLOWED_DOUBT_VISIBILITY = {"private", "class"}
ALLOWED_DOUBT_STATUS = {"open", "answered", "closed"}


def strip_control_chars(text: str, allow_newlines: bool = False) -> str:
    """Strips ASCII control characters (0-31, 127). Retains \n, \r, \t if allow_newlines is True."""
    if not text:
        return ""
    if allow_newlines:
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()
    return re.sub(r"[\x00-\x1f\x7f]", "", text).strip()


def validate_plain_text(
    text: str,
    max_length: int,
    field_name: str,
    allow_newlines: bool = False,
    required: bool = True
) -> str:
    """
    Validates and cleans plain text.
    - Strips control characters
    - Validates required constraints and length bounds
    - Stores plain text only
    """
    if text is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required."
            )
        return ""

    cleaned = strip_control_chars(str(text), allow_newlines=allow_newlines)
    if required and not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty."
        )

    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must not exceed {max_length} characters (got {len(cleaned)})."
        )
    return cleaned


def validate_url(url: str, max_length: int = 500) -> str:
    """
    Validates URL scheme and length.
    - Scheme MUST be http or https only.
    - Explicitly rejects javascript:, data:, file:, vbscript:, etc.
    - Max length 500 characters.
    """
    if not url or not str(url).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required."
        )

    clean_url = strip_control_chars(str(url).strip(), allow_newlines=False)
    if len(clean_url) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL must not exceed {max_length} characters."
        )

    parsed = urllib.parse.urlparse(clean_url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must use http or https scheme (e.g. https://example.com)."
        )
    if not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format: missing host."
        )
    return clean_url


def validate_resource_type(rtype: str) -> str:
    """Validates resource_type is one of the allowed categories."""
    if not rtype:
        return "other"
    cleaned = strip_control_chars(str(rtype).strip().lower(), allow_newlines=False)
    if cleaned not in ALLOWED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"resource_type must be one of: {', '.join(sorted(ALLOWED_RESOURCE_TYPES))}."
        )
    return cleaned


def validate_doubt_visibility(vis: str) -> str:
    """Validates doubt visibility is 'private' or 'class'."""
    if not vis:
        return "private"
    cleaned = strip_control_chars(str(vis).strip().lower(), allow_newlines=False)
    if cleaned not in ALLOWED_DOUBT_VISIBILITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="visibility must be 'private' or 'class'."
        )
    return cleaned
