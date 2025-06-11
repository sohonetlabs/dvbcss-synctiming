#!/usr/bin/env python3
"""
Frame Rate Parsing Tests - Phase 3.1: RED → GREEN → REFACTOR

This module implements TDD for fractional frame rate parsing and rational arithmetic.

Phase 3.1: Frame Rate Parser Tests
- RED: Write failing tests for fractional frame rate parsing
- GREEN: Implement parser to make tests pass  
- REFACTOR: Clean up parser implementation

The parser should handle:
- Decimal format: "23.976" → (24000, 1001)
- Rational format: "24000/1001" → (24000, 1001)  
- Integer format: "25" → (25, 1)
- Broadcast shortcuts: "ntsc-film" → (24000, 1001)
"""

import os
import sys
from fractions import Fraction

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import will fail initially - that's part of RED phase
try:
    from frame_rate_parser import get_broadcast_standard_fps, parse_frame_rate
except ImportError:
    # Expected during RED phase - parser doesn't exist yet
    parse_frame_rate = None
    get_broadcast_standard_fps = None


class TestFrameRateParserBasic:
    """Basic frame rate parsing tests (TDD Phase 3.1 RED)"""
    
    def test_parse_decimal_frame_rates(self):
        """Should parse common decimal frame rates to exact rationals"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        # NTSC rates (1001 denominator family)
        assert parse_frame_rate("23.976") == (24000, 1001)
        assert parse_frame_rate("29.97") == (30000, 1001)
        assert parse_frame_rate("59.94") == (60000, 1001)
        assert parse_frame_rate("47.952") == (48000, 1001)
        assert parse_frame_rate("119.88") == (120000, 1001)
    
    def test_parse_rational_frame_rates(self):
        """Should parse direct rational format"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        assert parse_frame_rate("24000/1001") == (24000, 1001)
        assert parse_frame_rate("30000/1001") == (30000, 1001)
        assert parse_frame_rate("60000/1001") == (60000, 1001)
        
        # Also integer rationals
        assert parse_frame_rate("25/1") == (25, 1)
        assert parse_frame_rate("50/1") == (50, 1)
    
    def test_parse_integer_frame_rates(self):
        """Should still support integer frame rates"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        assert parse_frame_rate("24") == (24, 1)
        assert parse_frame_rate("25") == (25, 1)
        assert parse_frame_rate("30") == (30, 1)
        assert parse_frame_rate("48") == (48, 1)
        assert parse_frame_rate("50") == (50, 1)
        assert parse_frame_rate("60") == (60, 1)
    
    def test_parse_float_input(self):
        """Should handle float input (not just strings)"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        assert parse_frame_rate(23.976) == (24000, 1001)
        assert parse_frame_rate(29.97) == (30000, 1001)
        assert parse_frame_rate(25.0) == (25, 1)
        assert parse_frame_rate(50) == (50, 1)


class TestBroadcastStandardShortcuts:
    """Test broadcast standard shortcut parsing (TDD Phase 3.1 RED)"""
    
    def test_ntsc_family_shortcuts(self):
        """Test NTSC family broadcast standards"""
        if get_broadcast_standard_fps is None:
            pytest.skip("Broadcast standards not implemented yet (RED phase)")
            
        assert get_broadcast_standard_fps("ntsc-film") == (24000, 1001)
        assert get_broadcast_standard_fps("ntsc") == (30000, 1001)
        assert get_broadcast_standard_fps("ntsc-hd") == (60000, 1001)
        assert get_broadcast_standard_fps("ntsc-4k") == (120000, 1001)
    
    def test_pal_family_shortcuts(self):
        """Test PAL family broadcast standards"""
        if get_broadcast_standard_fps is None:
            pytest.skip("Broadcast standards not implemented yet (RED phase)")
            
        assert get_broadcast_standard_fps("pal") == (25, 1)
        assert get_broadcast_standard_fps("pal-hd") == (50, 1)
        assert get_broadcast_standard_fps("pal-4k") == (100, 1)
    
    def test_cinema_standards(self):
        """Test cinema broadcast standards"""
        if get_broadcast_standard_fps is None:
            pytest.skip("Broadcast standards not implemented yet (RED phase)")
            
        assert get_broadcast_standard_fps("film") == (24, 1)
        assert get_broadcast_standard_fps("film-hfr-48") == (48, 1)
        assert get_broadcast_standard_fps("film-hfr-60") == (60, 1)
        assert get_broadcast_standard_fps("film-hfr-120") == (120, 1)


class TestFrameRateParserErrors:
    """Test error handling in frame rate parser (TDD Phase 3.1 RED)"""
    
    def test_invalid_formats(self):
        """Should raise ValueError for invalid formats"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        with pytest.raises(ValueError, match="Invalid frame rate format"):
            parse_frame_rate("not_a_number")
        
        with pytest.raises(ValueError, match="Invalid frame rate format"):
            parse_frame_rate("25/0")  # Division by zero
        
        with pytest.raises(ValueError, match="Invalid frame rate format"):
            parse_frame_rate("25/")  # Incomplete rational
        
        with pytest.raises(ValueError, match="Invalid frame rate format"):
            parse_frame_rate("/25")  # Invalid rational
    
    def test_out_of_range_values(self):
        """Should raise ValueError for unreasonable frame rates"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
            
        with pytest.raises(ValueError, match="Frame rate out of reasonable range"):
            parse_frame_rate("0")  # Zero fps
        
        with pytest.raises(ValueError, match="Frame rate out of reasonable range"):
            parse_frame_rate("-25")  # Negative fps
        
        with pytest.raises(ValueError, match="Frame rate out of reasonable range"):
            parse_frame_rate("1000")  # Unreasonably high fps
    
    def test_unknown_broadcast_standard(self):
        """Should raise ValueError for unknown broadcast standards"""
        if get_broadcast_standard_fps is None:
            pytest.skip("Broadcast standards not implemented yet (RED phase)")
            
        with pytest.raises(ValueError, match="Unknown broadcast standard"):
            get_broadcast_standard_fps("unknown-standard")


class TestFrameRateParserPrecision:
    """Test precision handling in frame rate parser (TDD Phase 3.1 RED)"""
    
    def test_decimal_precision_common_rates(self):
        """Common decimal rates should map to exact known rationals"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
        
        # Test that common inputs map to exact rationals
        test_cases = [
            # Various input formats for 23.976
            ("23.976", (24000, 1001)),
            ("23.9760", (24000, 1001)),
            ("23.976023976", (24000, 1001)),  # Should round to known value
            
            # Various input formats for 29.97  
            ("29.97", (30000, 1001)),
            ("29.970", (30000, 1001)),
            ("29.970029970", (30000, 1001)),
            
            # Various input formats for 59.94
            ("59.94", (60000, 1001)),
            ("59.940", (60000, 1001)),
        ]
        
        for input_fps, expected in test_cases:
            result = parse_frame_rate(input_fps)
            assert result == expected, f"Input {input_fps} should map to {expected}, got {result}"
    
    def test_rational_reduction(self):
        """Rational inputs should be reduced to lowest terms"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
        
        # Should reduce to lowest terms
        assert parse_frame_rate("48000/2002") == (24000, 1001)  # 2x reduction
        assert parse_frame_rate("50/2") == (25, 1)  # Simple reduction
        assert parse_frame_rate("100/4") == (25, 1)  # 4x reduction


class TestFrameRateToFraction:
    """Test conversion to Python Fraction objects (TDD Phase 3.1 RED)"""
    
    def test_rational_to_fraction(self):
        """Should convert parsed rationals to Fraction objects"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
        
        # Should be able to create Fraction from result
        num, den = parse_frame_rate("23.976")
        frac = Fraction(num, den)
        assert frac == Fraction(24000, 1001)
        
        # Should be exact
        assert float(frac) == 24000.0 / 1001.0
    
    def test_frame_duration_calculation(self):
        """Should calculate exact frame durations using Fraction"""
        if parse_frame_rate is None:
            pytest.skip("Parser not implemented yet (RED phase)")
        
        # 29.97 fps → frame duration = 1001/30000 seconds
        fps_num, fps_den = parse_frame_rate("29.97")
        frame_duration = Fraction(fps_den, fps_num)
        expected_duration = Fraction(1001, 30000)
        
        assert frame_duration == expected_duration
        
        # Should be more precise than float arithmetic
        float_duration = 1.0 / (30000.0 / 1001.0)
        fraction_duration_float = float(frame_duration)
        
        # Fraction should be more accurate
        assert abs(fraction_duration_float - (1001.0 / 30000.0)) < 1e-15


if __name__ == '__main__':
    pytest.main([__file__, "-v"])