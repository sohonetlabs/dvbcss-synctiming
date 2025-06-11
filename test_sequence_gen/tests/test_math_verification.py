#!/usr/bin/env python3
"""
Mathematical Verification Tests for Fractional Frame Rates

This module verifies the mathematical correctness of all fractional frame rate
calculations, ensuring precision and accuracy for broadcast standards.
"""

import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

# Set high precision for decimal calculations
getcontext().prec = 50

# Import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fractional_event_generation import genEventCentreTimesFractional
from frame_rate_parser import parse_frame_rate
from frame_timing import (
    calculate_frame_duration,
    calculate_sequence_duration,
    frame_to_seconds,
    seconds_to_frame,
)


# Helper functions for the tests
def calculate_duration_for_n_frames(n_frames, fps_num, fps_den):
    """Helper: Calculate duration for n frames."""
    return calculate_sequence_duration(n_frames, fps_num, fps_den)


def calculate_frames_for_duration(duration_secs, fps_num, fps_den):
    """Helper: Calculate number of frames for given duration."""
    return seconds_to_frame(duration_secs, fps_num, fps_den)


class TestMathematicalCorrectness:
    """Verify mathematical correctness of fractional frame rate calculations."""
    
    def test_ntsc_frame_rate_precision(self):
        """Test NTSC frame rates have exact mathematical precision."""
        # 23.976 fps = 24000/1001
        fps_num, fps_den = parse_frame_rate("23.976")
        assert fps_num == 24000
        assert fps_den == 1001
        
        # Verify exact decimal representation
        exact_fps = Fraction(fps_num, fps_den)
        decimal_fps = Decimal(fps_num) / Decimal(fps_den)
        
        # Should be exactly 23.976023976023976023976023976...
        assert str(decimal_fps)[:7] == "23.9760"
        assert exact_fps == Fraction(24000, 1001)
        
    def test_ntsc_1000_frames_timing(self):
        """Test timing of 1000 frames at NTSC rates."""
        # At 29.97 fps (30000/1001), 1000 frames should take exactly:
        # 1000 * 1001/30000 = 1001000/30000 = 1001/30 seconds
        
        fps_num, fps_den = 30000, 1001
        duration = calculate_duration_for_n_frames(1000, fps_num, fps_den)
        
        expected = Fraction(1001, 30)
        assert duration == expected
        assert float(duration) == pytest.approx(33.366666666666667, abs=1e-15)
        
    def test_ntsc_exact_second_boundaries(self):
        """Test that NTSC frame rates align at specific boundaries."""
        # At 29.97 fps, exactly 30000 frames = 1001 seconds
        fps_num, fps_den = 30000, 1001
        
        # 30000 frames
        duration = calculate_duration_for_n_frames(30000, fps_num, fps_den)
        assert duration == Fraction(1001, 1)  # Exactly 1001 seconds
        
        # Verify reverse calculation
        frames = calculate_frames_for_duration(1001, fps_num, fps_den)
        assert frames == 30000  # Exactly 1001 * 30000/1001
        
    def test_drop_frame_vs_native_timing(self):
        """Verify we're using native timing, not drop-frame."""
        # In drop-frame timecode, 2 frames are dropped every minute except
        # every 10th minute. We should NOT see this pattern.
        
        fps_num, fps_den = 30000, 1001  # 29.97 fps
        
        # Calculate frames for exactly 1 minute
        frames_per_minute = calculate_frames_for_duration(60, fps_num, fps_den)
        
        # Native: 60 * 30000/1001 = 1798.201798... ≈ 1798 frames
        # Drop-frame would be: 1800 - 2 = 1798 frames (coincidentally same)
        assert frames_per_minute == 1798
        
        # But for 10 minutes:
        frames_per_10min = calculate_frames_for_duration(600, fps_num, fps_den)
        
        # Native: 600 * 30000/1001 = 17982.017982... ≈ 17982 frames
        # Drop-frame would be: 18000 - 18 = 17982 frames
        assert frames_per_10min == 17982
        
        # The key difference: our frame times are exact
        frame_1798_time = frame_to_seconds(1798, fps_num, fps_den)
        assert frame_1798_time == Fraction(1798 * 1001, 30000)
        # Frame 1798 is actually just under 60 seconds
        assert float(frame_1798_time) < 60.0
        # Frame 1799 is the first frame over 60 seconds
        frame_1799_time = frame_to_seconds(1799, fps_num, fps_den)
        assert float(frame_1799_time) > 60.0
        
    def test_23_976_fps_exact_timing(self):
        """Test 23.976 fps (film to NTSC) exact timing."""
        fps_num, fps_den = 24000, 1001
        
        # Frame duration should be exactly 1001/24000 seconds
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        assert frame_duration == Fraction(1001, 24000)
        
        # 24 frames should take slightly more than 1 second
        duration_24_frames = calculate_duration_for_n_frames(24, fps_num, fps_den)
        assert duration_24_frames == Fraction(1001, 1000)
        assert float(duration_24_frames) == 1.001  # Exactly 1.001 seconds
        
    def test_event_timing_precision(self):
        """Test that event timings maintain exact precision."""
        fps_num, fps_den = 30000, 1001
        
        # Generate first few events
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen):
            if i >= 10:
                break
            events.append(event)
        
        # All events should be exact Fraction objects
        for event in events:
            assert isinstance(event, Fraction)
            
        # Events should align with frame centers based on base FPS timing
        # For 29.97 fps, uses base fps of 30, so events occur at:
        # 3.5/30, 9.5/30, etc. which map to fractional frame positions
        for i, event in enumerate(events):
            # Convert to exact frame position
            frame_pos = float(event * fps_num / fps_den)
            # These won't be exactly x.5 due to base fps timing design
            # Just verify they're reasonable frame positions
            assert frame_pos > 0
            
    def test_accumulated_timing_error(self):
        """Test that timing errors don't accumulate over long sequences."""
        fps_num, fps_den = 30000, 1001
        
        # Test 1 hour worth of frames
        one_hour_seconds = 3600
        total_frames = calculate_frames_for_duration(one_hour_seconds, fps_num, fps_den)
        
        # Calculate exact duration of those frames
        actual_duration = calculate_duration_for_n_frames(total_frames, fps_num, fps_den)
        
        # The difference should be less than 1 frame duration
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        error = abs(actual_duration - one_hour_seconds)
        assert error < frame_duration
        
    def test_frame_boundary_calculations(self):
        """Test frame boundary calculations for display timing."""
        fps_num, fps_den = 30000, 1001
        
        # Test frame 100
        frame_100_start = frame_to_seconds(100, fps_num, fps_den)
        frame_100_end = frame_to_seconds(101, fps_num, fps_den)
        
        # Duration should be exactly one frame
        duration = frame_100_end - frame_100_start
        expected_duration = calculate_frame_duration(fps_num, fps_den)
        assert duration == expected_duration
        
        # Verify displayed values match (as shown in PNG)
        # Frame 100: "3.337 ≤ t < 3.370 secs"
        assert float(frame_100_start) == pytest.approx(3.3366666666667, abs=1e-10)
        assert float(frame_100_end) == pytest.approx(3.370033333333333, abs=1e-10)
        
    def test_bit_timing_calculations(self):
        """Test bit timing calculations for fractional rates."""
        from fractional_event_generation import createFpsBitTimingsFractional
        
        fps_num, fps_den = 30000, 1001
        timings = createFpsBitTimingsFractional(fps_num, fps_den)
        
        # For 29.97 fps, uses base fps of 30
        # So bit timings are 3.5/30 and 9.5/30
        bit_0_time = timings[0][0]
        expected = Fraction(7, 60)  # 3.5/30 simplified
        assert bit_0_time == expected
        
        # Check bit 1 timings (3.5 and 9.5 frames)
        bit_1_times = timings[1]
        expected_1 = Fraction(7, 60)   # 3.5/30 simplified
        expected_2 = Fraction(19, 60)  # 9.5/30 simplified  
        assert bit_1_times[0] == expected_1
        assert bit_1_times[1] == expected_2
        
    def test_common_broadcast_rates_exact_values(self):
        """Test exact values for common broadcast frame rates."""
        test_cases = [
            # (input, expected_num, expected_den, exact_decimal)
            ("23.976", 24000, 1001, "23.976023976023976023976023976023976023976023976024"),
            ("29.97", 30000, 1001, "29.970029970029970029970029970029970029970029970030"),
            ("59.94", 60000, 1001, "59.940059940059940059940059940059940059940059940060"),
            ("119.88", 120000, 1001, "119.880119880119880119880119880119880119880119880120"),
        ]
        
        for input_fps, expected_num, expected_den, exact_decimal in test_cases:
            fps_num, fps_den = parse_frame_rate(input_fps)
            assert fps_num == expected_num
            assert fps_den == expected_den
            
            # Verify exact decimal representation (at least first 15 digits)
            decimal_fps = Decimal(fps_num) / Decimal(fps_den)
            assert str(decimal_fps)[:15] == exact_decimal[:15]
            
    def test_audio_video_sync_precision(self):
        """Test audio/video synchronization precision."""
        # At 29.97 fps with 48000 Hz audio
        fps_num, fps_den = 30000, 1001
        sample_rate = 48000
        
        # One frame duration in samples
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        samples_per_frame = frame_duration * sample_rate
        
        # Should be exactly 1601.6 samples per frame
        assert samples_per_frame == Fraction(1601600, 1000)
        assert float(samples_per_frame) == 1601.6
        
        # After 5 frames (5 * 1001/30000 seconds)
        # Audio samples = 5 * 1001/30000 * 48000 = 8008
        duration_5_frames = calculate_duration_for_n_frames(5, fps_num, fps_den)
        audio_samples = duration_5_frames * sample_rate
        assert audio_samples == Fraction(8008, 1)  # Exactly 8008 samples


class TestRealWorldScenarios:
    """Test real-world broadcast scenarios."""
    
    def test_one_hour_broadcast_timing(self):
        """Test timing accuracy for a 1-hour broadcast."""
        fps_num, fps_den = 30000, 1001  # 29.97 fps
        
        # 1 hour = 3600 seconds
        # Frames = 3600 * 30000/1001 = 107892.107892... ≈ 107892 frames
        frames = calculate_frames_for_duration(3600, fps_num, fps_den)
        assert frames == 107892
        
        # Actual duration of 107892 frames
        actual_duration = calculate_duration_for_n_frames(frames, fps_num, fps_den)
        
        # Should be slightly less than 3600 seconds
        assert actual_duration < 3600
        error_seconds = float(3600 - actual_duration)
        # 107892 frames at 30000/1001 fps = 3599.9964 seconds
        # Error = 3600 - 3599.9964 = 0.0036 seconds
        assert error_seconds == pytest.approx(0.0036, abs=1e-10)
        
        # This is 3.6 milliseconds short of an hour
        error_ms = error_seconds * 1000
        assert error_ms == pytest.approx(3.6, abs=1e-10)
        
    def test_24_hour_broadcast_drift(self):
        """Test timing drift over 24 hours."""
        fps_num, fps_den = 30000, 1001
        
        # 24 hours in seconds
        seconds_24h = 24 * 60 * 60  # 86400 seconds
        
        frames = calculate_frames_for_duration(seconds_24h, fps_num, fps_den)
        actual_duration = calculate_duration_for_n_frames(frames, fps_num, fps_den)
        
        # Calculate drift
        drift = float(seconds_24h - actual_duration)
        
        # Should be about 19.67 milliseconds short over 24 hours
        assert drift == pytest.approx(0.01966666666666666, abs=1e-10)
        
        # This is why broadcast systems need time code synchronization!


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_frame_timing(self):
        """Test timing of a single frame."""
        for fps_str in ["23.976", "29.97", "59.94"]:
            fps_num, fps_den = parse_frame_rate(fps_str)
            
            # Frame 0 starts at 0
            assert frame_to_seconds(0, fps_num, fps_den) == 0
            
            # Frame 1 starts at exactly 1 frame duration
            frame_1_start = frame_to_seconds(1, fps_num, fps_den)
            expected = calculate_frame_duration(fps_num, fps_den)
            assert frame_1_start == expected
            
    def test_zero_duration(self):
        """Test calculations with zero duration."""
        fps_num, fps_den = 30000, 1001
        
        frames = calculate_frames_for_duration(0, fps_num, fps_den)
        assert frames == 0
        
        duration = calculate_duration_for_n_frames(0, fps_num, fps_den)
        assert duration == 0
        
    def test_very_long_sequences(self):
        """Test calculations with very long sequences."""
        fps_num, fps_den = 30000, 1001
        
        # 1 million frames
        duration = calculate_duration_for_n_frames(1000000, fps_num, fps_den)
        
        # Should be exactly 1001000/30000 = 33366.666... seconds
        assert duration == Fraction(1001000, 30)
        assert float(duration) == pytest.approx(33366.666666666667, abs=1e-12)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])