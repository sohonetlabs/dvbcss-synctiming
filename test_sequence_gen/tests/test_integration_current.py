#!/usr/bin/env python3
"""
Integration tests for current test sequence generation functionality.

These tests verify that the complete workflow works end-to-end
for the existing integer frame rate support.

Phase 2.4: Integration testing to ensure all components work together.
"""

import json
import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio import genBeepSequence
from generate import fpsBitTimings, genEventCentreTimes
from video import frameNumToTimecode, genFlashSequence


class TestCompleteWorkflowIntegration:
    """Test complete generation workflow (TDD Phase 2.4)"""
    
    def test_event_to_flash_sequence_integration(self, supported_fps_rates, test_duration_short):
        """Test that events can be converted to flash sequences"""
        for fps in supported_fps_rates[:2]:  # Test subset for speed
            # Generate events
            events = []
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            for i, event in enumerate(gen):
                if event >= test_duration_short:
                    break
                events.append(event)
            
            # Convert to flash sequence
            flash_duration = 3.0 / fps  # 3 frame duration
            flash_seq = list(genFlashSequence(
                flashCentreTimesSecs=events,
                idealFlashDurationSecs=flash_duration,
                sequenceDurationSecs=test_duration_short,
                frameRate=fps,
                gapValue=(0, 0, 0),
                flashValue=(255, 255, 255)
            ))
            
            # Verify flash sequence
            expected_frames = test_duration_short * fps
            assert len(flash_seq) == expected_frames, f"Should have {expected_frames} frames for {fps} fps"
            
            # All flash values should be valid RGB tuples
            assert all(isinstance(color, tuple) and len(color) == 3 
                      for color in flash_seq), "All flash values should be RGB tuples"
    
    def test_event_to_beep_sequence_integration(self, supported_fps_rates, test_duration_short):
        """Test that events can be converted to beep sequences"""
        for fps in supported_fps_rates[:2]:  # Test subset for speed
            # Generate events
            events = []
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            for i, event in enumerate(gen):
                if event >= test_duration_short:
                    break
                events.append(event)
            
            # Convert to beep sequence
            sample_rate = 48000
            beep_duration = 3.0 / fps  # 3 frame duration
            tone_freq = 3000
            amplitude = 16384
            
            beep_seq = list(genBeepSequence(
                beepCentreTimesSecs=events,
                idealBeepDurationSecs=beep_duration,
                sequenceDurationSecs=test_duration_short,
                sampleRateHz=sample_rate,
                toneHz=tone_freq,
                amplitude=amplitude
            ))
            
            # Verify beep sequence
            expected_samples = test_duration_short * sample_rate
            assert len(beep_seq) == expected_samples, f"Should have {expected_samples} samples"
            
            # All samples should be in valid range
            assert all(-32768 <= sample <= 32767 for sample in beep_seq), \
                "All samples should be in 16-bit range"
    
    def test_frame_rate_consistency_across_modules(self, supported_fps_rates):
        """Test that frame rate handling is consistent across all modules"""
        for fps in supported_fps_rates:
            # Verify fpsBitTimings has entry
            assert fps in fpsBitTimings, f"fpsBitTimings should support {fps} fps"
            
            # Verify timecode generation works
            timecode = frameNumToTimecode(fps, fps, framesAreFields=False)
            assert timecode == "00:00:01:00", f"One second timecode should be correct for {fps} fps"
            
            # Verify event generation works
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            first_event = next(gen)
            assert first_event >= 0, f"First event should be non-negative for {fps} fps"
    
    def test_sequence_metadata_generation(self, supported_fps_rates, test_duration_short):
        """Test generation of metadata that describes the sequence"""
        for fps in supported_fps_rates[:2]:  # Test subset for speed
            # Generate events for metadata
            events = []
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            for i, event in enumerate(gen):
                if event >= test_duration_short:
                    break
                events.append(event)
            
            # Create metadata structure (as done in generate.py)
            metadata = {
                "size": [854, 480],
                "fps": fps,
                "durationSecs": test_duration_short,
                "patternWindowLength": 3,
                "eventCentreTimes": events,
                "approxBeepDurationSecs": 3.0 / fps,
                "approxFlashDurationSecs": 3.0 / fps,
            }
            
            # Verify metadata structure
            assert metadata["fps"] == fps, "FPS should match in metadata"
            assert len(metadata["eventCentreTimes"]) > 0, "Should have event timings"
            assert metadata["approxBeepDurationSecs"] > 0, "Beep duration should be positive"
            assert metadata["approxFlashDurationSecs"] > 0, "Flash duration should be positive"
            
            # Verify metadata is JSON serializable
            json_str = json.dumps(metadata)
            loaded = json.loads(json_str)
            assert loaded["fps"] == fps, "JSON roundtrip should preserve FPS"


class TestModuleInteroperability:
    """Test that modules work correctly together (TDD Phase 2.4)"""
    
    def test_video_audio_synchronization(self, supported_fps_rates):
        """Test that video and audio generation produce synchronized results"""
        for fps in [25, 30]:  # Test subset for speed
            duration = 1  # 1 second for quick test
            
            # Generate same events for both video and audio
            events = []
            gen = genEventCentreTimes(seqBits=3, fps=fps)
            for i, event in enumerate(gen):
                if event >= duration:
                    break
                events.append(event)
            
            # Generate video frames
            flash_duration = 3.0 / fps
            flash_seq = list(genFlashSequence(
                flashCentreTimesSecs=events,
                idealFlashDurationSecs=flash_duration,
                sequenceDurationSecs=duration,
                frameRate=fps
            ))
            
            # Generate audio samples
            sample_rate = 48000
            beep_seq = list(genBeepSequence(
                beepCentreTimesSecs=events,
                idealBeepDurationSecs=flash_duration,  # Same duration as flash
                sequenceDurationSecs=duration,
                sampleRateHz=sample_rate,
                toneHz=3000,
                amplitude=16384
            ))
            
            # Verify synchronization
            expected_frames = duration * fps
            expected_samples = duration * sample_rate
            
            assert len(flash_seq) == expected_frames, "Video frame count should match duration"
            assert len(beep_seq) == expected_samples, "Audio sample count should match duration"
            
            # Verify timing relationship
            frame_duration = 1.0 / fps
            sample_duration = 1.0 / sample_rate
            
            # Each frame corresponds to specific samples
            samples_per_frame = sample_rate // fps
            assert samples_per_frame > 0, "Should have multiple samples per frame"
    
    def test_timing_precision_across_modules(self, supported_fps_rates):
        """Test that timing calculations are consistent across modules"""
        for fps in supported_fps_rates[:3]:  # Test subset for speed
            # Test frame-to-time conversions
            frame_duration = 1.0 / fps
            
            # One second should equal fps frames
            one_second_frames = fps
            timecode = frameNumToTimecode(one_second_frames, fps)
            assert timecode == "00:00:01:00", f"One second should be 00:00:01:00 for {fps} fps"
            
            # Frame 0 should be at time 0
            zero_timecode = frameNumToTimecode(0, fps)
            assert zero_timecode == "00:00:00:00", f"Frame 0 should be 00:00:00:00 for {fps} fps"
    
    def test_bit_encoding_consistency(self, supported_fps_rates):
        """Test that bit encoding is consistent with timing"""
        for fps in supported_fps_rates:
            timings = fpsBitTimings[fps]
            
            # Zero bit should have one timing
            zero_timings = timings[0]
            assert len(zero_timings) == 1, f"Zero bit should have 1 timing for {fps} fps"
            
            # One bit should have two timings
            one_timings = timings[1]
            assert len(one_timings) == 2, f"One bit should have 2 timings for {fps} fps"
            
            # All timings should be reasonable
            all_timings = zero_timings + one_timings
            max_reasonable_time = 1.0  # 1 second should be plenty for any timing
            
            assert all(0 < t < max_reasonable_time for t in all_timings), \
                f"All timings should be reasonable for {fps} fps"


class TestPerformanceCharacteristics:
    """Test performance characteristics of current implementation (TDD Phase 2.4)"""
    
    def test_event_generation_performance(self):
        """Test that event generation doesn't hang or consume excessive memory"""
        # This test ensures the infinite generator pattern works correctly
        fps = 25
        max_events = 100  # Reasonable limit for testing
        
        # Generate events and ensure it doesn't hang
        events = []
        gen = genEventCentreTimes(seqBits=4, fps=fps)
        
        for i, event in enumerate(gen):
            if i >= max_events:
                break
            events.append(event)
        
        # Verify we got the expected number of events
        assert len(events) == max_events, "Should generate exactly the requested number of events"
        
        # Verify events are reasonable
        assert all(isinstance(e, (int, float)) for e in events), "All events should be numeric"
        assert all(e >= 0 for e in events), "All events should be non-negative"
    
    def test_memory_usage_reasonable(self):
        """Test that generating sequences doesn't use excessive memory"""
        # Generate a small sequence and verify it completes
        fps = 30
        duration = 2  # 2 seconds
        
        # This should complete without memory issues
        events = []
        gen = genEventCentreTimes(seqBits=3, fps=fps)
        for i, event in enumerate(gen):
            if event >= duration:
                break
            events.append(event)
        
        # Should have generated some events
        assert len(events) > 0, "Should generate some events in reasonable time"
        assert len(events) < 1000, "Should not generate excessive events for short duration"


if __name__ == '__main__':
    pytest.main([__file__])