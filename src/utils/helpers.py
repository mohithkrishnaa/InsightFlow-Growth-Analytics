"""
Helper Utilities and Formatting Services.
Provides stubs for string formats, datetime parses, and basic arithmetic.
"""

from typing import Union

def format_currency(amount: Union[int, float, None]) -> str:
    """
    Formats a numeric value as a currency string (e.g. INR 1,250.00).
    
    Args:
        amount (Union[int, float, None]): Value to format.
        
    Returns:
        str: Styled currency string.
    """
    if amount is None:
        return "INR 0.00"
    return f"INR {amount:,.2f}"

def format_percentage(val: Union[int, float, None]) -> str:
    """
    Formats a fraction or decimal as a percentage (e.g. +5.20%).
    
    Args:
        val (Union[int, float, None]): Value to format.
        
    Returns:
        str: Styled percentage string.
    """
    if val is None:
        return "0.00%"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:,.2f}%"
