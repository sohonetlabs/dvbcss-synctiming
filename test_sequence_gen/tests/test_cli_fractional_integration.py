#!/usr/bin/env python3
"""
CLI Integration Tests for Fractional Frame Rates - Phase 6.1: RED → GREEN → REFACTOR

This module implements TDD for CLI integration with fractional frame rate support.
Tests command-line parsing, broadcast shortcuts, and complete workflow integration.

Phase 6.1: CLI Integration Tests for Fractional Rates  
- RED: Write failing tests for CLI fractional frame rate support
- GREEN: Implement CLI enhancements to make tests pass
- REFACTOR: Clean up and optimize CLI integration

Key functionality to test:
- --fps fractional parsing: "23.976", "24000/1001"
- Broadcast shortcuts: --fps-ntsc-film, --fps-ntsc, --fps-pal
- Resolution shortcuts: --size-4k-full, --size-hd-1080  
- Complete presets: --preset-1080p59.94, --preset-cinema-4k
- Integration with existing generate.py workflow
"""

import json
import os
import sys

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import current modules

# Import will fail initially - that's part of RED phase
try:
    from cli_fractional_integration import (
        create_fractional_metadata,
        get_format_preset,
        get_resolution_preset,
        parse_fractional_args,
    )
except ImportError:
    # Expected during RED phase - CLI integration module doesn't exist yet
    parse_fractional_args = None
    create_fractional_metadata = None
    get_resolution_preset = None
    get_format_preset = None


class TestFractionalCLIParsing:
    """Basic CLI parsing tests for fractional frame rates (TDD Phase 6.1 RED)"""
    
    def test_fractional_fps_argument_parsing(self):
        """Should parse fractional fps arguments"""
        if parse_fractional_args is None:
            pytest.skip("CLI fractional integration not implemented yet (RED phase)")
        
        test_cases = [
            # Decimal format
            (["--fps", "23.976"], (24000, 1001)),
            (["--fps", "29.97"], (30000, 1001)),
            (["--fps", "59.94"], (60000, 1001)),
            
            # Rational format  
            (["--fps", "24000/1001"], (24000, 1001)),
            (["--fps", "30000/1001"], (30000, 1001)),
            
            # Integer format (backward compatibility)
            (["--fps", "25"], (25, 1)),
            (["--fps", "50"], (50, 1)),
        ]
        
        for args, expected_fps in test_cases:
            parsed_args = parse_fractional_args(args + ["--duration", "5"])
            assert hasattr(parsed_args, 'fps_rational'), "Should have fps_rational attribute"
            assert parsed_args.fps_rational == expected_fps, \
                f"Args {args} should parse to {expected_fps}, got {parsed_args.fps_rational}"
    
    def test_broadcast_standard_shortcuts(self):
        """Should parse broadcast standard shortcuts"""
        if parse_fractional_args is None:
            pytest.skip("CLI fractional integration not implemented yet (RED phase)")
        
        broadcast_cases = [
            # NTSC family
            (["--fps-ntsc-film"], (24000, 1001)),
            (["--fps-ntsc"], (30000, 1001)),
            (["--fps-ntsc-hd"], (60000, 1001)),
            
            # PAL family
            (["--fps-pal"], (25, 1)),
            (["--fps-pal-hd"], (50, 1)),
            
            # Cinema standards
            (["--fps-film"], (24, 1)),
            (["--fps-film-hfr-48"], (48, 1)),
            (["--fps-film-hfr-60"], (60, 1)),
        ]
        
        for args, expected_fps in broadcast_cases:
            parsed_args = parse_fractional_args(args + ["--duration", "5"])
            assert parsed_args.fps_rational == expected_fps, \
                f"Broadcast shortcut {args} should parse to {expected_fps}"
    
    def test_resolution_shortcuts(self):
        """Should parse resolution shortcuts"""
        if get_resolution_preset is None:
            pytest.skip("Resolution presets not implemented yet (RED phase)")
        
        resolution_cases = [
            # TV/Broadcast resolutions
            ("sd-ntsc", (720, 480)),
            ("sd-pal", (720, 576)), 
            ("hd-720", (1280, 720)),
            ("hd-1080", (1920, 1080)),
            ("uhd-4k", (3840, 2160)),
            
            # Cinema resolutions
            ("2k-full", (2048, 1080)),
            ("4k-full", (4096, 2160)),
            ("4k-scope", (4096, 1716)),
        ]
        
        for preset_name, expected_size in resolution_cases:
            size = get_resolution_preset(preset_name)
            assert size == expected_size, \
                f"Resolution preset {preset_name} should be {expected_size}, got {size}"
    
    def test_complete_format_presets(self):
        """Should parse complete format presets combining fps + resolution"""
        if get_format_preset is None:
            pytest.skip("Format presets not implemented yet (RED phase)")
        
        preset_cases = [
            # TV broadcast presets
            ("1080p59.94", (60000, 1001), (1920, 1080)),
            ("1080p25", (25, 1), (1920, 1080)),
            ("720p50", (50, 1), (1280, 720)),
            
            # Cinema presets
            ("cinema-4k", (24, 1), (4096, 2160)),
            ("cinema-4k-hfr", (48, 1), (4096, 2160)),
            ("cinema-2k", (24, 1), (2048, 1080)),
        ]
        
        for preset_name, expected_fps, expected_size in preset_cases:
            fps_rational, size = get_format_preset(preset_name)
            assert fps_rational == expected_fps, \
                f"Preset {preset_name} fps should be {expected_fps}, got {fps_rational}"
            assert size == expected_size, \
                f"Preset {preset_name} size should be {expected_size}, got {size}"


class TestCLIBackwardCompatibility:
    """Test CLI backward compatibility with existing arguments (TDD Phase 6.1 RED)"""
    
    def test_existing_fps_arguments_still_work(self):
        """Existing integer fps arguments should continue to work"""
        if parse_fractional_args is None:
            pytest.skip("CLI fractional integration not implemented yet (RED phase)")
        
        # Test that existing integer fps values work unchanged
        for fps in [24, 25, 30, 48, 50, 60]:
            parsed_args = parse_fractional_args(["--fps", str(fps), "--duration", "5"])
            assert parsed_args.fps_rational == (fps, 1), \
                f"Integer fps {fps} should still work"
    
    def test_existing_arguments_preserved(self):
        """All existing CLI arguments should be preserved"""
        if parse_fractional_args is None:
            pytest.skip("CLI fractional integration not implemented yet (RED phase)")
        
        # Test that we can still parse existing arguments
        test_args = [
            "--fps", "25",
            "--window-len", "7", 
            "--duration", "10",
            "--size", "1920x1080",
            "--sampleRate", "48000",
            "--title", "Test Sequence"
        ]
        
        parsed_args = parse_fractional_args(test_args)
        
        # Should have expected values
        assert parsed_args.fps_rational == (25, 1)
        assert parsed_args.WINDOW_LEN == 7
        assert parsed_args.DURATION == 10
        assert parsed_args.size == (1920, 1080)
        assert parsed_args.SAMPLE_RATE == 48000
        assert parsed_args.TITLE_TEXT == "Test Sequence"
    
    def test_conflicting_fps_arguments_error(self):
        """Should error if both --fps and --fps-* shortcuts are provided"""
        if parse_fractional_args is None:
            pytest.skip("CLI fractional integration not implemented yet (RED phase)")
        
        # Should raise SystemExit for conflicting arguments (argparse behavior)
        with pytest.raises(SystemExit):
            parse_fractional_args(["--fps", "25", "--fps-ntsc", "--duration", "5"])


class TestCLIMetadataGeneration:
    """Test metadata generation for fractional frame rates (TDD Phase 6.1 RED)"""
    
    def test_fractional_metadata_creation(self):
        """Should create metadata with fractional frame rate information"""
        if create_fractional_metadata is None:
            pytest.skip("Fractional metadata not implemented yet (RED phase)")
        
        # Test metadata for 29.97 fps
        fps_rational = (30000, 1001)
        size = (1920, 1080)
        duration = 5
        events = [0.5, 1.0, 2.0]  # Sample events
        
        metadata = create_fractional_metadata(
            fps_rational=fps_rational,
            size=size,
            duration_secs=duration,
            seq_bits=7,
            event_times=events
        )
        
        # Should have fractional fps information
        assert "fps_rational" in metadata, "Metadata should include fps_rational"
        assert metadata["fps_rational"]["num"] == 30000
        assert metadata["fps_rational"]["den"] == 1001
        
        # Should have decimal fps for compatibility
        assert "fps" in metadata, "Metadata should include decimal fps"
        assert abs(metadata["fps"] - 29.970029970) < 0.000001
        
        # Should have exact frame duration
        assert "frame_duration_exact" in metadata
        assert metadata["frame_duration_exact"]["num"] == 1001
        assert metadata["frame_duration_exact"]["den"] == 30000
        
        # Should have all standard fields
        assert metadata["size"] == [1920, 1080]
        assert metadata["durationSecs"] == 5
        assert metadata["patternWindowLength"] == 7
        assert metadata["eventCentreTimes"] == events
    
    def test_metadata_json_serialization(self):
        """Metadata should be JSON serializable"""
        if create_fractional_metadata is None:
            pytest.skip("Fractional metadata not implemented yet (RED phase)")
        
        fps_rational = (24000, 1001)
        metadata = create_fractional_metadata(
            fps_rational=fps_rational,
            size=(4096, 2160),
            duration_secs=10,
            seq_bits=8,
            event_times=[1.0, 2.5, 4.0]
        )
        
        # Should be JSON serializable
        json_str = json.dumps(metadata)
        loaded_metadata = json.loads(json_str)
        
        # Should preserve all data
        assert loaded_metadata["fps_rational"]["num"] == 24000
        assert loaded_metadata["fps_rational"]["den"] == 1001
        assert loaded_metadata["size"] == [4096, 2160]


class TestCLIIntegrationWorkflow:
    """Test complete CLI workflow integration (TDD Phase 6.1 RED)"""
    
    def test_cli_fractional_workflow_simulation(self):
        """Simulate complete CLI workflow with fractional frame rates"""
        if (parse_fractional_args is None or create_fractional_metadata is None):
            pytest.skip("CLI integration not implemented yet (RED phase)")
        
        # Simulate CLI arguments for 23.976 fps cinema workflow
        cli_args = [
            "--fps-ntsc-film",  # 23.976 fps
            "--size-4k-full",   # 4096x2160
            "--duration", "3",
            "--window-len", "7",
            "--title", "Fractional Rate Test"
        ]
        
        # Parse arguments
        parsed_args = parse_fractional_args(cli_args)
        
        # Should have correct fps and size
        assert parsed_args.fps_rational == (24000, 1001)
        assert parsed_args.size == (4096, 2160)
        assert parsed_args.DURATION == 3
        assert parsed_args.WINDOW_LEN == 7
        assert parsed_args.TITLE_TEXT == "Fractional Rate Test"
        
        # Should be able to create metadata
        metadata = create_fractional_metadata(
            fps_rational=parsed_args.fps_rational,
            size=parsed_args.size,
            duration_secs=parsed_args.DURATION,
            seq_bits=parsed_args.WINDOW_LEN,
            event_times=[0.5, 1.0, 2.0]
        )
        
        # Metadata should be complete
        assert metadata["fps_rational"]["num"] == 24000
        assert metadata["fps_rational"]["den"] == 1001
        assert metadata["size"] == [4096, 2160]
        assert metadata["durationSecs"] == 3
    
    def test_cli_preset_workflow(self):
        """Test CLI workflow using complete presets"""
        if parse_fractional_args is None:
            pytest.skip("CLI integration not implemented yet (RED phase)")
        
        # Test with complete preset
        cli_args = [
            "--preset-1080p59.94",  # Complete preset: 1080p @ 59.94 fps
            "--duration", "5",
            "--window-len", "8"
        ]
        
        parsed_args = parse_fractional_args(cli_args)
        
        # Should parse preset correctly
        assert parsed_args.fps_rational == (60000, 1001)
        assert parsed_args.size == (1920, 1080)
        assert parsed_args.DURATION == 5
        assert parsed_args.WINDOW_LEN == 8
    
    def test_cli_help_includes_fractional_options(self):
        """CLI help should include fractional frame rate options"""
        if parse_fractional_args is None:
            pytest.skip("CLI integration not implemented yet (RED phase)")
        
        # Test that help includes new options
        try:
            parsed_args = parse_fractional_args(["--help"])
        except SystemExit:
            # argparse exits on --help, this is expected
            pass
        
        # Test that parser includes fractional options by checking for errors
        # with valid fractional arguments (should not raise)
        parsed_args = parse_fractional_args(["--fps-ntsc", "--duration", "1"])
        assert parsed_args.fps_rational == (30000, 1001)


class TestCLIErrorHandling:
    """Test CLI error handling for fractional frame rates (TDD Phase 6.1 RED)"""
    
    def test_invalid_fractional_fps_error(self):
        """Should provide clear error for invalid fractional fps"""
        if parse_fractional_args is None:
            pytest.skip("CLI integration not implemented yet (RED phase)")
        
        invalid_fps_cases = [
            ["--fps", "invalid"],
            ["--fps", "0"],
            ["--fps", "-25"],
            ["--fps", "1000"],  # Too high
        ]
        
        for args in invalid_fps_cases:
            with pytest.raises(ValueError, match="Frame rate.*out of.*range|Invalid.*frame.*rate"):
                parse_fractional_args(args + ["--duration", "5"])
    
    def test_unknown_broadcast_standard_error(self):
        """Should provide clear error for unknown broadcast standards"""
        if parse_fractional_args is None:
            pytest.skip("CLI integration not implemented yet (RED phase)")
        
        # Test with unknown broadcast standard (argparse will raise SystemExit for unknown args)
        with pytest.raises(SystemExit):
            parse_fractional_args(["--fps-unknown-standard", "--duration", "5"])
    
    def test_unknown_resolution_preset_error(self):
        """Should provide clear error for unknown resolution presets"""
        if get_resolution_preset is None:
            pytest.skip("Resolution presets not implemented yet (RED phase)")
        
        with pytest.raises(ValueError, match="Unknown resolution preset"):
            get_resolution_preset("unknown-resolution")
    
    def test_unknown_format_preset_error(self):
        """Should provide clear error for unknown format presets"""
        if get_format_preset is None:
            pytest.skip("Format presets not implemented yet (RED phase)")
        
        with pytest.raises(ValueError, match="Unknown format preset"):
            get_format_preset("unknown-preset")


class TestCLIOutputCompatibility:
    """Test CLI output compatibility with existing tools (TDD Phase 6.1 RED)"""
    
    def test_fractional_metadata_compatibility(self):
        """Fractional metadata should be compatible with existing analysis tools"""
        if create_fractional_metadata is None:
            pytest.skip("Fractional metadata not implemented yet (RED phase)")
        
        # Create metadata for fractional rate
        metadata = create_fractional_metadata(
            fps_rational=(30000, 1001),
            size=(1920, 1080),
            duration_secs=10,
            seq_bits=7,
            event_times=[1.0, 2.0, 3.0]
        )
        
        # Should have all fields expected by existing tools
        required_fields = [
            "size", "fps", "durationSecs", "patternWindowLength",
            "eventCentreTimes", "approxBeepDurationSecs", "approxFlashDurationSecs"
        ]
        
        for field in required_fields:
            assert field in metadata, f"Metadata should include {field} for compatibility"
        
        # fps field should be decimal for backward compatibility
        assert isinstance(metadata["fps"], (int, float)), "fps should be numeric for compatibility"
        
        # Should also have new fractional fields
        assert "fps_rational" in metadata, "Should include new fps_rational field"
        assert "frame_duration_exact" in metadata, "Should include exact frame duration"


if __name__ == '__main__':
    pytest.main([__file__, "-v"])