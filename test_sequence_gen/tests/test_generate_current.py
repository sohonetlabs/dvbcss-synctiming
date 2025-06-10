#!/usr/bin/env python
"""
Tests for current generate.py functionality (integer frame rates only).

This module tests the existing integer frame rate support to establish a baseline
before adding fractional frame rate functionality. All tests here should pass
with the current codebase.
"""

import sys
import os
import unittest
from hypothesis import given, strategies as st, assume
import math

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate import fpsBitTimings, genEventCentreTimes
from video import frameNumToTimecode
from eventTimingGen import mls


class TestCurrentFrameRateSupport(unittest.TestCase):
    """Test existing integer frame rate functionality"""
    
    def test_supported_integer_frame_rates(self):
        """Current code should support specific integer frame rates"""
        supported_rates = [24, 25, 30, 48, 50, 60]
        
        for fps in supported_rates:
            with self.subTest(fps=fps):
                self.assertIn(fps, fpsBitTimings, 
                             f"Frame rate {fps} should be supported")
                self.assertIn(0, fpsBitTimings[fps], 
                             f"Zero bit timing missing for {fps} fps")
                self.assertIn(1, fpsBitTimings[fps], 
                             f"One bit timing missing for {fps} fps")
    
    def test_bit_timings_structure(self):
        """Bit timings should follow expected structure"""
        for fps, timings in fpsBitTimings.items():
            with self.subTest(fps=fps):
                # Zero bit has exactly one pulse
                self.assertEqual(len(timings[0]), 1, 
                               f"Zero bit should have 1 pulse for {fps} fps")
                
                # One bit has exactly two pulses
                self.assertEqual(len(timings[1]), 2, 
                               f"One bit should have 2 pulses for {fps} fps")
                
                # All timings are positive
                self.assertTrue(all(t > 0 for t in timings[0]), 
                               f"Zero bit timings should be positive for {fps} fps")
                self.assertTrue(all(t > 0 for t in timings[1]), 
                               f"One bit timings should be positive for {fps} fps")
                
                # Second pulse comes after first for one bit
                self.assertGreater(timings[1][1], timings[1][0], 
                                 f"Second pulse should come after first for {fps} fps")
    
    def test_event_generation_basic(self):
        """Test basic event generation for each supported fps"""
        for fps in [24, 25, 30, 50]:
            with self.subTest(fps=fps):
                events = list(genEventCentreTimes(seqBits=4, fps=fps))
                
                # Should generate some events
                self.assertGreater(len(events), 0, 
                                 f"Should generate events for {fps} fps")
                
                # Events should be in ascending order
                for i in range(len(events) - 1):
                    self.assertLess(events[i], events[i+1], 
                                   f"Events should be ascending for {fps} fps")
                
                # All events should be non-negative
                self.assertTrue(all(e >= 0 for e in events), 
                               f"All events should be non-negative for {fps} fps")
    
    def test_mls_sequence_properties(self):
        """Test that MLS sequences have expected properties"""
        for seq_bits in [3, 4, 5]:
            with self.subTest(seq_bits=seq_bits):
                sequence = list(mls(seq_bits))
                expected_length = 2**seq_bits - 1
                
                # Sequence should have expected length
                self.assertEqual(len(sequence), expected_length,
                               f"MLS sequence should have length {expected_length}")
                
                # Should contain only 0s and 1s
                self.assertTrue(all(bit in [0, 1] for bit in sequence),
                               "MLS sequence should contain only 0s and 1s")


class TestCurrentTimecodeGeneration(unittest.TestCase):
    """Test timecode generation for integer frame rates"""
    
    def test_frame_to_timecode_conversion(self):
        """Test frame number to timecode conversion"""
        test_cases = [
            # (frame_num, fps, expected_timecode)
            (0, 25, "00:00:00:00"),
            (25, 25, "00:00:01:00"),
            (90, 30, "00:00:03:00"),
            (3661, 25, "00:02:26:11"),
            (86399, 24, "00:59:59:23"),  # Last frame of an hour
        ]
        
        for frame, fps, expected in test_cases:
            with self.subTest(frame=frame, fps=fps):
                result = frameNumToTimecode(frame, fps, framesAreFields=False)
                self.assertEqual(result, expected,
                               f"Frame {frame} at {fps} fps should be {expected}")
    
    def test_timecode_with_fields(self):
        """Test timecode generation in fields mode"""
        # Test a few basic cases with fields
        result = frameNumToTimecode(50, 25, framesAreFields=True)
        # Should include field indicator
        self.assertIn("○1", result)  # or "●2" depending on field


class TestCurrentEventProperties(unittest.TestCase):
    """Property-based tests for current functionality using Hypothesis"""
    
    @given(st.sampled_from([24, 25, 30, 48, 50, 60]))
    def test_bit_timing_frame_alignment(self, fps):
        """Property: Bit timings should align with frame boundaries"""
        timings = fpsBitTimings[fps]
        
        # Check all timing values
        for bit_val in [0, 1]:
            for timing in timings[bit_val]:
                with self.subTest(fps=fps, bit=bit_val, timing=timing):
                    # Timing * fps should be close to frame center (n + 0.5)
                    frame_position = timing * fps
                    frame_center = round(frame_position - 0.5) + 0.5
                    self.assertAlmostEqual(frame_position, frame_center, places=3,
                                         msg=f"Timing {timing} should align with frame for {fps} fps")
    
    @given(st.integers(min_value=3, max_value=8),
           st.sampled_from([24, 25, 30, 48, 50, 60]))
    def test_event_generation_monotonic(self, seq_bits, fps):
        """Property: Generated events should be monotonically increasing"""
        events = list(genEventCentreTimes(seq_bits, fps))
        
        # Take first 50 events to keep test fast
        test_events = events[:50]
        
        # Should be strictly increasing
        for i in range(len(test_events) - 1):
            self.assertLess(test_events[i], test_events[i + 1],
                           f"Events should be monotonic for {fps} fps, seq_bits {seq_bits}")
    
    @given(st.integers(min_value=3, max_value=8),
           st.sampled_from([24, 25, 30, 48, 50, 60]))
    def test_event_generation_bounds(self, seq_bits, fps):
        """Property: Events should be within expected sequence duration"""
        max_duration = 2**seq_bits - 1
        events = []
        
        # Collect events up to max duration
        for event in genEventCentreTimes(seq_bits, fps):
            if event >= max_duration:
                break
            events.append(event)
        
        # All collected events should be within bounds
        for event in events:
            self.assertGreaterEqual(event, 0, "Events should be non-negative")
            self.assertLess(event, max_duration, 
                           f"Events should be less than {max_duration} seconds")
    
    @given(st.integers(min_value=0, max_value=100000),
           st.sampled_from([24, 25, 30, 48, 50, 60]))
    def test_timecode_roundtrip(self, frame_num, fps):
        """Property: Frame→timecode→frame should be identity"""
        # Skip very large frame numbers that might cause overflow
        assume(frame_num < 24 * 3600 * fps)  # Less than 24 hours
        
        timecode = frameNumToTimecode(frame_num, fps)
        
        # Parse timecode back to frame number
        try:
            parts = timecode.split(':')
            if len(parts) == 4:
                h, m, s, f_str = parts
                # Handle field indicators
                f = int(f_str.split()[0]) if ' ' in f_str else int(f_str)
                reconstructed = (int(h) * 3600 + int(m) * 60 + int(s)) * fps + f
                
                self.assertEqual(reconstructed, frame_num,
                               f"Roundtrip failed: {frame_num} → {timecode} → {reconstructed}")
        except (ValueError, IndexError):
            self.fail(f"Could not parse timecode: {timecode}")


if __name__ == '__main__':
    unittest.main()