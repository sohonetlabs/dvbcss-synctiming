#!/usr/bin/env python3
"""
Comprehensive tests for current generate.py functionality (integer frame rates only).

This module follows TDD principles to establish comprehensive test coverage
for the existing integer frame rate support before adding fractional rates.

Phase 2: RED → GREEN → REFACTOR approach
- RED: Write failing tests first
- GREEN: Make tests pass with current code
- REFACTOR: Improve code while keeping tests green
"""

import os
import sys

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eventTimingGen import mls
from generate import fpsBitTimings, genEventCentreTimes
from video import frameNumToTimecode


class TestCurrentFrameRateSupport:
    """Test existing integer frame rate functionality (TDD Phase 2.2)"""
    
    def test_supported_integer_frame_rates(self, supported_fps_rates):
        """Current code should support specific integer frame rates"""
        for fps in supported_fps_rates:
            assert fps in fpsBitTimings, f"Frame rate {fps} should be supported"
            assert 0 in fpsBitTimings[fps], f"Zero bit timing missing for {fps} fps"
            assert 1 in fpsBitTimings[fps], f"One bit timing missing for {fps} fps"
    
    def test_bit_timings_structure_zero_bit(self, supported_fps_rates):
        """Zero bit timings should have exactly one pulse"""
        for fps in supported_fps_rates:
            timings = fpsBitTimings[fps]
            assert len(timings[0]) == 1, f"Zero bit should have 1 pulse for {fps} fps"
    
    def test_bit_timings_structure_one_bit(self, supported_fps_rates):
        """One bit timings should have exactly two pulses"""
        for fps in supported_fps_rates:
            timings = fpsBitTimings[fps]
            assert len(timings[1]) == 2, f"One bit should have 2 pulses for {fps} fps"
    
    def test_bit_timings_all_positive(self, supported_fps_rates):
        """All timing values should be positive"""
        for fps in supported_fps_rates:
            timings = fpsBitTimings[fps]
            
            # Zero bit timings should be positive
            assert all(t > 0 for t in timings[0]), f"Zero bit timings should be positive for {fps} fps"
            
            # One bit timings should be positive
            assert all(t > 0 for t in timings[1]), f"One bit timings should be positive for {fps} fps"
    
    def test_bit_timings_pulse_order(self, supported_fps_rates):
        """Second pulse should come after first pulse for one bit"""
        for fps in supported_fps_rates:
            timings = fpsBitTimings[fps]
            assert timings[1][1] > timings[1][0], f"Second pulse should come after first for {fps} fps"


class TestEventGeneration:
    """Test event generation functionality (TDD Phase 2.2)"""
    
    def test_event_generation_produces_events(self, supported_fps_rates, small_sequence_bits):
        """Event generation should produce some events"""
        for fps in supported_fps_rates[:3]:  # Test subset for speed
            for seq_bits in small_sequence_bits[:2]:  # Test subset for speed
                # Take limited events from infinite generator
                events = []
                gen = genEventCentreTimes(seqBits=seq_bits, fps=fps)
                for i, event in enumerate(gen):
                    if i >= 10:  # Take only first 10 events
                        break
                    events.append(event)
                
                assert len(events) > 0, f"Should generate events for {fps} fps, {seq_bits} bits"
    
    def test_events_are_monotonic(self, supported_fps_rates, small_sequence_bits):
        """Generated events should be in ascending order"""
        for fps in [25, 50]:  # Test subset for speed
            for seq_bits in [3, 4]:  # Test subset for speed
                # Take limited events from infinite generator
                events = []
                gen = genEventCentreTimes(seqBits=seq_bits, fps=fps)
                for i, event in enumerate(gen):
                    if i >= 15:  # Take first 15 events
                        break
                    events.append(event)
                
                # Check monotonic order
                for i in range(len(events) - 1):
                    assert events[i] < events[i+1], f"Events should be ascending for {fps} fps"
    
    def test_events_are_non_negative(self, supported_fps_rates, small_sequence_bits):
        """All generated events should be non-negative"""
        for fps in [25, 30]:  # Test subset for speed
            # Take limited events from infinite generator
            events = []
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            for i, event in enumerate(gen):
                if i >= 10:  # Take first 10 events
                    break
                events.append(event)
            
            assert all(e >= 0 for e in events), f"All events should be non-negative for {fps} fps"


class TestMLSSequenceGeneration:
    """Test maximal-length sequence generation (TDD Phase 2.2)"""
    
    def test_mls_sequence_length(self, small_sequence_bits):
        """MLS sequences should have expected length 2^n - 1"""
        for seq_bits in small_sequence_bits:
            sequence = list(mls(seq_bits))
            expected_length = 2**seq_bits - 1
            
            assert len(sequence) == expected_length, f"MLS sequence should have length {expected_length}"
    
    def test_mls_sequence_binary_values(self, small_sequence_bits):
        """MLS sequences should contain only 0s and 1s"""
        for seq_bits in small_sequence_bits:
            sequence = list(mls(seq_bits))
            
            assert all(bit in [0, 1] for bit in sequence), "MLS sequence should contain only 0s and 1s"
    
    def test_mls_sequence_non_empty(self, small_sequence_bits):
        """MLS sequences should not be empty"""
        for seq_bits in small_sequence_bits:
            sequence = list(mls(seq_bits))
            
            assert len(sequence) > 0, f"MLS sequence should not be empty for {seq_bits} bits"


class TestTimecodeGeneration:
    """Test timecode generation for integer frame rates (TDD Phase 2.2)"""
    
    def test_frame_zero_timecode(self, supported_fps_rates):
        """Frame 0 should always be 00:00:00:00"""
        for fps in supported_fps_rates:
            result = frameNumToTimecode(0, fps, framesAreFields=False)
            assert result == "00:00:00:00", f"Frame 0 at {fps} fps should be 00:00:00:00"
    
    def test_one_second_timecode(self, supported_fps_rates):
        """Frame equal to fps should be 00:00:01:00"""
        for fps in supported_fps_rates:
            result = frameNumToTimecode(fps, fps, framesAreFields=False)
            assert result == "00:00:01:00", f"Frame {fps} at {fps} fps should be 00:00:01:00"
    
    def test_specific_timecode_cases(self):
        """Test specific known timecode conversions"""
        test_cases = [
            (90, 30, "00:00:03:00"),    # 3 seconds at 30fps
            (125, 25, "00:00:05:00"),   # 5 seconds at 25fps
            (1440, 24, "00:01:00:00"),  # 1 minute at 24fps
        ]
        
        for frame, fps, expected in test_cases:
            result = frameNumToTimecode(frame, fps, framesAreFields=False)
            assert result == expected, f"Frame {frame} at {fps} fps should be {expected}, got {result}"
    
    def test_timecode_format_structure(self, supported_fps_rates):
        """Timecode should have HH:MM:SS:FF format"""
        for fps in supported_fps_rates[:3]:  # Test subset
            result = frameNumToTimecode(0, fps, framesAreFields=False)
            parts = result.split(':')
            
            assert len(parts) == 4, f"Timecode should have 4 parts separated by colons"
            assert all(len(part) == 2 for part in parts), f"Each timecode part should be 2 digits"


class TestCurrentCodePropertyTests:
    """Property-based tests using Hypothesis (TDD Phase 2.3)"""
    
    @given(st.sampled_from([24, 25, 30, 48, 50, 60]))
    def test_bit_timing_frame_alignment_property(self, fps):
        """Property: Bit timings should align with expected frame positions"""
        timings = fpsBitTimings[fps]
        
        # The design uses base frame rates for timing calculations
        # 48fps uses 24fps base, 50fps uses 25fps base, 60fps uses 30fps base
        base_fps_map = {24: 24, 25: 25, 30: 30, 48: 24, 50: 25, 60: 30}
        base_fps = base_fps_map[fps]
        
        # Check all timing values align with expected positions
        for bit_val in [0, 1]:
            for timing in timings[bit_val]:
                # Timing should align with base frame rate centers
                base_frame_position = timing * base_fps
                expected_centers = [3.5, 9.5]  # From the code design
                
                # Find closest expected center
                closest_center = min(expected_centers, key=lambda x: abs(base_frame_position - x))
                
                # Allow small tolerance for floating point precision
                assert abs(base_frame_position - closest_center) < 0.001, \
                    f"Timing {timing} should align with base frame centers for {fps} fps (base: {base_fps})"
    
    @given(st.integers(min_value=3, max_value=6),
           st.sampled_from([24, 25, 30, 50]))
    @settings(max_examples=20)  # Limit examples for speed
    def test_event_generation_monotonic_property(self, seq_bits, fps):
        """Property: Generated events should be monotonically increasing"""
        # Take limited events from infinite generator
        events = []
        gen = genEventCentreTimes(seq_bits, fps)
        for i, event in enumerate(gen):
            if i >= 20:  # Take first 20 events
                break
            events.append(event)
        
        # Should be strictly increasing
        for i in range(len(events) - 1):
            assert events[i] < events[i + 1], \
                f"Events should be monotonic for {fps} fps, seq_bits {seq_bits}"
    
    @given(st.integers(min_value=0, max_value=10000),
           st.sampled_from([24, 25, 30, 48, 50, 60]))
    @settings(max_examples=50)  # Limit examples for speed
    def test_timecode_roundtrip_property(self, frame_num, fps):
        """Property: Frame→timecode→frame should be identity"""
        # Skip very large frame numbers to avoid overflow
        assume(frame_num < 3600 * fps)  # Less than 1 hour
        
        timecode = frameNumToTimecode(frame_num, fps)
        
        # Parse timecode back to frame number
        parts = timecode.split(':')
        if len(parts) == 4:
            h, m, s, f_str = parts
            # Handle field indicators if present
            f = int(f_str.split()[0]) if ' ' in f_str else int(f_str)
            reconstructed = (int(h) * 3600 + int(m) * 60 + int(s)) * fps + f
            
            assert reconstructed == frame_num, \
                f"Roundtrip failed: {frame_num} → {timecode} → {reconstructed}"
    
    @given(st.integers(min_value=3, max_value=6))
    @settings(max_examples=10)  # Limit examples for speed
    def test_mls_length_property(self, seq_bits):
        """Property: MLS sequence length should always be 2^n - 1"""
        sequence = list(mls(seq_bits))
        expected_length = 2**seq_bits - 1
        
        assert len(sequence) == expected_length, \
            f"MLS sequence should have length {expected_length} for {seq_bits} bits"


if __name__ == '__main__':
    pytest.main([__file__])