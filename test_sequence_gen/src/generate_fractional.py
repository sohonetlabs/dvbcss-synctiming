#!/usr/bin/env python3
"""
Fractional Frame Rate Test Sequence Generator

This module integrates fractional frame rate support into the existing test
sequence generator. It combines all the fractional modules to provide a complete
end-to-end solution for generating test sequences at broadcast frame rates.

Phase 7: End-to-End Integration
- Integrates CLI parsing with fractional frame rates
- Uses fractional event generation for exact timing
- Produces frame-accurate test sequences
- Maintains backward compatibility
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from audio import saveAsWavFile

# Import fractional modules
from cli_fractional_integration import (
    create_fractional_metadata,
    format_fps_display,
    parse_fractional_args,
)

# Import existing modules
from eventTimingGen import _mls_taps, calcNearestDurationForExactNumberOfCycles
from fractional_event_generation import (
    genBeepSequenceFractional,
    genEventCentreTimesFractional,
    genFlashSequenceFractional,
)
from frame_timing import calculate_frame_duration
from video import genFrameImages


def generate_fractional_test_sequence(
    fps_rational: Tuple[int, int],
    size: Tuple[int, int],
    duration_secs: int,
    window_len: int,
    sample_rate: int = 48000,
    title_text: str = "",
    field_based: bool = False,
    output_audio: bool = True,
    output_video: bool = True,
    output_metadata: bool = True,
    audio_filename: Optional[str] = None,
    frame_filename_pattern: Optional[str] = None,
    metadata_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete test sequence with fractional frame rate support.
    
    Args:
        fps_rational: Frame rate as (numerator, denominator) tuple
        size: Video dimensions as (width, height) tuple
        duration_secs: Sequence duration in seconds
        window_len: Pattern window length in bits
        sample_rate: Audio sample rate in Hz
        title_text: Title text for video frames
        field_based: If True, output fields instead of frames
        output_audio: If True, generate WAV file
        output_video: If True, generate PNG frames
        output_metadata: If True, generate metadata JSON
        audio_filename: Output path for WAV file
        frame_filename_pattern: Output pattern for PNG frames
        metadata_filename: Output path for metadata JSON
        
    Returns:
        Dictionary with generation results and statistics
    """
    fps_num, fps_den = fps_rational
    width, height = size
    
    # Validate window length
    if window_len not in _mls_taps:
        raise ValueError(f"Invalid window length {window_len}. Must be one of: {sorted(_mls_taps.keys())}")
    
    # Calculate exact frame duration
    frame_duration = calculate_frame_duration(fps_num, fps_den)
    
    # If field-based, double the effective frame rate
    if field_based:
        effective_fps_num = fps_num * 2
        effective_fps_den = fps_den
    else:
        effective_fps_num = fps_num
        effective_fps_den = fps_den
    
    # Calculate adjusted duration for exact number of cycles
    # This ensures the pattern repeats perfectly
    # The function expects cycle frequency (Hz), so convert cycle length to Hz
    cycle_len_secs = 2**window_len - 1
    cycle_hz = 1.0 / cycle_len_secs
    
    # Ensure minimum duration is at least one full cycle
    min_duration = max(duration_secs, cycle_len_secs)
    adjusted_duration = int(calcNearestDurationForExactNumberOfCycles(
        idealDurationSecs=min_duration,
        cycleHz=cycle_hz
    ))
    
    print("Generating test sequence:")
    print(f"  Frame rate: {format_fps_display(fps_rational)}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Duration: {adjusted_duration} seconds")
    print(f"  Window length: {window_len} bits")
    print(f"  Pattern repeats every: {2**window_len - 1} seconds")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Mode: {'Field-based' if field_based else 'Frame-based'}")
    
    # Generate event timings using fractional arithmetic
    print("\nGenerating event timings...")
    event_times = []
    event_gen = genEventCentreTimesFractional(
        seqBits=window_len,
        fps_num=fps_num,
        fps_den=fps_den
    )
    
    for event_time in event_gen:
        if float(event_time) >= adjusted_duration:
            break
        event_times.append(event_time)
    
    print(f"  Generated {len(event_times)} events")
    
    # Calculate flash/beep duration (3 frames)
    flash_duration = frame_duration * 3
    
    # Generate audio if requested
    audio_samples = None
    if output_audio:
        print("\nGenerating audio...")
        beep_gen = genBeepSequenceFractional(
            beepCentreTimesSecs=event_times,
            idealBeepDurationSecs=flash_duration,
            sequenceDurationSecs=adjusted_duration,
            sampleRateHz=sample_rate,
            fps_num=fps_num,
            fps_den=fps_den,
            toneHz=3000,
            amplitude=16384
        )
        
        audio_samples = list(beep_gen)
        print(f"  Generated {len(audio_samples)} samples ({len(audio_samples)/sample_rate:.2f} seconds)")
        
        if audio_filename:
            print(f"  Saving to: {audio_filename}")
            # Ensure output directory exists
            Path(audio_filename).parent.mkdir(parents=True, exist_ok=True)
            saveAsWavFile(audio_samples, audio_filename, sample_rate)
    
    # Generate video frames if requested
    video_frames = None
    if output_video:
        print("\nGenerating video frames...")
        
        # Calculate total frames
        frames_exact = adjusted_duration * effective_fps_num / effective_fps_den
        total_frames = int(frames_exact)
        if frames_exact > total_frames:
            total_frames += 1
        
        # Generate flash sequence using fractional method
        flash_gen = genFlashSequenceFractional(
            flashCentreTimesSecs=event_times,
            idealFlashDurationSecs=flash_duration,
            sequenceDurationSecs=adjusted_duration,
            fps_num=effective_fps_num,
            fps_den=effective_fps_den,
            gapValue=(0, 0, 0),
            flashValue=(255, 255, 255)  # genFrameImages expects RGB values 0-255
        )
        
        # Convert to list for genFrameImages
        flash_sequence = list(flash_gen)
        print(f"  Generated {len(flash_sequence)} flash states")
        
        if frame_filename_pattern:
            print(f"  Saving frames to: {frame_filename_pattern}")
            # Ensure output directory exists
            frame_dir = Path(frame_filename_pattern).parent
            frame_dir.mkdir(parents=True, exist_ok=True)
            
            # Use genFrameImages to create frames with overlays
            # Note: genFrameImages expects a pipTrainSequence which we don't use
            # for fractional rates, so we pass an empty generator
            empty_pip_train = (None for _ in range(total_frames))
            
            # Default colors
            bg_colour = (0, 0, 0)
            text_colour = (255, 255, 255)
            gfx_colour = (255, 255, 255)
            title_colour = (255, 255, 255)
            
            # Generate frames using existing video module
            frame_generator = genFrameImages(
                size=size,
                flashColourGen=iter(flash_sequence),
                flashColourGenPipTrain=empty_pip_train,
                numFrames=total_frames,
                FPS=fps_num/fps_den if not field_based else (effective_fps_num/effective_fps_den),
                BG_COLOUR=bg_colour,
                TEXT_COLOUR=text_colour,
                GFX_COLOUR=gfx_colour,
                title=title_text,
                TITLE_COLOUR=title_colour,
                FRAMES_AS_FIELDS=field_based,
                segments=[]
            )
            
            # Save each frame
            frame_count = 0
            for frame_num, frame_img in enumerate(frame_generator):
                filename = frame_filename_pattern % frame_num
                frame_img.save(filename, "PNG")
                frame_count += 1
            
            video_frames = list(range(frame_count))  # Just track count
            print(f"  Saved {frame_count} frames")
    
    # Generate metadata if requested
    metadata = None
    if output_metadata:
        print("\nGenerating metadata...")
        
        # Convert event times to float for JSON serialization
        event_times_float = [float(e) for e in event_times]
        
        metadata = create_fractional_metadata(
            fps_rational=fps_rational,
            size=size,
            duration_secs=adjusted_duration,
            seq_bits=window_len,
            event_times=event_times_float,
            beep_duration_secs=float(flash_duration),
            flash_duration_secs=float(flash_duration)
        )
        
        # Add additional metadata
        metadata['adjusted_duration'] = adjusted_duration
        metadata['field_based'] = field_based
        metadata['sample_rate'] = sample_rate
        metadata['title'] = title_text
        metadata['pattern_repeat_time'] = 2**window_len - 1
        metadata['total_frames'] = len(video_frames) if video_frames else 0
        metadata['total_audio_samples'] = len(audio_samples) if audio_samples else 0
        
        if metadata_filename:
            print(f"  Saving to: {metadata_filename}")
            # Ensure output directory exists
            Path(metadata_filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_filename, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    print("\nGeneration complete!")
    
    # Return results
    return {
        'success': True,
        'fps_rational': fps_rational,
        'size': size,
        'duration': adjusted_duration,
        'window_len': window_len,
        'event_count': len(event_times),
        'frame_count': len(video_frames) if video_frames else 0,
        'sample_count': len(audio_samples) if audio_samples else 0,
        'metadata': metadata
    }


def main():
    """Main entry point for fractional frame rate test sequence generator."""
    
    # Default values (matching original generate.py)
    
    # Default output paths
    default_audio_file = "build/audio.wav"
    default_frame_pattern = "build/img_%06d.png"
    default_metadata_file = "build/metadata.json"
    
    # Parse command line arguments using fractional CLI parser
    args = parse_fractional_args(sys.argv[1:])
    
    # Set default output paths if not specified
    if args.AUDIO_FILENAME is None:
        args.AUDIO_FILENAME = default_audio_file
    if args.FRAME_FILENAME_PATTERN is None:
        args.FRAME_FILENAME_PATTERN = default_frame_pattern
    if args.METADATA_FILENAME is None:
        args.METADATA_FILENAME = default_metadata_file
    
    # Determine what outputs to generate
    output_audio = args.AUDIO_FILENAME is not None
    output_video = args.FRAME_FILENAME_PATTERN is not None
    output_metadata = args.METADATA_FILENAME is not None
    
    # Generate the test sequence
    try:
        result = generate_fractional_test_sequence(
            fps_rational=args.fps_rational,
            size=args.size,
            duration_secs=args.DURATION,
            window_len=args.WINDOW_LEN,
            sample_rate=args.SAMPLE_RATE,
            title_text=args.TITLE_TEXT,
            field_based=args.FIELD_BASED,
            output_audio=output_audio,
            output_video=output_video,
            output_metadata=output_metadata,
            audio_filename=args.AUDIO_FILENAME if output_audio else None,
            frame_filename_pattern=args.FRAME_FILENAME_PATTERN if output_video else None,
            metadata_filename=args.METADATA_FILENAME if output_metadata else None
        )
        
        if result['success']:
            print("\nSummary:")
            print(f"  Events generated: {result['event_count']}")
            print(f"  Frames generated: {result['frame_count']}")
            print(f"  Audio samples: {result['sample_count']}")
            
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()