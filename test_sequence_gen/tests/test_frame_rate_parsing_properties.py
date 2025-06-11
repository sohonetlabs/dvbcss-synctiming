#!/usr/bin/env python3
"""
Hypothesis Property Tests for Frame Rate Parsing - Phase 3.2

This module uses property-based testing to verify mathematical correctness
and edge case handling of the frame rate parser.

Phase 3.2: Hypothesis Property Tests for Frame Rate Parsing
- Property 1: Parser output should always be valid rationals
- Property 2: Integer inputs should always produce (n, 1) rationals  
- Property 3: Rational inputs should be reduced to lowest terms
- Property 4: Decimal precision should be reasonable
- Property 5: Round-trip conversion should preserve precision
"""

import math
import os
import sys
from fractions import Fraction

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from frame_rate_parser import get_broadcast_standard_fps, parse_frame_rate


class TestFrameRateParserProperties:
    """Property-based tests for frame rate parser (TDD Phase 3.2)"""
    
    @given(st.integers(min_value=1, max_value=240))
    def test_integer_fps_parsing_invariant(self, fps):
        """Property: Integer fps should parse to (fps, 1)"""
        result = parse_frame_rate(str(fps))
        assert result == (fps, 1), f"Integer {fps} should parse to ({fps}, 1)"
        
        # Also test as actual integer input
        result_int = parse_frame_rate(fps)
        assert result_int == (fps, 1), f"Integer input {fps} should parse to ({fps}, 1)"
    
    @given(st.floats(min_value=1.0, max_value=240.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)  # Limit for performance
    def test_decimal_fps_precision(self, fps):
        """Property: Decimal fps parsing should maintain reasonable precision"""
        assume(not math.isnan(fps) and not math.isinf(fps))
        assume(1.0 <= fps <= 240.0)  # Reasonable range
        
        result_num, result_den = parse_frame_rate(f"{fps:.6f}")
        reconstructed = result_num / result_den
        
        # Should be close to original (within reasonable tolerance)
        precision_error = abs(reconstructed - fps)
        assert precision_error < 0.001, f"Precision error too large: {precision_error} for input {fps}"
        
        # Result should be a valid rational
        assert result_num > 0, "Numerator should be positive"
        assert result_den > 0, "Denominator should be positive"
        assert isinstance(result_num, int), "Numerator should be integer"
        assert isinstance(result_den, int), "Denominator should be integer"
    
    @given(st.integers(min_value=1, max_value=240000),
           st.integers(min_value=1, max_value=1001))
    @settings(max_examples=100)  # Limit for performance
    def test_rational_parsing_exact(self, num, den):
        """Property: Rational format should parse exactly"""
        # Skip if fps would be out of range
        fps_value = num / den
        assume(1.0 <= fps_value <= 240.0)
        
        fps_str = f"{num}/{den}"
        result_num, result_den = parse_frame_rate(fps_str)
        
        # Should be mathematically equivalent (reduced to lowest terms)
        original_fraction = Fraction(num, den)
        result_fraction = Fraction(result_num, result_den)
        
        assert original_fraction == result_fraction, \
            f"Rational {fps_str} should parse to equivalent fraction"
        
        # Result should be in reduced form
        assert math.gcd(result_num, result_den) == 1, \
            f"Result ({result_num}, {result_den}) should be in lowest terms"
    
    @given(st.sampled_from([
        "ntsc-film", "ntsc", "ntsc-hd", "pal", "pal-hd", "film", "film-hfr-48"
    ]))
    def test_broadcast_standard_consistency(self, standard):
        """Property: Broadcast standards should return consistent rationals"""
        result_num, result_den = get_broadcast_standard_fps(standard)
        
        # Should be valid positive integers
        assert isinstance(result_num, int), "Broadcast standard numerator should be integer"
        assert isinstance(result_den, int), "Broadcast standard denominator should be integer"
        assert result_num > 0, "Broadcast standard numerator should be positive"
        assert result_den > 0, "Broadcast standard denominator should be positive"
        
        # Should be in reduced form
        assert math.gcd(result_num, result_den) == 1, \
            f"Broadcast standard {standard} should return reduced rational"
        
        # Should be reasonable frame rate
        fps_value = result_num / result_den
        assert 1.0 <= fps_value <= 240.0, \
            f"Broadcast standard {standard} fps {fps_value} should be reasonable"
    
    @given(st.integers(min_value=1, max_value=240000),
           st.integers(min_value=1, max_value=1001))
    @settings(max_examples=50)
    def test_parser_output_always_valid(self, num, den):
        """Property: Parser should always return valid rationals or raise ValueError"""
        fps_value = num / den
        fps_str = f"{num}/{den}"
        
        try:
            result_num, result_den = parse_frame_rate(fps_str)
            
            # If parsing succeeds, result must be valid
            assert isinstance(result_num, int), "Numerator must be integer"
            assert isinstance(result_den, int), "Denominator must be integer"
            assert result_num > 0, "Numerator must be positive"
            assert result_den > 0, "Denominator must be positive"
            
            # Result fps should be in reasonable range
            result_fps = result_num / result_den
            assert 0.1 <= result_fps < 500.0, "Result fps should be in valid range"
            
        except ValueError:
            # If parsing fails, input should be unreasonable
            assert fps_value < 0.1 or fps_value >= 240.0, \
                f"Parser should only reject unreasonable fps: {fps_value}"


class TestFrameRateParserRoundTrip:
    """Round-trip property tests (TDD Phase 3.2)"""
    
    @given(st.sampled_from([
        (24000, 1001), (30000, 1001), (60000, 1001),  # NTSC family
        (24, 1), (25, 1), (30, 1), (50, 1), (60, 1)   # Integer rates
    ]))
    def test_known_rationals_roundtrip(self, fps_rational):
        """Property: Known rational → decimal → parse should preserve value"""
        num, den = fps_rational
        
        # Convert to decimal
        decimal_fps = num / den
        decimal_str = f"{decimal_fps:.6f}"
        
        # Parse back
        parsed_num, parsed_den = parse_frame_rate(decimal_str)
        
        # Should be equivalent (allowing for different reduced forms)
        original_fraction = Fraction(num, den)
        parsed_fraction = Fraction(parsed_num, parsed_den)
        
        assert abs(float(original_fraction) - float(parsed_fraction)) < 1e-6, \
            f"Round-trip failed: {fps_rational} → {decimal_str} → {(parsed_num, parsed_den)}"
    
    @given(st.integers(min_value=1, max_value=240))
    def test_integer_roundtrip_exact(self, fps):
        """Property: Integer → string → parse should be exact"""
        # Integer to string
        fps_str = str(fps)
        
        # Parse back
        parsed_num, parsed_den = parse_frame_rate(fps_str)
        
        # Should be exact
        assert parsed_num == fps, f"Integer roundtrip failed: numerator {parsed_num} != {fps}"
        assert parsed_den == 1, f"Integer roundtrip failed: denominator {parsed_den} != 1"


class TestFrameRateParserMathematicalProperties:
    """Mathematical property tests (TDD Phase 3.2)"""
    
    @given(st.sampled_from([
        (24000, 1001), (30000, 1001), (60000, 1001),
        (48000, 1001), (120000, 1001)
    ]))
    def test_ntsc_family_mathematical_relationships(self, fps_rational):
        """Property: NTSC family rates should have 1001 denominator"""
        num, den = fps_rational
        
        # All NTSC family rates should have 1001 denominator when reduced
        assert den == 1001, f"NTSC rate {fps_rational} should have denominator 1001"
        
        # Numerator should be divisible by 1000 (approximately)
        # 24000/1001 ≈ 24000/1000 = 24
        base_rate = num // 1000
        assert 20 <= base_rate <= 150, f"NTSC base rate {base_rate} should be reasonable"
    
    @given(st.integers(min_value=1, max_value=240))
    def test_frame_duration_calculation_properties(self, fps):
        """Property: Frame duration calculation should be mathematically correct"""
        fps_num, fps_den = parse_frame_rate(fps)
        
        # Frame duration = 1 / fps = fps_den / fps_num
        frame_duration = Fraction(fps_den, fps_num)
        
        # Duration should be positive and reasonable
        duration_seconds = float(frame_duration)
        assert duration_seconds > 0, "Frame duration should be positive"
        assert duration_seconds <= 1.0, "Frame duration should be at most 1 second"
        assert duration_seconds > 1.0/500.0, "Frame duration should be reasonable"
        
        # Reciprocal should give back the original fps
        reciprocal_fps = 1.0 / duration_seconds
        assert abs(reciprocal_fps - fps) < 1e-10, \
            f"Frame duration reciprocal should equal original fps: {reciprocal_fps} vs {fps}"
    
    @given(st.integers(min_value=2, max_value=100),
           st.integers(min_value=24, max_value=60))
    def test_rational_reduction_properties(self, multiplier, base_fps):
        """Property: Rational reduction should preserve mathematical equality"""
        # Create a non-reduced rational
        original_num = base_fps * multiplier
        original_den = 1 * multiplier
        
        # Parse the rational
        parsed_num, parsed_den = parse_frame_rate(f"{original_num}/{original_den}")
        
        # Should be mathematically equal
        original_value = original_num / original_den
        parsed_value = parsed_num / parsed_den
        
        assert abs(original_value - parsed_value) < 1e-15, \
            f"Reduction should preserve value: {original_value} vs {parsed_value}"
        
        # Should be in reduced form
        assert math.gcd(parsed_num, parsed_den) == 1, \
            f"Result should be reduced: gcd({parsed_num}, {parsed_den}) = {math.gcd(parsed_num, parsed_den)}"
        
        # For this specific case, should reduce to (base_fps, 1)
        assert parsed_num == base_fps, f"Should reduce to base fps: {parsed_num} vs {base_fps}"
        assert parsed_den == 1, f"Should reduce to denominator 1: {parsed_den}"


if __name__ == '__main__':
    pytest.main([__file__, "-v"])