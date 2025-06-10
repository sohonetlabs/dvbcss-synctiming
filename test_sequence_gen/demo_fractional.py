#!/usr/bin/env python3
"""
Demo script for fractional frame rate test sequence generation.

This script demonstrates the new fractional frame rate capabilities
added to the DVB CSS synchronization timing measurement system.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generate_fractional import generate_fractional_test_sequence
from cli_fractional_integration import parse_fractional_args, format_fps_display


def demo_basic_fractional():
    """Demonstrate basic fractional frame rate generation."""
    print("=" * 60)
    print("DEMO 1: Basic Fractional Frame Rate (29.97 fps)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_fractional_test_sequence(
            fps_rational=(30000, 1001),  # 29.97 fps
            size=(640, 480),
            duration_secs=3,
            window_len=3,
            sample_rate=48000,
            title_text="29.97 fps Demo",
            output_metadata=True,
            metadata_filename=os.path.join(tmpdir, "demo1_metadata.json")
        )
        
        print(f"\nGeneration complete:")
        print(f"  - Generated {result['event_count']} timing events")
        print(f"  - Frame rate: {format_fps_display(result['fps_rational'])}")
        print(f"  - Duration: {result['duration']} seconds")
        print(f"  - Metadata saved to: {tmpdir}/demo1_metadata.json")


def demo_broadcast_shortcuts():
    """Demonstrate broadcast standard shortcuts."""
    print("\n" + "=" * 60)
    print("DEMO 2: Broadcast Standard Shortcuts")
    print("=" * 60)
    
    # Parse CLI arguments with shortcuts
    shortcuts = [
        ["--fps-ntsc-film", "--duration", "2"],
        ["--fps-ntsc", "--duration", "2"],
        ["--fps-pal", "--duration", "2"],
    ]
    
    for args in shortcuts:
        parsed = parse_fractional_args(args)
        print(f"\nShortcut: {args[0]}")
        print(f"  Parsed to: {format_fps_display(parsed.fps_rational)}")


def demo_format_presets():
    """Demonstrate complete format presets."""
    print("\n" + "=" * 60)
    print("DEMO 3: Complete Format Presets")
    print("=" * 60)
    
    presets = [
        "--preset-1080p59.94",
        "--preset-cinema-4k",
        "--preset-ntsc-sd",
    ]
    
    for preset in presets:
        parsed = parse_fractional_args([preset, "--duration", "1"])
        print(f"\nPreset: {preset}")
        print(f"  Frame rate: {format_fps_display(parsed.fps_rational)}")
        print(f"  Resolution: {parsed.size[0]}x{parsed.size[1]}")


def demo_cinema_workflow():
    """Demonstrate cinema workflow with DCI 4K."""
    print("\n" + "=" * 60)
    print("DEMO 4: Cinema Workflow (DCI 4K at 23.976 fps)")
    print("=" * 60)
    
    # Parse cinema arguments
    args = parse_fractional_args([
        "--fps-ntsc-film",    # 23.976 fps
        "--size-4k-full",     # 4096x2160
        "--duration", "2",
        "--window-len", "4",
        "--title", "Cinema 4K Demo"
    ])
    
    print(f"\nCinema configuration:")
    print(f"  Frame rate: {format_fps_display(args.fps_rational)}")
    print(f"  Resolution: {args.size[0]}x{args.size[1]} (DCI 4K)")
    print(f"  Duration: {args.DURATION} seconds")
    print(f"  Pattern window: {args.WINDOW_LEN} bits")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_fractional_test_sequence(
            fps_rational=args.fps_rational,
            size=args.size,
            duration_secs=args.DURATION,
            window_len=args.WINDOW_LEN,
            title_text=args.TITLE_TEXT,
            output_audio=True,
            output_video=False,  # Skip video for demo speed
            output_metadata=True,
            audio_filename=os.path.join(tmpdir, "cinema_demo.wav"),
            metadata_filename=os.path.join(tmpdir, "cinema_demo.json")
        )
        
        print(f"\nGeneration results:")
        print(f"  - Events: {result['event_count']}")
        print(f"  - Audio samples: {result['sample_count']:,}")
        print(f"  - Exact frame duration: {1001/24000:.10f} seconds")


def main():
    """Run all demos."""
    print("\nDVB CSS Synchronization Timing - Fractional Frame Rate Demo")
    print("===========================================================\n")
    
    print("This demo showcases the new fractional frame rate support")
    print("including broadcast standards (NTSC, PAL) and cinema formats.\n")
    
    # Run demos
    demo_basic_fractional()
    demo_broadcast_shortcuts()
    demo_format_presets()
    demo_cinema_workflow()
    
    print("\n" + "=" * 60)
    print("Demo complete! The system now supports:")
    print("  - Fractional frame rates (23.976, 29.97, 59.94 fps)")
    print("  - Broadcast shortcuts (--fps-ntsc-film, --fps-pal, etc.)")
    print("  - Resolution presets (--size-4k-full, --size-hd-1080, etc.)")
    print("  - Complete format presets (--preset-1080p59.94, etc.)")
    print("  - Exact rational arithmetic (no floating-point errors)")
    print("=" * 60)


if __name__ == "__main__":
    main()