#!/usr/bin/env python3
"""
Validation functions for the invoicer application.

This module provides validation functions for various configuration settings
and user inputs with comprehensive error handling and clear feedback.
"""

import re
from pathlib import Path
from typing import Any, Callable, Dict

import typer


def validate_email(email: str) -> bool:
    """
    Validate email address format using a comprehensive regex pattern.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
        
    Examples:
        >>> validate_email("test@example.com")
        True
        >>> validate_email("user.name@domain.co.uk")
        True
        >>> validate_email("invalid-email")
        False
    """
    try:
        # Use pydantic's email validation for robustness
        from pydantic import BaseModel, EmailStr
        
        class EmailModel(BaseModel):
            email: EmailStr
        
        EmailModel(email=email)
        return True
    except Exception:
        return False


def validate_positive_float(value: str, field_name: str) -> float:
    """
    Validate that a string represents a positive float value.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        
    Returns:
        float: The validated float value
        
    Raises:
        typer.BadParameter: If value is not a positive float
        
    Examples:
        >>> validate_positive_float("10.5", "hourly_rate")
        10.5
        >>> validate_positive_float("0", "hourly_rate")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        typer.BadParameter: hourly_rate must be greater than 0
    """
    try:
        float_val = float(value)
        if float_val <= 0:
            raise typer.BadParameter(f"{field_name} must be greater than 0")
        return float_val
    except ValueError:
        raise typer.BadParameter(f"{field_name} must be a valid number")


def validate_vat_rate(value: str) -> float:
    """
    Validate VAT rate accepting both percentage (0-100) and decimal (0.0-1.0) formats.
    
    Args:
        value: VAT rate as string
        
    Returns:
        float: VAT rate as decimal (0.0-1.0)
        
    Raises:
        typer.BadParameter: If VAT rate is invalid
        
    Examples:
        >>> validate_vat_rate("21")
        0.21
        >>> validate_vat_rate("0.21")
        0.21
        >>> validate_vat_rate("150")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        typer.BadParameter: VAT rate must be between 0-100% or 0.0-1.0
    """
    try:
        float_val = float(value)
        # Accept both percentage (0-100) and decimal (0.0-1.0) formats
        if 1 < float_val <= 100:
            float_val = float_val / 100  # Convert percentage to decimal
        elif not (0 <= float_val <= 1):
            raise typer.BadParameter("VAT rate must be between 0-100% or 0.0-1.0")
        return float_val
    except ValueError:
        raise typer.BadParameter("VAT rate must be a valid number")


def validate_phone(value: str) -> bool:
    """
    Validate phone number format with support for international formats.
    
    Args:
        value: Phone number to validate
        
    Returns:
        bool: True if phone number format is valid
        
    Examples:
        >>> validate_phone("+1 (555) 123-4567")
        True
        >>> validate_phone("+32 472 904 555")
        True
        >>> validate_phone("invalid")
        False
    """
    # Allow common phone formats: +1 (555) 123-4567, +1-555-123-4567, etc.
    phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
    return bool(re.match(phone_pattern, value.strip()))


def validate_currency_code(value: str) -> str:
    """
    Validate currency code format (3 uppercase letters).
    
    Args:
        value: Currency code to validate
        
    Returns:
        str: Uppercase currency code
        
    Raises:
        typer.BadParameter: If currency code format is invalid
        
    Examples:
        >>> validate_currency_code("USD")
        'USD'
        >>> validate_currency_code("eur")
        'EUR'
        >>> validate_currency_code("INVALID")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        typer.BadParameter: Currency code must be 3 uppercase letters (e.g., USD, EUR, GBP)
    """
    if not re.match(r'^[A-Z]{3}$', value.upper()):
        raise typer.BadParameter("Currency code must be 3 uppercase letters (e.g., USD, EUR, GBP)")
    return value.upper()


def validate_template(template: str) -> bool:
    """
    Validate invoice number template format with supported variables.
    
    Args:
        template: Template string to validate
        
    Returns:
        bool: True if template is valid
        
    Examples:
        >>> validate_template("INV-{year}{month:02d}-{client_code}")
        True
        >>> validate_template("INV-{invalid_var}")
        False
    """
    # Check for valid template variables
    valid_vars = {'year', 'month', 'day', 'client_code', 'invoice_number'}
    
    # Find all variables in template
    found_vars = set(re.findall(r'\{(\w+)(?::.*?)?\}', template))
    
    # Check if all variables are valid
    invalid_vars = found_vars - valid_vars
    if invalid_vars:
        return False
    
    # Try to format with sample data
    try:
        template.format(
            year=2024,
            month=12,
            day=31,
            client_code='TST',
            invoice_number='001'
        )
        return True
    except (KeyError, ValueError):
        return False


def validate_directory_path(path: str) -> Path:
    """
    Validate and resolve directory path, creating it if it doesn't exist.
    
    Args:
        path: Directory path to validate
        
    Returns:
        Path: Resolved absolute path
        
    Raises:
        typer.BadParameter: If path is invalid or cannot be created
    """
    try:
        path_obj = Path(path).expanduser().resolve()
        
        # Create directory if it doesn't exist
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
        elif not path_obj.is_dir():
            raise typer.BadParameter(f"Path '{path}' exists but is not a directory")
            
        return path_obj
    except (OSError, PermissionError) as e:
        raise typer.BadParameter(f"Invalid directory path '{path}': {e}")


def validate_non_empty_string(value: str, field_name: str) -> str:
    """
    Validate that a string is not empty or only whitespace.
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        
    Returns:
        str: Stripped string value
        
    Raises:
        typer.BadParameter: If string is empty or only whitespace
        
    Examples:
        >>> validate_non_empty_string("Hello World", "company_name")
        'Hello World'
        >>> validate_non_empty_string("   ", "company_name")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        typer.BadParameter: company_name cannot be empty
    """
    stripped = value.strip()
    if not stripped:
        raise typer.BadParameter(f"{field_name} cannot be empty")
    return stripped


# Validator registry for dynamic lookup
VALIDATORS: Dict[str, Callable] = {
    'email': validate_email,
    'positive_float': validate_positive_float,
    'vat_rate': validate_vat_rate,
    'phone': validate_phone,
    'currency_code': validate_currency_code,
    'template': validate_template,
    'directory_path': validate_directory_path,
    'non_empty_string': validate_non_empty_string,
}


def get_validator(validator_name: str) -> Callable:
    """
    Get a validator function by name.
    
    Args:
        validator_name: Name of the validator
        
    Returns:
        Callable: Validator function
        
    Raises:
        KeyError: If validator name is not found
    """
    if validator_name not in VALIDATORS:
        raise KeyError(f"Unknown validator: {validator_name}")
    return VALIDATORS[validator_name]


if __name__ == "__main__":
    import doctest
    doctest.testmod()