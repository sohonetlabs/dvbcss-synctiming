#!/usr/bin/env python3
"""
Frame Timing Calculation Tests - Phase 4.1: RED → GREEN → REFACTOR

This module implements TDD for precise frame timing calculations using rational arithmetic.
Tests exact frame-to-time and time-to-frame conversions for fractional frame rates.

Phase 4.1: Rational Arithmetic Tests for Timing
- RED: Write failing tests for frame timing calculations
- GREEN: Implement timing functions to make tests pass
- REFACTOR: Clean up timing calculation implementation

Key timing functions to test:
- frame_to_seconds(frame_num, fps_num, fps_den) → exact time
- seconds_to_frame(time_secs, fps_num, fps_den) → frame number
- calculate_frame_duration(fps_num, fps_den) → exact duration
- calculate_sequence_duration(n_frames, fps_num, fps_den) → total time
"""

import os
import sys
from fractions import Fraction

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import will fail initially - that's part of RED phase
try:
    from frame_timing import (
        calculate_frame_duration,
        calculate_sequence_duration,
        frame_to_seconds,
        seconds_to_frame,
        validate_fps_rational,
    )
except ImportError:
    # Expected during RED phase - timing module doesn't exist yet
    frame_to_seconds = None
    seconds_to_frame = None
    calculate_frame_duration = None
    calculate_sequence_duration = None
    validate_fps_rational = None


class TestFrameToTimeConversion:
    """Basic frame-to-time conversion tests (TDD Phase 4.1 RED)"""
    
    def test_frame_zero_always_zero_time(self):
        """Frame 0 should always be at time 0"""
        if frame_to_seconds is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_rates = [(24, 1), (25, 1), (30, 1), (24000, 1001), (30000, 1001)]
        
        for fps_num, fps_den in test_rates:
            time = frame_to_seconds(0, fps_num, fps_den)
            assert time == 0, f"Frame 0 should be at time 0 for {fps_num}/{fps_den} fps"
    
    def test_one_second_frame_conversion(self):
        """Frame equal to fps should be at exactly 1 second"""
        if frame_to_seconds is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # Integer frame rates
        integer_rates = [(24, 1), (25, 1), (30, 1), (50, 1), (60, 1)]
        
        for fps_num, fps_den in integer_rates:
            fps_value = fps_num // fps_den
            time = frame_to_seconds(fps_value, fps_num, fps_den)
            assert time == 1, f"Frame {fps_value} should be at 1 second for {fps_num}/{fps_den} fps"
    
    def test_fractional_fps_precise_timing(self):
        """Fractional frame rates should have exact timing"""
        if frame_to_seconds is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # 29.97 fps: frame 30 should be at exactly 30 * 1001/30000 seconds
        fps_num, fps_den = 30000, 1001
        frame_num = 30
        
        time = frame_to_seconds(frame_num, fps_num, fps_den)
        expected_time = Fraction(frame_num * fps_den, fps_num)
        
        assert time == expected_time, f"Frame {frame_num} timing should be exact"
        
        # Should be approximately 1.001 seconds
        time_float = float(time)
        assert abs(time_float - 1.001) < 0.0001, f"Time should be ~1.001 seconds, got {time_float}"
    
    def test_frame_conversion_returns_fraction(self):
        """Frame timing should return Fraction objects for exact arithmetic"""
        if frame_to_seconds is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        time = frame_to_seconds(100, 24000, 1001)
        assert isinstance(time, Fraction), "Should return Fraction for exact arithmetic"
        
        # Should be reducible
        assert time.numerator > 0, "Numerator should be positive"
        assert time.denominator > 0, "Denominator should be positive"


class TestTimeToFrameConversion:
    """Time-to-frame conversion tests (TDD Phase 4.1 RED)"""
    
    def test_time_zero_always_frame_zero(self):
        """Time 0 should always be frame 0"""
        if seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_rates = [(24, 1), (25, 1), (30, 1), (24000, 1001), (30000, 1001)]
        
        for fps_num, fps_den in test_rates:
            frame = seconds_to_frame(0, fps_num, fps_den)
            assert frame == 0, f"Time 0 should be frame 0 for {fps_num}/{fps_den} fps"
    
    def test_one_second_to_frame_conversion(self):
        """One second should convert to fps frame number"""
        if seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # Integer rates
        integer_rates = [(24, 1), (25, 1), (30, 1), (50, 1)]
        
        for fps_num, fps_den in integer_rates:
            fps_value = fps_num // fps_den
            frame = seconds_to_frame(1, fps_num, fps_den)
            assert frame == fps_value, f"1 second should be frame {fps_value} for {fps_num}/{fps_den} fps"
    
    def test_fractional_time_to_frame(self):
        """Fractional time inputs should convert correctly"""
        if seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # 29.97 fps: 1001/30000 seconds should be frame 1
        fps_num, fps_den = 30000, 1001
        time_input = Fraction(1001, 30000)
        
        frame = seconds_to_frame(time_input, fps_num, fps_den)
        assert frame == 1, f"Time {time_input} should be frame 1"
    
    def test_accepts_fraction_and_float_input(self):
        """Time conversion should accept both Fraction and float inputs"""
        if seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        fps_num, fps_den = 25, 1
        
        # Test with Fraction input
        time_frac = Fraction(2, 1)  # 2 seconds
        frame_frac = seconds_to_frame(time_frac, fps_num, fps_den)
        
        # Test with float input
        time_float = 2.0  # 2 seconds  
        frame_float = seconds_to_frame(time_float, fps_num, fps_den)
        
        assert frame_frac == frame_float == 50, "Both input types should give same result"


class TestRoundTripConversions:
    """Round-trip conversion tests (TDD Phase 4.1 RED)"""
    
    def test_frame_to_time_to_frame_identity(self):
        """Frame → time → frame should be identity"""
        if frame_to_seconds is None or seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_cases = [
            (0, 25, 1),      # Frame 0
            (100, 25, 1),    # Frame 100 at 25 fps
            (250, 30000, 1001),  # Frame 250 at 29.97 fps
            (1000, 24000, 1001), # Frame 1000 at 23.976 fps
        ]
        
        for frame, fps_num, fps_den in test_cases:
            # Frame → time
            time = frame_to_seconds(frame, fps_num, fps_den)
            
            # Time → frame  
            reconstructed_frame = seconds_to_frame(time, fps_num, fps_den)
            
            assert reconstructed_frame == frame, \
                f"Round trip failed: {frame} → {time} → {reconstructed_frame}"
    
    def test_time_to_frame_to_time_near_identity(self):
        """Time → frame → time should be close (within frame precision)"""
        if frame_to_seconds is None or seconds_to_frame is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_cases = [
            (Fraction(1, 2), 25, 1),     # 0.5 seconds at 25 fps
            (Fraction(5, 4), 30000, 1001), # 1.25 seconds at 29.97 fps
            (Fraction(10, 3), 24, 1),    # 3.333... seconds at 24 fps
        ]
        
        for time, fps_num, fps_den in test_cases:
            # Time → frame
            frame = seconds_to_frame(time, fps_num, fps_den)
            
            # Frame → time
            reconstructed_time = frame_to_seconds(frame, fps_num, fps_den)
            
            # Should be within one frame duration
            frame_duration = Fraction(fps_den, fps_num)
            time_diff = abs(float(reconstructed_time) - float(time))
            
            assert time_diff <= float(frame_duration), \
                f"Time round trip error too large: {time_diff} > {float(frame_duration)}"


class TestFrameDurationCalculation:
    """Frame duration calculation tests (TDD Phase 4.1 RED)"""
    
    def test_integer_fps_frame_duration(self):
        """Integer fps should have simple frame durations"""
        if calculate_frame_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_cases = [
            (24, 1, Fraction(1, 24)),    # 24 fps
            (25, 1, Fraction(1, 25)),    # 25 fps  
            (30, 1, Fraction(1, 30)),    # 30 fps
            (60, 1, Fraction(1, 60)),    # 60 fps
        ]
        
        for fps_num, fps_den, expected_duration in test_cases:
            duration = calculate_frame_duration(fps_num, fps_den)
            assert duration == expected_duration, \
                f"Frame duration for {fps_num}/{fps_den} should be {expected_duration}"
    
    def test_fractional_fps_frame_duration(self):
        """Fractional fps should have exact rational durations"""
        if calculate_frame_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_cases = [
            (24000, 1001, Fraction(1001, 24000)),  # 23.976 fps
            (30000, 1001, Fraction(1001, 30000)),  # 29.97 fps
            (60000, 1001, Fraction(1001, 60000)),  # 59.94 fps
        ]
        
        for fps_num, fps_den, expected_duration in test_cases:
            duration = calculate_frame_duration(fps_num, fps_den)
            assert duration == expected_duration, \
                f"Frame duration for {fps_num}/{fps_den} should be {expected_duration}"
    
    def test_frame_duration_reciprocal_property(self):
        """Frame duration should be reciprocal of frame rate"""
        if calculate_frame_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        test_rates = [(24, 1), (25, 1), (30000, 1001), (60000, 1001)]
        
        for fps_num, fps_den in test_rates:
            duration = calculate_frame_duration(fps_num, fps_den)
            fps_fraction = Fraction(fps_num, fps_den)
            
            # duration * fps should equal 1
            product = duration * fps_fraction
            assert product == 1, f"Duration * fps should equal 1, got {product}"


class TestSequenceDurationCalculation:
    """Sequence duration calculation tests (TDD Phase 4.1 RED)"""
    
    def test_sequence_duration_integer_fps(self):
        """Sequence duration for integer frame rates"""
        if calculate_sequence_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # 100 frames at 25 fps = 4 seconds exactly
        duration = calculate_sequence_duration(100, 25, 1)
        assert duration == 4, f"100 frames at 25 fps should be 4 seconds"
        
        # 150 frames at 30 fps = 5 seconds exactly  
        duration = calculate_sequence_duration(150, 30, 1)
        assert duration == 5, f"150 frames at 30 fps should be 5 seconds"
    
    def test_sequence_duration_fractional_fps(self):
        """Sequence duration for fractional frame rates"""
        if calculate_sequence_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        # 30000 frames at 30000/1001 fps = 1001 seconds exactly
        duration = calculate_sequence_duration(30000, 30000, 1001)
        expected = Fraction(1001, 1)
        assert duration == expected, f"30000 frames at 29.97 fps should be 1001 seconds"
        
        # 24000 frames at 24000/1001 fps = 1001 seconds exactly
        duration = calculate_sequence_duration(24000, 24000, 1001)
        expected = Fraction(1001, 1)
        assert duration == expected, f"24000 frames at 23.976 fps should be 1001 seconds"
    
    def test_sequence_duration_zero_frames(self):
        """Zero frames should have zero duration"""
        if calculate_sequence_duration is None:
            pytest.skip("Timing functions not implemented yet (RED phase)")
        
        duration = calculate_sequence_duration(0, 25, 1)
        assert duration == 0, "Zero frames should have zero duration"


class TestFrameTimingValidation:
    """Frame timing validation tests (TDD Phase 4.1 RED)"""
    
    def test_fps_rational_validation(self):
        """FPS rational validation should reject invalid inputs"""
        if validate_fps_rational is None:
            pytest.skip("Validation functions not implemented yet (RED phase)")
        
        # Valid inputs should pass
        validate_fps_rational(25, 1)      # Integer fps
        validate_fps_rational(30000, 1001) # Fractional fps
        
        # Invalid inputs should raise ValueError
        with pytest.raises(ValueError, match="denominator must be positive"):
            validate_fps_rational(25, 0)
        
        with pytest.raises(ValueError, match="denominator must be positive"):
            validate_fps_rational(25, -1)
        
        with pytest.raises(ValueError, match="numerator must be positive"):
            validate_fps_rational(0, 1)
        
        with pytest.raises(ValueError, match="numerator must be positive"):
            validate_fps_rational(-25, 1)
    
    def test_unreasonable_fps_rejection(self):
        """Unreasonable frame rates should be rejected"""
        if validate_fps_rational is None:
            pytest.skip("Validation functions not implemented yet (RED phase)")
        
        # Very high fps should be rejected
        with pytest.raises(ValueError, match="Frame rate out of reasonable range"):
            validate_fps_rational(10000, 1)
        
        # Very low fps should be rejected  
        with pytest.raises(ValueError, match="Frame rate out of reasonable range"):
            validate_fps_rational(1, 100)  # 0.01 fps


if __name__ == '__main__':
    pytest.main([__file__, "-v"])