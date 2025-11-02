#!/usr/bin/env python3
"""
Reusable field types for the invoicer application.

This module defines standardized field types with validation, descriptions,
and constraints that can be reused across configuration, client, invoice,
and project data models.

Since field types that are used only once have been moved to their respective
usage locations, this module now contains only truly reusable field types
and helper functions.
"""




# ============================================================================
# Helper Functions
# ============================================================================


def uppercase_transform(value: str) -> str:
    """Transform string to uppercase."""
    return value.upper().strip()


def strip_whitespace(value: str) -> str:
    """Strip leading and trailing whitespace."""
    return value.strip()


def validate_non_empty_after_strip(value: str) -> str:
    """Validate that string is not empty after stripping whitespace."""
    if not value:
        raise ValueError("Field cannot be empty")
    return value


# ============================================================================
# Reusable Field Types
# ============================================================================
