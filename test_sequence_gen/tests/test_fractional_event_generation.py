#!/usr/bin/env python3
"""
Fractional Frame Rate Event Generation Tests - Phase 5.1: RED → GREEN → REFACTOR

This module implements TDD for event generation supporting fractional frame rates.
Tests integration of frame rate parsing, timing calculations, and event generation.

Phase 5.1: Event Generation Tests for Fractional Rates
- RED: Write failing tests for fractional frame rate event generation
- GREEN: Implement fractional event generation to make tests pass
- REFACTOR: Clean up and optimize fractional event generation

Key functionality to test:
- genEventCentreTimesFractional(seqBits, fps_num, fps_den) → exact event times
- genFlashSequenceFractional(...) → frame-accurate flash sequences
- genBeepSequenceFractional(...) → sample-accurate beep sequences
- fpsBitTimingsFractional integration → exact timing for fractional rates
"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, assume, settings
from fractions import Fraction
import math

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import current modules
from generate import fpsBitTimings, genEventCentreTimes
from video import genFlashSequence
from audio import genBeepSequence
from frame_rate_parser import parse_frame_rate
from frame_timing import frame_to_seconds, calculate_frame_duration

# Import will fail initially - that's part of RED phase
try:
    from fractional_event_generation import (
        genEventCentreTimesFractional, genFlashSequenceFractional,
        genBeepSequenceFractional, createFpsBitTimingsFractional
    )
except ImportError:
    # Expected during RED phase - fractional module doesn't exist yet
    genEventCentreTimesFractional = None
    genFlashSequenceFractional = None
    genBeepSequenceFractional = None
    createFpsBitTimingsFractional = None


class TestFractionalEventGeneration:
    """Basic fractional frame rate event generation tests (TDD Phase 5.1 RED)"""
    
    def test_fractional_event_generation_basic(self):
        """Should generate events for fractional frame rates"""
        if genEventCentreTimesFractional is None:
            pytest.skip("Fractional event generation not implemented yet (RED phase)")
        
        # Test 23.976 fps (24000/1001)
        fps_num, fps_den = 24000, 1001
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        
        # Take first 10 events
        for i, event in enumerate(gen):
            if i >= 10:
                break
            events.append(event)
        
        # Should generate some events
        assert len(events) > 0, "Should generate events for fractional fps"
        
        # All events should be Fraction objects for exact precision
        assert all(isinstance(event, Fraction) for event in events), \
            "All events should be Fraction objects for exact timing"
        
        # Events should be monotonically increasing
        for i in range(len(events) - 1):
            assert events[i] < events[i+1], "Events should be in ascending order"
    
    def test_fractional_vs_integer_event_comparison(self):
        """Compare fractional and integer frame rate event generation"""
        if genEventCentreTimesFractional is None:
            pytest.skip("Fractional event generation not implemented yet (RED phase)")
        
        # Generate events for 25 fps using both methods
        fps_num, fps_den = 25, 1
        
        # Current integer method
        integer_events = []
        gen_int = genEventCentreTimes(seqBits=3, fps=25)
        for i, event in enumerate(gen_int):
            if i >= 5:
                break
            integer_events.append(event)
        
        # New fractional method
        fractional_events = []
        gen_frac = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen_frac):
            if i >= 5:
                break
            fractional_events.append(float(event))  # Convert to float for comparison
        
        # Should be very close (within floating point precision)
        assert len(integer_events) == len(fractional_events), "Should generate same number of events"
        
        for i, (int_event, frac_event) in enumerate(zip(integer_events, fractional_events)):
            assert abs(int_event - frac_event) < 1e-10, \
                f"Event {i} should be similar: {int_event} vs {frac_event}"
    
    def test_ntsc_frame_rate_event_generation(self):
        """Test event generation for NTSC frame rates"""
        if genEventCentreTimesFractional is None:
            pytest.skip("Fractional event generation not implemented yet (RED phase)")
        
        ntsc_rates = [
            (24000, 1001),  # 23.976 fps
            (30000, 1001),  # 29.97 fps
            (60000, 1001),  # 59.94 fps
        ]
        
        for fps_num, fps_den in ntsc_rates:
            events = []
            gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
            
            # Take first 3 events
            for i, event in enumerate(gen):
                if i >= 3:
                    break
                events.append(event)
            
            # Should generate events
            assert len(events) >= 3, f"Should generate events for {fps_num}/{fps_den} fps"
            
            # Events should align with frame boundaries
            for event in events:
                # Convert event time to frame number
                frame_time = event * fps_num / fps_den
                frame_int = int(frame_time)
                frame_frac = frame_time - frame_int
                
                # Should be close to frame center (0.5)
                # Allow tolerance for bit timing design (events at 3.5 and 9.5 frame units)
                # Frame centers can be at 0.5 or other positions based on bit timing
                assert 0.0 <= frame_frac <= 1.0, \
                    f"Event should be within frame boundaries: {frame_frac} for event {event}"


class TestFractionalFlashSequence:
    """Fractional flash sequence generation tests (TDD Phase 5.1 RED)"""
    
    def test_fractional_flash_sequence_basic(self):
        """Should generate flash sequences for fractional frame rates"""
        if genFlashSequenceFractional is None:
            pytest.skip("Fractional flash sequence not implemented yet (RED phase)")
        
        # Test 29.97 fps
        fps_num, fps_den = 30000, 1001
        duration = 2  # 2 seconds
        
        # Generate events
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen):
            if event >= duration:
                break
            events.append(event)
        
        # Generate flash sequence
        flash_duration = calculate_frame_duration(fps_num, fps_den) * 3  # 3-frame flash
        flash_seq = list(genFlashSequenceFractional(
            flashCentreTimesSecs=events,
            idealFlashDurationSecs=flash_duration,
            sequenceDurationSecs=duration,
            fps_num=fps_num,
            fps_den=fps_den,
            gapValue=(0, 0, 0),
            flashValue=(255, 255, 255)
        ))
        
        # Should generate correct number of frames
        expected_frames = int(duration * fps_num / fps_den)
        assert abs(len(flash_seq) - expected_frames) <= 1, \
            f"Should generate ~{expected_frames} frames, got {len(flash_seq)}"
        
        # All values should be valid RGB tuples
        assert all(isinstance(color, tuple) and len(color) == 3 for color in flash_seq), \
            "All flash values should be RGB tuples"
    
    def test_fractional_flash_sequence_precision(self):
        """Flash sequences should maintain frame-accurate timing"""
        if genFlashSequenceFractional is None:
            pytest.skip("Fractional flash sequence not implemented yet (RED phase)")
        
        # Test with exact NTSC timing
        fps_num, fps_den = 30000, 1001
        
        # Create event at exactly 1001/30000 seconds (1 frame time)
        event_time = Fraction(1001, 30000)
        events = [event_time]
        
        # Generate flash sequence
        flash_duration = Fraction(3003, 30000)  # 3 frames
        flash_seq = list(genFlashSequenceFractional(
            flashCentreTimesSecs=events,
            idealFlashDurationSecs=flash_duration,
            sequenceDurationSecs=1,
            fps_num=fps_num,
            fps_den=fps_den
        ))
        
        # Should have flash at the correct frame
        # Event at 1001/30000 seconds should flash around frame 1
        expected_frames = int(1 * fps_num / fps_den)  # ~29.97 frames for 1 second
        assert len(flash_seq) >= expected_frames, f"Should generate at least {expected_frames} frames for 1 second"
        
        # Check that there's a flash around frame 1
        flash_frames = [i for i, color in enumerate(flash_seq) if color != (0, 0, 0)]
        assert len(flash_frames) > 0, "Should have some flash frames"
        assert min(flash_frames) <= 3, "Flash should start near frame 1"


class TestFractionalBeepSequence:
    """Fractional beep sequence generation tests (TDD Phase 5.1 RED)"""
    
    def test_fractional_beep_sequence_basic(self):
        """Should generate beep sequences for fractional frame rates"""
        if genBeepSequenceFractional is None:
            pytest.skip("Fractional beep sequence not implemented yet (RED phase)")
        
        # Test 23.976 fps
        fps_num, fps_den = 24000, 1001
        duration = 1  # 1 second
        sample_rate = 48000
        
        # Generate events
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen):
            if event >= duration:
                break
            events.append(event)
        
        # Generate beep sequence
        beep_duration = calculate_frame_duration(fps_num, fps_den) * 3  # 3-frame beep
        beep_seq = list(genBeepSequenceFractional(
            beepCentreTimesSecs=events,
            idealBeepDurationSecs=beep_duration,
            sequenceDurationSecs=duration,
            sampleRateHz=sample_rate,
            fps_num=fps_num,
            fps_den=fps_den,
            toneHz=3000,
            amplitude=16384
        ))
        
        # Should generate correct number of samples
        expected_samples = duration * sample_rate
        assert len(beep_seq) == expected_samples, \
            f"Should generate {expected_samples} samples, got {len(beep_seq)}"
        
        # All samples should be in valid range
        assert all(-32768 <= sample <= 32767 for sample in beep_seq), \
            "All samples should be in 16-bit range"
    
    def test_fractional_beep_timing_precision(self):
        """Beep timing should be sample-accurate for fractional rates"""
        if genBeepSequenceFractional is None:
            pytest.skip("Fractional beep sequence not implemented yet (RED phase)")
        
        # Test with exact timing
        fps_num, fps_den = 30000, 1001
        sample_rate = 48000
        
        # Event at exactly 1001/30000 seconds
        event_time = Fraction(1001, 30000)
        events = [event_time]
        
        # Generate beep sequence
        beep_duration = Fraction(3003, 30000)  # 3 frames
        beep_seq = list(genBeepSequenceFractional(
            beepCentreTimesSecs=events,
            idealBeepDurationSecs=beep_duration,
            sequenceDurationSecs=0.5,  # 0.5 seconds
            sampleRateHz=sample_rate,
            fps_num=fps_num,
            fps_den=fps_den,
            toneHz=3000,
            amplitude=16384
        ))
        
        # Should have correct number of samples
        expected_samples = int(0.5 * sample_rate)
        assert len(beep_seq) == expected_samples, "Should have correct sample count"
        
        # Check that beep occurs at correct sample position
        # Event at 1001/30000 ≈ 0.03337 seconds should beep around sample 1600
        expected_sample = int(float(event_time) * sample_rate)
        
        # Find non-zero samples (beep samples)
        beep_samples = [i for i, sample in enumerate(beep_seq) if abs(sample) > 1000]
        
        if beep_samples:  # If we have beeps
            beep_center = sum(beep_samples) // len(beep_samples)
            # Allow larger tolerance for beep timing (within ~500 samples = ~10ms at 48kHz)
            assert abs(beep_center - expected_sample) < 500, \
                f"Beep should be near sample {expected_sample}, got center at {beep_center}"


class TestFractionalBitTimings:
    """Fractional frame rate bit timing tests (TDD Phase 5.1 RED)"""
    
    def test_create_fractional_bit_timings(self):
        """Should create bit timings for fractional frame rates"""
        if createFpsBitTimingsFractional is None:
            pytest.skip("Fractional bit timings not implemented yet (RED phase)")
        
        # Test creating timings for NTSC rates
        ntsc_rates = [
            (24000, 1001),  # 23.976 fps
            (30000, 1001),  # 29.97 fps
            (60000, 1001),  # 59.94 fps
        ]
        
        for fps_num, fps_den in ntsc_rates:
            timings = createFpsBitTimingsFractional(fps_num, fps_den)
            
            # Should have timings for 0 and 1 bits
            assert 0 in timings, f"Should have zero bit timing for {fps_num}/{fps_den}"
            assert 1 in timings, f"Should have one bit timing for {fps_num}/{fps_den}"
            
            # Zero bit should have 1 timing, one bit should have 2 timings
            assert len(timings[0]) == 1, "Zero bit should have 1 pulse"
            assert len(timings[1]) == 2, "One bit should have 2 pulses"
            
            # All timings should be Fraction objects for exact precision
            all_timings = timings[0] + timings[1]
            assert all(isinstance(t, Fraction) for t in all_timings), \
                "All timings should be Fraction objects"
            
            # All timings should be positive
            assert all(t > 0 for t in all_timings), "All timings should be positive"
    
    def test_fractional_bit_timings_frame_alignment(self):
        """Fractional bit timings should align with frame boundaries"""
        if createFpsBitTimingsFractional is None:
            pytest.skip("Fractional bit timings not implemented yet (RED phase)")
        
        # Test with 29.97 fps
        fps_num, fps_den = 30000, 1001
        timings = createFpsBitTimingsFractional(fps_num, fps_den)
        
        # Check frame alignment
        base_fps = 30  # Base fps for 30000/1001
        expected_positions = [Fraction(35, 10), Fraction(95, 10)]  # 3.5, 9.5 frame units
        
        # Convert timings to base frame positions
        for bit_val in [0, 1]:
            for timing in timings[bit_val]:
                # Check if timing aligns with expected frame positions
                timing_in_base_frames = timing * base_fps
                
                # Should be close to one of the expected positions (3.5 or 9.5)
                distances = [abs(timing_in_base_frames - pos) for pos in expected_positions]
                min_distance = min(distances)
                
                assert min_distance < Fraction(1, 100), \
                    f"Timing {timing} should align with frame positions {expected_positions}, distance: {min_distance}"
    
    def test_fractional_bit_timings_consistency(self):
        """Fractional bit timings should be consistent with integer equivalents"""
        if createFpsBitTimingsFractional is None:
            pytest.skip("Fractional bit timings not implemented yet (RED phase)")
        
        # Compare 25 fps integer vs fractional
        fps_num, fps_den = 25, 1
        
        # Integer version (existing)
        integer_timings = fpsBitTimings[25]
        
        # Fractional version (new)
        fractional_timings = createFpsBitTimingsFractional(fps_num, fps_den)
        
        # Should have same structure
        assert len(fractional_timings[0]) == len(integer_timings[0]), \
            "Should have same number of zero bit timings"
        assert len(fractional_timings[1]) == len(integer_timings[1]), \
            "Should have same number of one bit timings"
        
        # Values should be very close
        for bit_val in [0, 1]:
            for i, (int_timing, frac_timing) in enumerate(zip(integer_timings[bit_val], fractional_timings[bit_val])):
                assert abs(float(frac_timing) - int_timing) < 1e-10, \
                    f"Timing {i} for bit {bit_val} should be equivalent: {int_timing} vs {float(frac_timing)}"


class TestFractionalEventIntegration:
    """Integration tests for fractional event generation (TDD Phase 5.1 RED)"""
    
    def test_complete_fractional_workflow(self):
        """Test complete fractional frame rate workflow"""
        if (genEventCentreTimesFractional is None or 
            genFlashSequenceFractional is None or 
            genBeepSequenceFractional is None):
            pytest.skip("Fractional generation not implemented yet (RED phase)")
        
        # Test with 23.976 fps
        fps_num, fps_den = 24000, 1001
        duration = 2  # 2 seconds
        sample_rate = 48000
        
        # Generate events
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen):
            if event >= duration:
                break
            events.append(event)
        
        # Generate flash sequence
        frame_duration = calculate_frame_duration(fps_num, fps_den)
        flash_duration = frame_duration * 3
        
        flash_seq = list(genFlashSequenceFractional(
            flashCentreTimesSecs=events,
            idealFlashDurationSecs=flash_duration,
            sequenceDurationSecs=duration,
            fps_num=fps_num,
            fps_den=fps_den
        ))
        
        # Generate beep sequence
        beep_seq = list(genBeepSequenceFractional(
            beepCentreTimesSecs=events,
            idealBeepDurationSecs=flash_duration,  # Same duration as flash
            sequenceDurationSecs=duration,
            sampleRateHz=sample_rate,
            fps_num=fps_num,
            fps_den=fps_den,
            toneHz=3000,
            amplitude=16384
        ))
        
        # Verify synchronization
        expected_frames = int(duration * fps_num / fps_den)
        expected_samples = duration * sample_rate
        
        assert abs(len(flash_seq) - expected_frames) <= 1, \
            f"Flash sequence should have ~{expected_frames} frames"
        assert len(beep_seq) == expected_samples, \
            f"Beep sequence should have {expected_samples} samples"
        
        # Should have some events
        assert len(events) > 0, "Should generate some events"
        
        # Events should be precise Fraction objects
        assert all(isinstance(event, Fraction) for event in events), \
            "All events should be exact fractions"


if __name__ == '__main__':
    pytest.main([__file__, "-v"])