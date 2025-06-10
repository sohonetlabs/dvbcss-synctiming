#!/usr/bin/env python3
"""
End-to-End Integration Tests - Phase 7.1: Complete Workflow Testing

This module tests the complete fractional frame rate test sequence generation
workflow from CLI parsing through to output generation.

Phase 7.1: End-to-End Integration Tests
- Complete workflow tests with fractional frame rates
- Output file verification (audio, video, metadata)
- Backward compatibility verification
- Performance testing
"""

import sys
import os
import pytest
import json
import tempfile
import subprocess
from pathlib import Path
from fractions import Fraction
import wave
from PIL import Image

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import modules
from generate_fractional import generate_fractional_test_sequence
from cli_fractional_integration import parse_fractional_args
from frame_timing import frame_to_seconds


class TestEndToEndIntegration:
    """Complete workflow integration tests"""
    
    def test_basic_fractional_generation(self):
        """Test basic fractional frame rate generation workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with 29.97 fps
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),
                size=(640, 480),
                duration_secs=2,
                window_len=3,
                sample_rate=48000,
                title_text="Test 29.97 fps",
                output_audio=True,
                output_video=True,
                output_metadata=True,
                audio_filename=os.path.join(tmpdir, "test.wav"),
                frame_filename_pattern=os.path.join(tmpdir, "frame_%06d.png"),
                metadata_filename=os.path.join(tmpdir, "metadata.json")
            )
            
            # Verify result
            assert result['success'] is True
            assert result['fps_rational'] == (30000, 1001)
            assert result['size'] == (640, 480)
            assert result['event_count'] > 0
            assert result['frame_count'] > 0
            assert result['sample_count'] > 0
            
            # Verify files were created
            assert os.path.exists(os.path.join(tmpdir, "test.wav"))
            assert os.path.exists(os.path.join(tmpdir, "metadata.json"))
            assert os.path.exists(os.path.join(tmpdir, "frame_000000.png"))
    
    def test_ntsc_film_rate_generation(self):
        """Test 23.976 fps (NTSC film) generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_fractional_test_sequence(
                fps_rational=(24000, 1001),
                size=(1920, 1080),
                duration_secs=3,
                window_len=4,
                sample_rate=48000,
                title_text="NTSC Film Test",
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "metadata.json")
            )
            
            assert result['success'] is True
            assert result['fps_rational'] == (24000, 1001)
            
            # Check metadata
            with open(os.path.join(tmpdir, "metadata.json"), 'r') as f:
                metadata = json.load(f)
            
            assert metadata['fps_rational']['num'] == 24000
            assert metadata['fps_rational']['den'] == 1001
            assert abs(metadata['fps'] - 23.976023976) < 0.000001
            assert metadata['timing_precision'] == 'exact_rational'
    
    def test_field_based_generation(self):
        """Test field-based output for interlaced formats"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),  # 29.97 fps
                size=(1920, 1080),
                duration_secs=1,
                window_len=3,
                field_based=True,
                output_video=True,
                frame_filename_pattern=os.path.join(tmpdir, "field_%06d.png")
            )
            
            assert result['success'] is True
            # Should generate twice as many frames for field-based
            expected_frames = int(1 * 30000 / 1001) * 2  # ~60 fields for 1 second
            assert abs(result['frame_count'] - expected_frames) <= 2
    
    def test_cli_to_generation_workflow(self):
        """Test complete workflow from CLI parsing to generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Parse CLI arguments
            cli_args = [
                "--fps-ntsc-film",  # 23.976 fps
                "--size-4k-full",   # 4096x2160
                "--duration", "2",
                "--window-len", "4",
                "--title", "CLI Integration Test"
            ]
            
            args = parse_fractional_args(cli_args)
            
            # Generate test sequence using parsed arguments
            result = generate_fractional_test_sequence(
                fps_rational=args.fps_rational,
                size=args.size,
                duration_secs=args.DURATION,
                window_len=args.WINDOW_LEN,
                title_text=args.TITLE_TEXT,
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "cli_test.json")
            )
            
            assert result['success'] is True
            assert result['fps_rational'] == (24000, 1001)
            assert result['size'] == (4096, 2160)
            
            # Verify metadata
            with open(os.path.join(tmpdir, "cli_test.json"), 'r') as f:
                metadata = json.load(f)
            
            assert metadata['size'] == [4096, 2160]
            assert metadata['fps_rational']['num'] == 24000
            assert metadata['fps_rational']['den'] == 1001
    
    def test_format_preset_workflow(self):
        """Test complete format preset workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Parse preset arguments
            cli_args = [
                "--preset-1080p59.94",  # Complete preset
                "--duration", "1",
                "--window-len", "3"
            ]
            
            args = parse_fractional_args(cli_args)
            
            # Generate test sequence
            result = generate_fractional_test_sequence(
                fps_rational=args.fps_rational,
                size=args.size,
                duration_secs=args.DURATION,
                window_len=args.WINDOW_LEN,
                output_audio=True,
                output_video=True,
                audio_filename=os.path.join(tmpdir, "preset.wav"),
                frame_filename_pattern=os.path.join(tmpdir, "preset_%04d.png")
            )
            
            assert result['success'] is True
            assert result['fps_rational'] == (60000, 1001)  # 59.94 fps
            assert result['size'] == (1920, 1080)
            
            # Should generate ~60 frames for 1 second at 59.94 fps
            assert 58 <= result['frame_count'] <= 62
    
    def test_audio_video_sync(self):
        """Test that audio and video are properly synchronized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate with known event times
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),
                size=(640, 480),
                duration_secs=2,
                window_len=3,
                sample_rate=48000,
                output_audio=True,
                output_video=True,
                output_metadata=True,
                audio_filename=os.path.join(tmpdir, "sync.wav"),
                frame_filename_pattern=os.path.join(tmpdir, "sync_%06d.png"),
                metadata_filename=os.path.join(tmpdir, "sync.json")
            )
            
            # Load metadata to check event times
            with open(os.path.join(tmpdir, "sync.json"), 'r') as f:
                metadata = json.load(f)
            
            event_times = metadata['eventCentreTimes']
            assert len(event_times) > 0
            
            # Check that events are frame-aligned
            fps_num = metadata['fps_rational']['num']
            fps_den = metadata['fps_rational']['den']
            
            for event_time in event_times:
                # Calculate which frame this event should occur in
                frame_num = event_time * fps_num / fps_den
                # Should be near a frame boundary (within tolerance)
                assert abs(frame_num - round(frame_num)) < 0.1
    
    def test_pattern_window_accuracy(self):
        """Test that pattern window length is respected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            window_len = 4  # Pattern repeats every 2^4 - 1 = 15 seconds
            
            result = generate_fractional_test_sequence(
                fps_rational=(25, 1),  # Simple 25 fps
                size=(640, 480),
                duration_secs=20,  # Longer than pattern
                window_len=window_len,
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "pattern.json")
            )
            
            assert result['success'] is True
            
            # Check metadata
            with open(os.path.join(tmpdir, "pattern.json"), 'r') as f:
                metadata = json.load(f)
            
            assert metadata['patternWindowLength'] == window_len
            assert metadata['pattern_repeat_time'] == 2**window_len - 1  # 15 seconds
            
            # Duration should be adjusted to exact multiple of pattern
            assert metadata['adjusted_duration'] % (2**window_len - 1) == 0
    
    def test_high_frame_rate_generation(self):
        """Test generation at high frame rates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test 119.88 fps (120000/1001)
            result = generate_fractional_test_sequence(
                fps_rational=(120000, 1001),
                size=(1280, 720),
                duration_secs=1,
                window_len=3,
                output_video=True,
                frame_filename_pattern=os.path.join(tmpdir, "hfr_%06d.png")
            )
            
            assert result['success'] is True
            # Should generate ~120 frames for 1 second
            assert 118 <= result['frame_count'] <= 122
    
    def test_exact_timing_preservation(self):
        """Test that exact rational timing is preserved throughout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a fractional rate with known precision requirements
            fps_num, fps_den = 24000, 1001
            
            result = generate_fractional_test_sequence(
                fps_rational=(fps_num, fps_den),
                size=(640, 480),
                duration_secs=5,
                window_len=4,
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "timing.json")
            )
            
            # Load metadata
            with open(os.path.join(tmpdir, "timing.json"), 'r') as f:
                metadata = json.load(f)
            
            # Check frame duration exactness
            frame_duration_exact = metadata['frame_duration_exact']
            assert frame_duration_exact['num'] == 1001
            assert frame_duration_exact['den'] == 24000
            
            # Verify it matches expected value
            expected_duration = Fraction(1001, 24000)
            actual_duration = Fraction(frame_duration_exact['num'], frame_duration_exact['den'])
            assert actual_duration == expected_duration


class TestOutputFileValidation:
    """Tests that validate the actual output files"""
    
    def test_wav_file_format(self):
        """Test that generated WAV files are valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = os.path.join(tmpdir, "test.wav")
            
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),
                size=(640, 480),
                duration_secs=1,
                window_len=3,
                sample_rate=48000,
                output_audio=True,
                audio_filename=audio_file
            )
            
            assert result['success'] is True
            assert os.path.exists(audio_file)
            
            # Validate WAV file
            with wave.open(audio_file, 'rb') as wav:
                assert wav.getnchannels() == 1  # Mono
                assert wav.getsampwidth() == 2  # 16-bit
                assert wav.getframerate() == 48000
                assert wav.getnframes() == result['sample_count']
    
    def test_png_file_format(self):
        """Test that generated PNG files are valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_pattern = os.path.join(tmpdir, "frame_%03d.png")
            
            result = generate_fractional_test_sequence(
                fps_rational=(25, 1),
                size=(854, 480),
                duration_secs=0.5,  # Short duration for quick test
                window_len=3,
                output_video=True,
                frame_filename_pattern=frame_pattern
            )
            
            assert result['success'] is True
            
            # Check first frame
            first_frame = os.path.join(tmpdir, "frame_000.png")
            assert os.path.exists(first_frame)
            
            # Validate PNG
            with Image.open(first_frame) as img:
                assert img.size == (854, 480)
                assert img.mode == 'RGB'
    
    def test_metadata_json_structure(self):
        """Test that metadata JSON has all required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_file = os.path.join(tmpdir, "metadata.json")
            
            result = generate_fractional_test_sequence(
                fps_rational=(60000, 1001),
                size=(1920, 1080),
                duration_secs=3,
                window_len=4,
                sample_rate=96000,
                title_text="Metadata Test",
                output_metadata=True,
                metadata_filename=metadata_file
            )
            
            assert result['success'] is True
            assert os.path.exists(metadata_file)
            
            # Load and validate metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check all required fields exist
            required_fields = [
                'size', 'fps', 'fps_rational', 'durationSecs',
                'patternWindowLength', 'eventCentreTimes',
                'approxBeepDurationSecs', 'approxFlashDurationSecs',
                'frame_duration_exact', 'timing_precision',
                'sample_rate', 'title', 'total_frames', 'total_audio_samples'
            ]
            
            for field in required_fields:
                assert field in metadata, f"Missing required field: {field}"
            
            # Validate specific values
            assert metadata['fps_rational']['num'] == 60000
            assert metadata['fps_rational']['den'] == 1001
            assert metadata['size'] == [1920, 1080]
            assert metadata['sample_rate'] == 96000
            assert metadata['title'] == "Metadata Test"
            assert metadata['timing_precision'] == 'exact_rational'


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing tools"""
    
    def test_integer_frame_rate_compatibility(self):
        """Test that integer frame rates work identically to original"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with traditional integer frame rate
            result = generate_fractional_test_sequence(
                fps_rational=(50, 1),  # 50 fps
                size=(1920, 1080),
                duration_secs=2,
                window_len=4,
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "integer.json")
            )
            
            assert result['success'] is True
            
            # Check metadata compatibility
            with open(os.path.join(tmpdir, "integer.json"), 'r') as f:
                metadata = json.load(f)
            
            # Should have decimal fps for compatibility
            assert metadata['fps'] == 50.0
            assert isinstance(metadata['fps'], (int, float))
            
            # Should also have new fractional fields
            assert metadata['fps_rational']['num'] == 50
            assert metadata['fps_rational']['den'] == 1
    
    def test_metadata_backward_compatibility_fields(self):
        """Test that all original metadata fields are present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),
                size=(1280, 720),
                duration_secs=1,
                window_len=3,
                output_metadata=True,
                metadata_filename=os.path.join(tmpdir, "compat.json")
            )
            
            with open(os.path.join(tmpdir, "compat.json"), 'r') as f:
                metadata = json.load(f)
            
            # Original fields that must be present
            original_fields = [
                'size',  # [width, height] array
                'fps',   # Decimal fps
                'durationSecs',
                'patternWindowLength',
                'eventCentreTimes',  # Array of floats
                'approxBeepDurationSecs',
                'approxFlashDurationSecs'
            ]
            
            for field in original_fields:
                assert field in metadata, f"Missing original field: {field}"
                
            # Verify format matches original
            assert isinstance(metadata['size'], list)
            assert len(metadata['size']) == 2
            assert isinstance(metadata['fps'], (int, float))
            assert isinstance(metadata['eventCentreTimes'], list)
            assert all(isinstance(t, (int, float)) for t in metadata['eventCentreTimes'])


class TestPerformance:
    """Basic performance tests"""
    
    def test_generation_performance(self):
        """Test that generation completes in reasonable time"""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            start_time = time.time()
            
            result = generate_fractional_test_sequence(
                fps_rational=(30000, 1001),
                size=(1920, 1080),
                duration_secs=10,  # 10 second sequence
                window_len=5,
                output_audio=True,
                output_video=False,  # Skip video for performance test
                output_metadata=True,
                audio_filename=os.path.join(tmpdir, "perf.wav"),
                metadata_filename=os.path.join(tmpdir, "perf.json")
            )
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            assert result['success'] is True
            # Should complete in reasonable time (< 5 seconds for 10 second audio)
            assert generation_time < 5.0, f"Generation took too long: {generation_time:.2f}s"
            
            print(f"Generated 10 second sequence in {generation_time:.2f}s")


if __name__ == '__main__':
    pytest.main([__file__, "-v"])