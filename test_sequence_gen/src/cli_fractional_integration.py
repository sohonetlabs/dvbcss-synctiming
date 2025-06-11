#!/usr/bin/env python3
"""
CLI Integration for Fractional Frame Rates

This module extends the existing CLI interface to support fractional frame rates,
broadcast shortcuts, resolution presets, and complete format presets.

Phase 6.1: CLI Integration Implementation (GREEN phase)
- parse_fractional_args: Enhanced argument parsing with fractional fps support
- create_fractional_metadata: Metadata generation with exact rational information
- get_resolution_preset: Resolution shortcuts (4k-full, hd-1080, etc.)
- get_format_preset: Complete format presets (1080p59.94, cinema-4k, etc.)
"""

import argparse
import re
from fractions import Fraction
from typing import Any, Dict, List, Tuple

# Import our modules
from frame_rate_parser import get_broadcast_standard_fps, parse_frame_rate
from frame_timing import validate_fps_rational

# Resolution presets for professional formats
RESOLUTION_PRESETS = {
    # TV/Broadcast resolutions
    "sd-ntsc": (720, 480),      # NTSC SD
    "sd-pal": (720, 576),       # PAL SD
    "hd-720": (1280, 720),      # HD 720p
    "hd-1080": (1920, 1080),    # HD 1080p/i
    "uhd-4k": (3840, 2160),     # UHD 4K
    "uhd-8k": (7680, 4320),     # UHD 8K
    
    # Cinema resolutions
    "2k-flat": (1998, 1080),    # 2K Flat (1.85:1)
    "2k-scope": (2048, 858),    # 2K Cinemascope (2.39:1)
    "2k-full": (2048, 1080),    # 2K Full Container
    "4k-flat": (3996, 2160),    # 4K Flat (1.85:1)
    "4k-scope": (4096, 1716),   # 4K Cinemascope (2.39:1)
    "4k-full": (4096, 2160),    # 4K DCI Full Container
    "imax-digital": (5120, 2700), # IMAX Digital
}

# Complete format presets combining fps + resolution
FORMAT_PRESETS = {
    # TV Broadcast presets
    "ntsc-sd": ((30000, 1001), (720, 480)),        # NTSC Standard Def
    "pal-sd": ((25, 1), (720, 576)),               # PAL Standard Def
    "1080i50": ((25, 1), (1920, 1080)),            # HD PAL regions
    "1080i59.94": ((30000, 1001), (1920, 1080)),   # HD NTSC regions
    "1080p25": ((25, 1), (1920, 1080)),            # Progressive PAL
    "1080p30": ((30, 1), (1920, 1080)),            # Progressive web
    "1080p50": ((50, 1), (1920, 1080)),            # High motion PAL
    "1080p60": ((60, 1), (1920, 1080)),            # High motion NTSC
    "1080p59.94": ((60000, 1001), (1920, 1080)),   # High motion NTSC fractional
    "720p50": ((50, 1), (1280, 720)),              # 720p PAL
    "720p60": ((60, 1), (1280, 720)),              # 720p NTSC
    "4k50": ((50, 1), (3840, 2160)),               # 4K PAL
    "4k60": ((60, 1), (3840, 2160)),               # 4K NTSC
    "4k59.94": ((60000, 1001), (3840, 2160)),      # 4K NTSC fractional
    
    # Cinema presets
    "cinema-2k": ((24, 1), (2048, 1080)),          # 2K DCI
    "cinema-4k": ((24, 1), (4096, 2160)),          # 4K DCI
    "cinema-4k-scope": ((24, 1), (4096, 1716)),    # 4K Scope
    "cinema-4k-hfr": ((48, 1), (4096, 2160)),      # 4K HFR
    "cinema-4k-hfr-60": ((60, 1), (4096, 2160)),   # 4K HFR 60
    "imax-digital": ((24, 1), (5120, 2700)),       # IMAX Digital
}

# Broadcast standard shortcuts for CLI
BROADCAST_SHORTCUTS = {
    # NTSC Family
    "ntsc-film": (24000, 1001),
    "ntsc": (30000, 1001),
    "ntsc-hd": (60000, 1001),
    "ntsc-4k": (120000, 1001),
    
    # PAL Family
    "pal": (25, 1),
    "pal-hd": (50, 1),
    "pal-4k": (100, 1),
    
    # Cinema Standards
    "film": (24, 1),
    "film-hfr-48": (48, 1),
    "film-hfr-60": (60, 1),
    "film-hfr-120": (120, 1),
}


def get_resolution_preset(preset_name: str) -> Tuple[int, int]:
    """
    Get resolution for a named preset.
    
    Args:
        preset_name: Resolution preset name (e.g., "4k-full", "hd-1080")
        
    Returns:
        Tuple of (width, height) in pixels
        
    Raises:
        ValueError: If preset name is unknown
    """
    if preset_name not in RESOLUTION_PRESETS:
        available = ", ".join(sorted(RESOLUTION_PRESETS.keys()))
        raise ValueError(f"Unknown resolution preset: '{preset_name}'. "
                        f"Available presets: {available}")
    
    return RESOLUTION_PRESETS[preset_name]


def get_format_preset(preset_name: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Get complete format preset (fps + resolution).
    
    Args:
        preset_name: Format preset name (e.g., "1080p59.94", "cinema-4k")
        
    Returns:
        Tuple of ((fps_num, fps_den), (width, height))
        
    Raises:
        ValueError: If preset name is unknown
    """
    if preset_name not in FORMAT_PRESETS:
        available = ", ".join(sorted(FORMAT_PRESETS.keys()))
        raise ValueError(f"Unknown format preset: '{preset_name}'. "
                        f"Available presets: {available}")
    
    return FORMAT_PRESETS[preset_name]


def parse_fractional_args(args_list: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments with fractional frame rate support.
    
    Extends the existing argument parser to support:
    - Fractional fps: --fps 23.976, --fps 24000/1001
    - Broadcast shortcuts: --fps-ntsc-film, --fps-pal, etc.
    - Resolution shortcuts: --size-4k-full, --size-hd-1080, etc.
    - Format presets: --preset-1080p59.94, --preset-cinema-4k, etc.
    
    Args:
        args_list: List of command line arguments
        
    Returns:
        Parsed arguments with fps_rational and size attributes
        
    Raises:
        ValueError: If arguments are invalid or conflicting
    """
    
    # Create parser based on existing generate.py structure
    parser = argparse.ArgumentParser(
        description="Generate test sequence with fractional frame rate support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Fractional Frame Rate Examples:
  --fps 23.976                 # Decimal format
  --fps 24000/1001            # Rational format
  --fps-ntsc-film             # 23.976 fps shortcut
  --fps-pal                   # 25 fps shortcut

Resolution Examples:
  --size-4k-full              # 4096x2160
  --size-hd-1080              # 1920x1080
  --size-2k-scope             # 2048x858 (cinemascope)

Complete Preset Examples:
  --preset-1080p59.94         # 1080p @ 59.94 fps
  --preset-cinema-4k          # 4K DCI @ 24 fps
  --preset-ntsc-sd            # NTSC SD @ 29.97 fps
        """)
    
    # Frame rate arguments (mutually exclusive)
    fps_group = parser.add_mutually_exclusive_group()
    
    # Traditional fps argument (enhanced to support fractional)
    fps_group.add_argument(
        "--fps", dest="FPS_INPUT", type=str, metavar="RATE",
        help="Frame rate: integer (25), decimal (23.976), or rational (24000/1001)")
    
    # Broadcast standard shortcuts
    for standard in BROADCAST_SHORTCUTS:
        fps_group.add_argument(
            f"--fps-{standard}", dest="FPS_SHORTCUT", action="store_const", const=standard,
            help=f"{BROADCAST_SHORTCUTS[standard][0]}/{BROADCAST_SHORTCUTS[standard][1]} fps "
                 f"({BROADCAST_SHORTCUTS[standard][0]/BROADCAST_SHORTCUTS[standard][1]:.6f} fps)")
    
    # Resolution arguments (mutually exclusive with traditional --size)
    size_group = parser.add_mutually_exclusive_group()
    
    # Traditional size argument  
    size_group.add_argument(
        "--size", dest="SIZE_INPUT", type=str, metavar="WxH",
        help="Frame dimensions as WIDTHxHEIGHT (e.g., 1920x1080)")
    
    # Resolution preset shortcuts
    for preset in RESOLUTION_PRESETS:
        size_group.add_argument(
            f"--size-{preset}", dest="SIZE_SHORTCUT", action="store_const", const=preset,
            help=f"{RESOLUTION_PRESETS[preset][0]}x{RESOLUTION_PRESETS[preset][1]} resolution")
    
    # Complete format presets (mutually exclusive with fps and size)
    preset_group = parser.add_mutually_exclusive_group()
    for preset in FORMAT_PRESETS:
        fps_rational, size = FORMAT_PRESETS[preset]
        fps_decimal = fps_rational[0] / fps_rational[1]
        preset_group.add_argument(
            f"--preset-{preset}", dest="FORMAT_PRESET", action="store_const", const=preset,
            help=f"{size[0]}x{size[1]} @ {fps_decimal:.6f} fps")
    
    # Other arguments (based on existing generate.py)
    parser.add_argument(
        "--fields", dest="FIELD_BASED", action="store_true", default=False,
        help="Output fields instead of frames")
    
    parser.add_argument(
        "--window-len", dest="WINDOW_LEN", type=int, default=7, metavar="N",
        help="Pattern window length in bits (default: 7)")
    
    parser.add_argument(
        "--duration", dest="DURATION", type=int, metavar="SECS",
        help="Sequence duration in seconds")
    
    parser.add_argument(
        "--sampleRate", dest="SAMPLE_RATE", type=int, default=48000, metavar="HZ",
        help="Audio sample rate in Hz (default: 48000)")
    
    parser.add_argument(
        "--title", dest="TITLE_TEXT", type=str, default="", metavar="TEXT",
        help="Title text for video frames")
    
    parser.add_argument(
        "--frame-filename", dest="FRAME_FILENAME_PATTERN", type=str, metavar="PATTERN",
        help="Filename pattern for PNG frames (printf style)")
    
    parser.add_argument(
        "--wav-filename", dest="AUDIO_FILENAME", type=str, metavar="FILE",
        help="Filename for WAV audio output")
    
    parser.add_argument(
        "--metadata-filename", dest="METADATA_FILENAME", type=str, metavar="FILE",
        help="Filename for JSON metadata output")
    
    # Parse arguments
    parsed_args = parser.parse_args(args_list)
    
    # Process frame rate
    fps_rational = None
    fps_source = None
    
    if parsed_args.FORMAT_PRESET:
        # Complete format preset
        fps_rational, size = get_format_preset(parsed_args.FORMAT_PRESET)
        parsed_args.fps_rational = fps_rational
        parsed_args.size = size
        fps_source = f"preset-{parsed_args.FORMAT_PRESET}"
        
    else:
        # Process fps arguments
        if parsed_args.FPS_INPUT:
            fps_rational = parse_frame_rate(parsed_args.FPS_INPUT)
            fps_source = f"fps-{parsed_args.FPS_INPUT}"
        elif parsed_args.FPS_SHORTCUT:
            fps_rational = get_broadcast_standard_fps(parsed_args.FPS_SHORTCUT)
            fps_source = f"fps-{parsed_args.FPS_SHORTCUT}"
        else:
            # Default to 50 fps (as integer)
            fps_rational = (50, 1)
            fps_source = "default"
        
        parsed_args.fps_rational = fps_rational
        
        # Process size arguments
        if parsed_args.SIZE_INPUT:
            # Parse traditional WxH format
            match = re.match(r'^(\d+)x(\d+)$', parsed_args.SIZE_INPUT)
            if not match:
                raise ValueError(f"Invalid size format: {parsed_args.SIZE_INPUT}. Use WIDTHxHEIGHT format.")
            parsed_args.size = (int(match.group(1)), int(match.group(2)))
        elif parsed_args.SIZE_SHORTCUT:
            parsed_args.size = get_resolution_preset(parsed_args.SIZE_SHORTCUT)
        else:
            # Default size
            parsed_args.size = (854, 480)
    
    # Validate fps_rational
    validate_fps_rational(parsed_args.fps_rational[0], parsed_args.fps_rational[1])
    
    # Set default duration if not specified
    if parsed_args.DURATION is None:
        parsed_args.DURATION = 2**parsed_args.WINDOW_LEN - 1
    
    # Store metadata about argument sources for debugging
    parsed_args._fps_source = fps_source
    parsed_args._size_source = getattr(parsed_args, 'SIZE_SHORTCUT', 'manual')
    
    return parsed_args


def create_fractional_metadata(fps_rational: Tuple[int, int], 
                               size: Tuple[int, int],
                               duration_secs: int,
                               seq_bits: int,
                               event_times: List[float],
                               beep_duration_secs: float = None,
                               flash_duration_secs: float = None) -> Dict[str, Any]:
    """
    Create metadata dictionary with fractional frame rate information.
    
    Args:
        fps_rational: Frame rate as (numerator, denominator) tuple
        size: Video dimensions as (width, height) tuple  
        duration_secs: Sequence duration in seconds
        seq_bits: Pattern window length in bits
        event_times: List of event center times in seconds
        beep_duration_secs: Beep duration (optional)
        flash_duration_secs: Flash duration (optional)
        
    Returns:
        Metadata dictionary compatible with existing tools plus fractional info
    """
    fps_num, fps_den = fps_rational
    fps_decimal = fps_num / fps_den
    
    # Calculate exact frame duration
    frame_duration = Fraction(fps_den, fps_num)
    
    # Default durations if not provided
    if beep_duration_secs is None:
        beep_duration_secs = float(frame_duration * 3)  # 3 frames
    if flash_duration_secs is None:
        flash_duration_secs = float(frame_duration * 3)  # 3 frames
    
    # Create metadata compatible with existing tools
    metadata = {
        # Existing fields for backward compatibility
        "size": [size[0], size[1]],
        "fps": fps_decimal,  # Decimal fps for existing tools
        "durationSecs": duration_secs,
        "patternWindowLength": seq_bits,
        "eventCentreTimes": event_times,
        "approxBeepDurationSecs": beep_duration_secs,
        "approxFlashDurationSecs": flash_duration_secs,
        
        # New fractional frame rate fields
        "fps_rational": {
            "num": fps_num,
            "den": fps_den,
            "decimal": fps_decimal
        },
        "frame_duration_exact": {
            "num": frame_duration.numerator,
            "den": frame_duration.denominator,
            "seconds": float(frame_duration)
        },
        
        # Additional precision information
        "timing_precision": "exact_rational",
        "generator_version": "fractional_1.0",
        "notes": f"Generated with exact {fps_num}/{fps_den} fps timing using rational arithmetic"
    }
    
    return metadata


def format_fps_display(fps_rational: Tuple[int, int]) -> str:
    """
    Format frame rate for human-readable display.
    
    Args:
        fps_rational: Frame rate as (numerator, denominator) tuple
        
    Returns:
        Human-readable frame rate string
    """
    fps_num, fps_den = fps_rational
    
    if fps_den == 1:
        return f"{fps_num} fps"
    else:
        decimal = fps_num / fps_den
        return f"{decimal:.6f} fps ({fps_num}/{fps_den})"


def get_available_presets() -> Dict[str, List[str]]:
    """
    Get lists of all available presets for help/documentation.
    
    Returns:
        Dictionary with preset categories and their options
    """
    return {
        "broadcast_standards": list(BROADCAST_SHORTCUTS.keys()),
        "resolution_presets": list(RESOLUTION_PRESETS.keys()),
        "format_presets": list(FORMAT_PRESETS.keys())
    }


if __name__ == "__main__":
    # Demo usage
    print("Fractional Frame Rate CLI Integration Demo")
    print("=" * 50)
    
    # Test argument parsing
    test_cases = [
        ["--fps", "23.976", "--duration", "5"],
        ["--fps-ntsc-film", "--size-4k-full", "--duration", "3"],
        ["--preset-1080p59.94", "--duration", "10"],
        ["--fps-pal", "--size-hd-1080", "--window-len", "8"],
    ]
    
    for i, args in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {' '.join(args)}")
        try:
            parsed = parse_fractional_args(args)
            fps_display = format_fps_display(parsed.fps_rational)
            print(f"  Frame rate: {fps_display}")
            print(f"  Resolution: {parsed.size[0]}x{parsed.size[1]}")
            print(f"  Duration: {parsed.DURATION} seconds")
            print(f"  Window length: {parsed.WINDOW_LEN} bits")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Test metadata creation
    print(f"\nMetadata creation demo:")
    print("=" * 30)
    
    fps_rational = (30000, 1001)
    metadata = create_fractional_metadata(
        fps_rational=fps_rational,
        size=(1920, 1080),
        duration_secs=5,
        seq_bits=7,
        event_times=[0.5, 1.0, 2.0, 3.5]
    )
    
    print(f"Frame rate: {format_fps_display(fps_rational)}")
    print(f"Exact frame duration: {metadata['frame_duration_exact']['seconds']:.10f} seconds")
    print(f"Rational representation: {metadata['frame_duration_exact']['num']}/{metadata['frame_duration_exact']['den']}")
    print(f"Compatibility fps: {metadata['fps']}")
    
    # Show available presets
    print(f"\nAvailable presets:")
    print("=" * 20)
    
    presets = get_available_presets()
    for category, preset_list in presets.items():
        print(f"{category.replace('_', ' ').title()}:")
        for preset in sorted(preset_list)[:5]:  # Show first 5
            print(f"  --{category.replace('_', '-')}-{preset}")
        if len(preset_list) > 5:
            print(f"  ... and {len(preset_list) - 5} more")
        print()