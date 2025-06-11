#!/usr/bin/env python3
"""
Frame Rate Parser for Fractional Frame Rates

This module provides parsing functionality for fractional frame rates using exact
rational arithmetic. Supports decimal, rational, and broadcast standard formats.

Phase 3.1: Frame Rate Parsing Implementation (GREEN phase)
- Parse decimal format: "23.976" → (24000, 1001)
- Parse rational format: "24000/1001" → (24000, 1001)  
- Parse integer format: "25" → (25, 1)
- Parse broadcast shortcuts: "ntsc-film" → (24000, 1001)
"""

import re
from fractions import Fraction
from typing import Tuple, Union

# Mapping of common decimal frame rates to exact rationals
DECIMAL_TO_RATIONAL = {
    # NTSC family (1001 denominator)
    "23.976": (24000, 1001),
    "29.97": (30000, 1001), 
    "59.94": (60000, 1001),
    "47.952": (48000, 1001),
    "119.88": (120000, 1001),
    
    # Common variations with extra precision
    "23.9760": (24000, 1001),
    "23.976023976": (24000, 1001),
    "29.970": (30000, 1001),
    "29.970029970": (30000, 1001),
    "59.940": (60000, 1001),
    "59.940059940": (60000, 1001),
    
    # Integer rates as decimals
    "24.0": (24, 1),
    "25.0": (25, 1),
    "30.0": (30, 1),
    "48.0": (48, 1),
    "50.0": (50, 1),
    "60.0": (60, 1),
    "100.0": (100, 1),
    "120.0": (120, 1),
}

# Broadcast standard frame rate mappings
BROADCAST_STANDARDS = {
    # NTSC Family (1001 denominator)
    "ntsc-film": (24000, 1001),    # 23.976 fps - Film to NTSC
    "ntsc": (30000, 1001),         # 29.97 fps - NTSC video
    "ntsc-hd": (60000, 1001),      # 59.94 fps - NTSC HD
    "ntsc-4k": (120000, 1001),     # 119.88 fps - NTSC 4K/8K
    
    # PAL/SECAM Family
    "pal": (25, 1),                # 25 fps - PAL/SECAM
    "pal-hd": (50, 1),             # 50 fps - PAL HD
    "pal-4k": (100, 1),            # 100 fps - PAL 4K/8K
    
    # Cinema Standards
    "film": (24, 1),               # 24 fps - Standard cinema
    "film-hfr-48": (48, 1),        # 48 fps - HFR cinema (Hobbit)
    "film-hfr-60": (60, 1),        # 60 fps - HFR cinema (Gemini Man)  
    "film-hfr-120": (120, 1),      # 120 fps - Future HFR
}

# Reasonable frame rate bounds (fps)
MIN_FRAME_RATE = 0.1  # Allow very low frame rates for testing
MAX_FRAME_RATE = 500.0


def parse_frame_rate(fps_input: Union[str, int, float]) -> Tuple[int, int]:
    """
    Parse frame rate string/number to (numerator, denominator) tuple.
    
    Supports multiple input formats:
    - Decimal: "23.976" → (24000, 1001)
    - Rational: "24000/1001" → (24000, 1001)
    - Integer: "25" → (25, 1)
    - Float: 29.97 → (30000, 1001)
    
    Args:
        fps_input: Frame rate as string, int, or float
        
    Returns:
        Tuple of (numerator, denominator) representing exact rational frame rate
        
    Raises:
        ValueError: If input format is invalid or frame rate is out of range
    """
    # Convert input to string for consistent processing
    fps_str = str(fps_input).strip()
    
    # Check for exact decimal matches first (for common broadcast rates)
    if fps_str in DECIMAL_TO_RATIONAL:
        return DECIMAL_TO_RATIONAL[fps_str]
    
    # Try rational format: "numerator/denominator"
    rational_match = re.match(r'^(\d+)/(\d+)$', fps_str)
    if rational_match:
        numerator = int(rational_match.group(1))
        denominator = int(rational_match.group(2))
        
        if denominator == 0:
            raise ValueError("Invalid frame rate format: division by zero")
        
        # Reduce to lowest terms
        fraction = Fraction(numerator, denominator)
        reduced_num = fraction.numerator
        reduced_den = fraction.denominator
        
        # Check if result is in reasonable range
        fps_value = reduced_num / reduced_den
        _validate_frame_rate_range(fps_value)
        
        return (reduced_num, reduced_den)
    
    # Try decimal/integer format
    try:
        fps_value = float(fps_str)
    except ValueError:
        raise ValueError(f"Invalid frame rate format: '{fps_input}'")
    
    # Validate range
    _validate_frame_rate_range(fps_value)
    
    # Check if it's effectively an integer
    if abs(fps_value - round(fps_value)) < 1e-6:
        return (int(round(fps_value)), 1)
    
    # For non-integer decimals, try to match known rationals
    # Check if it's close to any known NTSC rate
    tolerance = 1e-3
    
    if abs(fps_value - 24000.0/1001.0) < tolerance:
        return (24000, 1001)
    elif abs(fps_value - 30000.0/1001.0) < tolerance:
        return (30000, 1001)  
    elif abs(fps_value - 60000.0/1001.0) < tolerance:
        return (60000, 1001)
    elif abs(fps_value - 48000.0/1001.0) < tolerance:
        return (48000, 1001)
    elif abs(fps_value - 120000.0/1001.0) < tolerance:
        return (120000, 1001)
    
    # For other decimals, convert using Fraction with reasonable precision
    # Limit denominator to avoid huge rationals for imprecise inputs
    fraction = Fraction(fps_value).limit_denominator(max_denominator=10000)
    
    return (fraction.numerator, fraction.denominator)


def get_broadcast_standard_fps(standard_name: str) -> Tuple[int, int]:
    """
    Get frame rate for broadcast standard shortcut.
    
    Args:
        standard_name: Broadcast standard name (e.g., "ntsc", "pal", "film")
        
    Returns:
        Tuple of (numerator, denominator) for the standard's frame rate
        
    Raises:
        ValueError: If broadcast standard is unknown
    """
    standard_name = standard_name.lower().strip()
    
    if standard_name not in BROADCAST_STANDARDS:
        available = ", ".join(sorted(BROADCAST_STANDARDS.keys()))
        raise ValueError(f"Unknown broadcast standard: '{standard_name}'. "
                        f"Available standards: {available}")
    
    return BROADCAST_STANDARDS[standard_name]


def _validate_frame_rate_range(fps_value: float) -> None:
    """
    Validate that frame rate is within reasonable bounds.
    
    Args:
        fps_value: Frame rate value to validate
        
    Raises:
        ValueError: If frame rate is out of reasonable range
    """
    if fps_value < MIN_FRAME_RATE:
        raise ValueError(f"Frame rate out of reasonable range: {fps_value} fps "
                        f"(minimum: {MIN_FRAME_RATE} fps)")
    
    if fps_value >= MAX_FRAME_RATE:
        raise ValueError(f"Frame rate out of reasonable range: {fps_value} fps "
                        f"(maximum: {MAX_FRAME_RATE} fps)")


def format_frame_rate_rational(numerator: int, denominator: int) -> str:
    """
    Format rational frame rate for display.
    
    Args:
        numerator: Numerator of frame rate rational
        denominator: Denominator of frame rate rational
        
    Returns:
        Human-readable string representation
    """
    if denominator == 1:
        return f"{numerator} fps"
    else:
        decimal = numerator / denominator
        return f"{decimal:.6f} fps ({numerator}/{denominator})"


if __name__ == "__main__":
    # Demo usage
    test_inputs = ["23.976", "29.97", "25", "24000/1001", "50/1", 60.0]
    
    print("Frame Rate Parser Demo:")
    print("=" * 40)
    
    for fps_input in test_inputs:
        try:
            num, den = parse_frame_rate(fps_input)
            formatted = format_frame_rate_rational(num, den)
            print(f"Input: {fps_input:>10} → Output: {formatted}")
        except ValueError as e:
            print(f"Input: {fps_input:>10} → Error: {e}")
    
    print("\nBroadcast Standards:")
    print("=" * 20)
    
    for standard in ["ntsc-film", "ntsc", "pal", "film"]:
        try:
            num, den = get_broadcast_standard_fps(standard)
            formatted = format_frame_rate_rational(num, den)
            print(f"{standard:>10}: {formatted}")
        except ValueError as e:
            print(f"{standard:>10}: Error: {e}")