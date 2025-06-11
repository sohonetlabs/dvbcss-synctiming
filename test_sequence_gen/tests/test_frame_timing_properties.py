#!/usr/bin/env python3
"""
Hypothesis Property Tests for Frame Timing Calculations - Phase 4.2

This module uses property-based testing to verify mathematical correctness
and invariants of frame timing calculations using rational arithmetic.

Phase 4.2: Hypothesis Property Tests for Frame Timing
- Property 1: Round-trip conversions should be identity or near-identity
- Property 2: Frame timing should be monotonically increasing
- Property 3: Mathematical relationships should hold exactly
- Property 4: Edge cases should be handled correctly
- Property 5: Precision should be exact for rational arithmetic
"""

import os
import sys
from fractions import Fraction

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from frame_timing import (
    calculate_frame_duration,
    calculate_sequence_duration,
    frame_to_seconds,
    seconds_to_frame,
)

# Strategy for valid frame rate rationals
valid_fps_rationals = st.one_of([
    # Integer frame rates
    st.tuples(st.integers(min_value=1, max_value=240), st.just(1)),
    
    # NTSC family (1001 denominator)
    st.tuples(
        st.sampled_from([24000, 30000, 48000, 60000, 120000]),
        st.just(1001)
    ),
    
    # Other reasonable rationals
    st.tuples(
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=1, max_value=100)
    ).filter(lambda fps: 1.0 <= fps[0]/fps[1] <= 240.0)
])


class TestFrameTimingProperties:
    """Property-based tests for frame timing calculations (TDD Phase 4.2)"""
    
    @given(st.integers(min_value=0, max_value=10000),
           valid_fps_rationals)
    @settings(max_examples=100)
    def test_frame_to_time_monotonic_property(self, frame_num, fps_rational):
        """Property: Frame timing should be monotonically increasing"""
        fps_num, fps_den = fps_rational
        
        # Frame N should be before frame N+1
        time_n = frame_to_seconds(frame_num, fps_num, fps_den)
        time_n_plus_1 = frame_to_seconds(frame_num + 1, fps_num, fps_den)
        
        assert time_n < time_n_plus_1, \
            f"Frame {frame_num} should be before frame {frame_num + 1}"
        
        # Time difference should equal frame duration
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        time_diff = time_n_plus_1 - time_n
        
        assert time_diff == frame_duration, \
            f"Time difference should equal frame duration: {time_diff} vs {frame_duration}"
    
    @given(st.integers(min_value=0, max_value=10000),
           valid_fps_rationals)
    @settings(max_examples=100) 
    def test_frame_time_roundtrip_property(self, frame_num, fps_rational):
        """Property: Frame → time → frame should be identity"""
        fps_num, fps_den = fps_rational
        
        # Frame → time
        time = frame_to_seconds(frame_num, fps_num, fps_den)
        
        # Time → frame
        reconstructed_frame = seconds_to_frame(time, fps_num, fps_den)
        
        assert reconstructed_frame == frame_num, \
            f"Round trip failed: {frame_num} → {time} → {reconstructed_frame}"
    
    @given(st.integers(min_value=1, max_value=1000),
           valid_fps_rationals)
    @settings(max_examples=50)
    def test_sequence_duration_linearity_property(self, n_frames, fps_rational):
        """Property: Sequence duration should scale linearly with frame count"""
        fps_num, fps_den = fps_rational
        
        # Single frame duration
        single_duration = calculate_frame_duration(fps_num, fps_den)
        
        # N frames duration
        sequence_duration = calculate_sequence_duration(n_frames, fps_num, fps_den)
        
        # Should be exactly N times single duration
        expected_duration = single_duration * n_frames
        
        assert sequence_duration == expected_duration, \
            f"Sequence duration should be linear: {sequence_duration} vs {expected_duration}"
    
    @given(valid_fps_rationals)
    def test_frame_duration_reciprocal_property(self, fps_rational):
        """Property: Frame duration should be exact reciprocal of frame rate"""
        fps_num, fps_den = fps_rational
        
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        fps_fraction = Fraction(fps_num, fps_den)
        
        # duration * fps should equal exactly 1
        product = frame_duration * fps_fraction
        
        assert product == 1, \
            f"Frame duration * fps should equal 1: {product}"
        
        # Frame duration should be fps_den / fps_num
        expected_duration = Fraction(fps_den, fps_num)
        
        assert frame_duration == expected_duration, \
            f"Frame duration should be {expected_duration}, got {frame_duration}"
    
    @given(st.fractions(min_value=0, max_value=1000),
           valid_fps_rationals)
    @settings(max_examples=100)
    def test_time_to_frame_consistency_property(self, time_input, fps_rational):
        """Property: Time-to-frame conversion should be consistent"""
        fps_num, fps_den = fps_rational
        
        # Convert time to frame
        frame = seconds_to_frame(time_input, fps_num, fps_den)
        
        # Frame should be non-negative
        assert frame >= 0, f"Frame number should be non-negative: {frame}"
        
        # Frame should be reasonable for given time
        fps_value = fps_num / fps_den
        max_expected_frame = int(float(time_input) * fps_value) + 1
        
        assert frame <= max_expected_frame, \
            f"Frame {frame} seems too high for time {time_input} at {fps_value} fps"
    
    @given(st.integers(min_value=0, max_value=1000),
           valid_fps_rationals)
    @settings(max_examples=50)
    def test_frame_zero_timing_property(self, offset_frames, fps_rational):
        """Property: Frame 0 should always be at time 0, regardless of fps"""
        fps_num, fps_den = fps_rational
        
        # Frame 0 should always be at time 0
        time_zero = frame_to_seconds(0, fps_num, fps_den)
        assert time_zero == 0, f"Frame 0 should be at time 0, got {time_zero}"
        
        # Time 0 should always give frame 0
        frame_zero = seconds_to_frame(0, fps_num, fps_den)
        assert frame_zero == 0, f"Time 0 should be frame 0, got {frame_zero}"


class TestFrameTimingMathematicalProperties:
    """Mathematical property tests for frame timing (TDD Phase 4.2)"""
    
    @given(st.integers(min_value=1, max_value=100),
           st.integers(min_value=1, max_value=100),
           valid_fps_rationals)
    @settings(max_examples=50)
    def test_frame_timing_additivity_property(self, frame_a, frame_b, fps_rational):
        """Property: Frame timing should be additive"""
        fps_num, fps_den = fps_rational
        
        # Time for frame A
        time_a = frame_to_seconds(frame_a, fps_num, fps_den)
        
        # Time for frame B  
        time_b = frame_to_seconds(frame_b, fps_num, fps_den)
        
        # Time for frame A+B
        time_a_plus_b = frame_to_seconds(frame_a + frame_b, fps_num, fps_den)
        
        # Should satisfy: time(A+B) = time(A) + time(B) - time(0)
        # Since time(0) = 0, this simplifies to: time(A+B) = time(A) + time(B)
        expected_time = time_a + time_b
        
        assert time_a_plus_b == expected_time, \
            f"Frame timing should be additive: {time_a_plus_b} vs {expected_time}"
    
    @given(st.integers(min_value=2, max_value=10),
           valid_fps_rationals)
    @settings(max_examples=30)
    def test_frame_timing_scaling_property(self, scale_factor, fps_rational):
        """Property: Scaling frame numbers should scale timing proportionally"""
        fps_num, fps_den = fps_rational
        
        base_frame = 10
        scaled_frame = base_frame * scale_factor
        
        # Time for base frame
        base_time = frame_to_seconds(base_frame, fps_num, fps_den)
        
        # Time for scaled frame
        scaled_time = frame_to_seconds(scaled_frame, fps_num, fps_den)
        
        # Scaled time should be exactly scale_factor times base time
        expected_scaled_time = base_time * scale_factor
        
        assert scaled_time == expected_scaled_time, \
            f"Scaled timing should be proportional: {scaled_time} vs {expected_scaled_time}"
    
    @given(valid_fps_rationals,
           valid_fps_rationals)
    @settings(max_examples=30)
    def test_frame_rate_comparison_property(self, fps_a, fps_b):
        """Property: Higher frame rates should have shorter frame durations"""
        fps_a_num, fps_a_den = fps_a
        fps_b_num, fps_b_den = fps_b
        
        # Calculate decimal frame rates
        fps_a_value = fps_a_num / fps_a_den
        fps_b_value = fps_b_num / fps_b_den
        
        # Skip if frame rates are too close
        assume(abs(fps_a_value - fps_b_value) > 0.1)
        
        # Calculate frame durations
        duration_a = calculate_frame_duration(fps_a_num, fps_a_den)
        duration_b = calculate_frame_duration(fps_b_num, fps_b_den)
        
        # Higher frame rate should have shorter duration
        if fps_a_value > fps_b_value:
            assert duration_a < duration_b, \
                f"Higher fps {fps_a_value} should have shorter duration than {fps_b_value}"
        elif fps_a_value < fps_b_value:
            assert duration_a > duration_b, \
                f"Lower fps {fps_a_value} should have longer duration than {fps_b_value}"
    
    @given(st.integers(min_value=1, max_value=1000),
           valid_fps_rationals)
    @settings(max_examples=50) 
    def test_rational_precision_property(self, frame_num, fps_rational):
        """Property: Rational arithmetic should be exact (no floating point errors)"""
        fps_num, fps_den = fps_rational
        
        # Calculate time using rational arithmetic
        exact_time = frame_to_seconds(frame_num, fps_rational[0], fps_rational[1])
        
        # Should be exact Fraction
        assert isinstance(exact_time, Fraction), "Result should be exact Fraction"
        
        # Manual calculation should give same result
        expected_time = Fraction(frame_num * fps_den, fps_num)
        
        assert exact_time == expected_time, \
            f"Manual calculation should match: {exact_time} vs {expected_time}"
        
        # Convert to float and back should preserve precision within limits
        float_time = float(exact_time)
        back_to_fraction = Fraction(float_time).limit_denominator(max_denominator=1000000)
        
        # Should be very close (limited by float precision)
        precision_error = abs(float(exact_time) - float(back_to_fraction))
        assert precision_error < 1e-10, f"Precision error too large: {precision_error}"


class TestFrameTimingEdgeCases:
    """Edge case property tests for frame timing (TDD Phase 4.2)"""
    
    @given(valid_fps_rationals)
    def test_frame_duration_bounds_property(self, fps_rational):
        """Property: Frame durations should be within reasonable bounds"""
        fps_num, fps_den = fps_rational
        
        duration = calculate_frame_duration(fps_num, fps_den)
        duration_seconds = float(duration)
        
        # Duration should be positive
        assert duration_seconds > 0, "Frame duration should be positive"
        
        # Duration should be reasonable (between 0.002 and 10 seconds)
        # 0.002s = 500fps, 10s = 0.1fps
        assert 0.002 <= duration_seconds <= 10.0, \
            f"Frame duration {duration_seconds} should be reasonable"
    
    @given(st.integers(min_value=0, max_value=0),  # Test specifically frame 0
           valid_fps_rationals)
    def test_frame_zero_edge_case_property(self, frame_num, fps_rational):
        """Property: Frame 0 edge case should work correctly"""
        fps_num, fps_den = fps_rational
        
        time = frame_to_seconds(frame_num, fps_num, fps_den)
        
        # Frame 0 should always give time 0
        assert time == 0, f"Frame 0 should give time 0, got {time}"
        
        # Time should be exact zero (not floating point approximation)
        assert time.numerator == 0, "Time should be exact zero"
        assert time.denominator == 1, "Zero should be represented as 0/1"
    
    @given(st.sampled_from([
        (24000, 1001), (30000, 1001), (60000, 1001)  # NTSC family
    ]))
    def test_ntsc_precision_property(self, fps_rational):
        """Property: NTSC frame rates should maintain exact precision"""
        fps_num, fps_den = fps_rational
        
        # Test that fps_num frames takes exactly 1001 seconds
        # This is the key NTSC relationship: fps_num frames / (fps_num/1001) fps = 1001 seconds
        n_frames = fps_num
        duration = calculate_sequence_duration(n_frames, fps_num, fps_den)
        
        # Should be exactly 1001 seconds
        expected_duration = Fraction(1001, 1)
        
        assert duration == expected_duration, \
            f"NTSC precision: {fps_num} frames should take exactly 1001 seconds: {duration} vs {expected_duration}"
        
        # Verify the mathematical relationship: fps_num frames at fps_num/1001 fps = 1001 seconds
        duration_float = float(duration)
        assert abs(duration_float - 1001.0) < 1e-10, \
            f"NTSC precision check: should be exactly 1001 seconds, got {duration_float}"


class TestFrameTimingBoundaryConditions:
    """Boundary condition tests using Hypothesis (TDD Phase 4.2)"""
    
    @given(st.sampled_from([1, 2, 10, 100, 1000]),  # Test specific boundaries
           valid_fps_rationals)
    def test_power_of_ten_frames_property(self, frame_power, fps_rational):
        """Property: Powers of 10 frame numbers should work correctly"""
        fps_num, fps_den = fps_rational
        
        time = frame_to_seconds(frame_power, fps_num, fps_den)
        back_frame = seconds_to_frame(time, fps_num, fps_den)
        
        # Round trip should work
        assert back_frame == frame_power, \
            f"Power of 10 round trip: {frame_power} → {time} → {back_frame}"
        
        # Time should be exact
        expected_time = Fraction(frame_power * fps_den, fps_num)
        assert time == expected_time, \
            f"Power of 10 timing should be exact: {time} vs {expected_time}"
    
    @given(st.floats(min_value=0.0, max_value=1.0),
           valid_fps_rationals)
    @settings(max_examples=50)
    def test_sub_second_timing_property(self, time_fraction, fps_rational):
        """Property: Sub-second timings should work correctly"""
        fps_num, fps_den = fps_rational
        
        # Convert to exact fraction
        time_input = Fraction(time_fraction).limit_denominator(max_denominator=10000)
        
        # Convert time to frame
        frame = seconds_to_frame(time_input, fps_num, fps_den)
        
        # Frame should be reasonable for sub-second timing
        fps_value = fps_num / fps_den
        max_expected_frame = int(fps_value) + 1
        
        assert 0 <= frame <= max_expected_frame, \
            f"Sub-second frame should be reasonable: {frame} for time {time_input}"


if __name__ == '__main__':
    pytest.main([__file__, "-v"])