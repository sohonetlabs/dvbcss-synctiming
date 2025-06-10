#!/usr/bin/env python3
"""
Fractional Frame Rate Event Generation

This module extends the existing event generation system to support fractional
frame rates using exact rational arithmetic. Integrates with frame_timing.py
and frame_rate_parser.py for precise timing calculations.

Phase 5.1: Fractional Event Generation Implementation (GREEN phase)
- genEventCentreTimesFractional: Generate events for fractional frame rates
- genFlashSequenceFractional: Frame-accurate flash sequences  
- genBeepSequenceFractional: Sample-accurate beep sequences
- createFpsBitTimingsFractional: Bit timings for fractional rates
"""

from fractions import Fraction
from typing import Iterator, Tuple, List, Union
import itertools

# Import existing modules
from eventTimingGen import mls, encodeBitStreamAsPulseTimings
from frame_timing import (
    frame_to_seconds, seconds_to_frame, calculate_frame_duration,
    validate_fps_rational
)


def createFpsBitTimingsFractional(fps_num: int, fps_den: int) -> dict:
    """
    Create bit timings for fractional frame rates using exact rational arithmetic.
    
    The timing design follows the same pattern as the existing fpsBitTimings:
    - Zero bit: one pulse at 3.5 frame units
    - One bit: two pulses at 3.5 and 9.5 frame units
    
    For fractional rates, we use the base frame rate for timing calculations:
    - 24000/1001 fps uses 24 fps base
    - 30000/1001 fps uses 30 fps base
    - 60000/1001 fps uses 30 fps base (doubled)
    
    Args:
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Dictionary with bit timings as Fraction objects
        
    Example:
        createFpsBitTimingsFractional(30000, 1001) returns:
        {
            0: [Fraction(3.5 * 1001, 30000)],
            1: [Fraction(3.5 * 1001, 30000), Fraction(9.5 * 1001, 30000)]
        }
    """
    validate_fps_rational(fps_num, fps_den)
    
    # Determine base frame rate for timing calculations
    # This matches the existing fpsBitTimings design
    fps_decimal = fps_num / fps_den
    
    if abs(fps_decimal - 23.976) < 0.1:  # 24000/1001
        base_fps = 24
    elif abs(fps_decimal - 29.97) < 0.1:  # 30000/1001
        base_fps = 30
    elif abs(fps_decimal - 47.952) < 0.1:  # 48000/1001
        base_fps = 24  # Uses 24 fps base like 48 fps
    elif abs(fps_decimal - 59.94) < 0.1:  # 60000/1001
        base_fps = 30  # Uses 30 fps base like 60 fps
    elif abs(fps_decimal - 119.88) < 0.1:  # 120000/1001
        base_fps = 30  # Uses 30 fps base like 120 fps
    else:
        # For other fractional rates, use closest integer base
        base_fps = round(fps_decimal)
        if base_fps > 60:
            base_fps = 30  # High frame rates use 30 fps base
        elif base_fps > 30:
            base_fps = 24 if base_fps <= 48 else 30
    
    # Create exact rational timings based on base fps
    # The design uses base frame positions: 3.5 and 9.5 frame units
    # These are converted to seconds using: time = frame_position / base_fps
    
    # Zero bit: pulse at 3.5 base frame units 
    zero_timing = Fraction(35, 10 * base_fps)  # 3.5 / base_fps seconds
    
    # One bit: pulses at 3.5 and 9.5 base frame units
    one_timing_1 = Fraction(35, 10 * base_fps)  # 3.5 / base_fps seconds
    one_timing_2 = Fraction(95, 10 * base_fps)  # 9.5 / base_fps seconds
    
    return {
        0: [zero_timing],
        1: [one_timing_1, one_timing_2]
    }


def genEventCentreTimesFractional(seqBits: int, fps_num: int, fps_den: int) -> Iterator[Fraction]:
    """
    Generate event center times for fractional frame rates using exact rational arithmetic.
    
    This is the fractional equivalent of genEventCentreTimes() that works with
    rational frame rates and returns exact Fraction times.
    
    Args:
        seqBits: Maximal-length sequence size in bits
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Yields:
        Event times as exact Fraction objects in seconds
        
    Example:
        gen = genEventCentreTimesFractional(3, 30000, 1001)
        events = [next(gen) for _ in range(5)]  # First 5 events
    """
    validate_fps_rational(fps_num, fps_den)
    
    # Generate maximal length sequence
    bitStream = mls(bitLen=seqBits, limitRepeats=None)
    
    # Create bit timings for this fractional frame rate
    bit_timings = createFpsBitTimingsFractional(fps_num, fps_den)
    bitZeroTimings = bit_timings[0]
    bitOneTimings = bit_timings[1]
    
    # Bit interval is 1 second (same as original design)
    bitInterval = Fraction(1, 1)
    
    # Use existing encodeBitStreamAsPulseTimings but convert to exact fractions
    timing_generator = encodeBitStreamAsPulseTimings(
        bitStream, float(bitInterval), 
        [float(t) for t in bitZeroTimings],
        [float(t) for t in bitOneTimings]
    )
    
    # Convert float timings back to exact fractions for precision
    for timing in timing_generator:
        # Find which bit timing this corresponds to and return exact value
        timing_fraction = Fraction(timing).limit_denominator(max_denominator=1000000)
        
        # Try to match with exact bit timings for maximum precision
        for bit_val in [0, 1]:
            for exact_timing in bit_timings[bit_val]:
                if abs(float(exact_timing) - timing) < 1e-10:
                    timing_fraction = exact_timing
                    break
        
        yield timing_fraction


def genFlashSequenceFractional(flashCentreTimesSecs: List[Fraction], 
                              idealFlashDurationSecs: Union[Fraction, float],
                              sequenceDurationSecs: Union[Fraction, float, int],
                              fps_num: int, fps_den: int,
                              gapValue: Tuple[int, int, int] = (0, 0, 0),
                              flashValue: Tuple[int, int, int] = (255, 255, 255)) -> Iterator[Tuple[int, int, int]]:
    """
    Generate flash sequence for fractional frame rates with exact timing.
    
    This is the fractional equivalent of genFlashSequence() that works with
    rational frame rates and exact timing calculations.
    
    Args:
        flashCentreTimesSecs: List of flash center times as Fraction objects
        idealFlashDurationSecs: Duration of each flash (Fraction or float)
        sequenceDurationSecs: Total sequence duration
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        gapValue: RGB tuple for non-flash frames
        flashValue: RGB tuple for flash frames
        
    Yields:
        RGB tuples for each frame in sequence
    """
    validate_fps_rational(fps_num, fps_den)
    
    # Convert durations to Fraction for exact arithmetic
    if isinstance(idealFlashDurationSecs, (int, float)):
        flash_duration = Fraction(idealFlashDurationSecs).limit_denominator(max_denominator=1000000)
    else:
        flash_duration = idealFlashDurationSecs
    
    if isinstance(sequenceDurationSecs, (int, float)):
        sequence_duration = Fraction(sequenceDurationSecs).limit_denominator(max_denominator=1000000)
    else:
        sequence_duration = sequenceDurationSecs
    
    # Calculate total number of frames (use ceiling to ensure we cover full duration)
    frames_exact = sequence_duration * fps_num / fps_den
    total_frames = int(frames_exact)
    if frames_exact > total_frames:
        total_frames += 1
    
    # Calculate flash start/end times
    flash_intervals = []
    for center_time in flashCentreTimesSecs:
        start_time = center_time - flash_duration / 2
        end_time = center_time + flash_duration / 2
        flash_intervals.append((start_time, end_time))
    
    # Generate frame sequence
    for frame_num in range(total_frames):
        # Calculate exact time for this frame
        frame_time = frame_to_seconds(frame_num, fps_num, fps_den)
        
        # Check if this frame should flash
        is_flash = False
        for start_time, end_time in flash_intervals:
            if start_time <= frame_time <= end_time:
                is_flash = True
                break
        
        yield flashValue if is_flash else gapValue


def genBeepSequenceFractional(beepCentreTimesSecs: List[Fraction],
                             idealBeepDurationSecs: Union[Fraction, float],
                             sequenceDurationSecs: Union[Fraction, float, int],
                             sampleRateHz: int,
                             fps_num: int, fps_den: int,
                             toneHz: int = 3000,
                             amplitude: int = 16384) -> Iterator[int]:
    """
    Generate beep sequence for fractional frame rates with sample-accurate timing.
    
    This is the fractional equivalent of genBeepSequence() that works with
    rational frame rates and exact timing calculations.
    
    Args:
        beepCentreTimesSecs: List of beep center times as Fraction objects
        idealBeepDurationSecs: Duration of each beep (Fraction or float)
        sequenceDurationSecs: Total sequence duration
        sampleRateHz: Audio sample rate in Hz
        fps_num: Frame rate numerator  
        fps_den: Frame rate denominator
        toneHz: Beep tone frequency in Hz
        amplitude: Beep amplitude (0-32767)
        
    Yields:
        16-bit audio samples as integers
    """
    validate_fps_rational(fps_num, fps_den)
    
    # Convert durations to Fraction for exact arithmetic
    if isinstance(idealBeepDurationSecs, (int, float)):
        beep_duration = Fraction(idealBeepDurationSecs).limit_denominator(max_denominator=1000000)
    else:
        beep_duration = idealBeepDurationSecs
    
    if isinstance(sequenceDurationSecs, (int, float)):
        sequence_duration = Fraction(sequenceDurationSecs).limit_denominator(max_denominator=1000000)
    else:
        sequence_duration = sequenceDurationSecs
    
    # Calculate total number of samples
    total_samples = int(float(sequence_duration) * sampleRateHz)
    
    # Calculate beep start/end sample positions
    beep_intervals = []
    for center_time in beepCentreTimesSecs:
        start_time = center_time - beep_duration / 2
        end_time = center_time + beep_duration / 2
        
        # Convert to sample positions
        start_sample = int(float(start_time) * sampleRateHz)
        end_sample = int(float(end_time) * sampleRateHz)
        beep_intervals.append((start_sample, end_sample))
    
    # Generate sample sequence
    import math
    
    for sample_num in range(total_samples):
        # Check if this sample should beep
        is_beep = False
        for start_sample, end_sample in beep_intervals:
            if start_sample <= sample_num <= end_sample:
                is_beep = True
                break
        
        if is_beep:
            # Generate sine wave tone
            time_sec = sample_num / sampleRateHz
            sample_value = int(amplitude * math.sin(2 * math.pi * toneHz * time_sec))
        else:
            # Silence
            sample_value = 0
        
        yield sample_value


def get_fractional_timing_info(fps_num: int, fps_den: int) -> dict:
    """
    Get comprehensive timing information for a fractional frame rate.
    
    Args:
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Dictionary with fractional timing information
    """
    validate_fps_rational(fps_num, fps_den)
    
    frame_duration = calculate_frame_duration(fps_num, fps_den)
    bit_timings = createFpsBitTimingsFractional(fps_num, fps_den)
    
    return {
        'fps_rational': (fps_num, fps_den),
        'fps_decimal': fps_num / fps_den,
        'frame_duration_fraction': frame_duration,
        'frame_duration_seconds': float(frame_duration),
        'bit_timings_zero': bit_timings[0],
        'bit_timings_one': bit_timings[1],
        'samples_per_frame_48k': float(frame_duration) * 48000,
        'microseconds_per_frame': float(frame_duration) * 1000000,
        'nanoseconds_per_frame': float(frame_duration) * 1000000000,
    }


if __name__ == "__main__":
    # Demo usage
    print("Fractional Frame Rate Event Generation Demo")
    print("=" * 50)
    
    # Test with NTSC frame rates
    ntsc_rates = [
        (24000, 1001),  # 23.976 fps
        (30000, 1001),  # 29.97 fps
        (60000, 1001),  # 59.94 fps
    ]
    
    for fps_num, fps_den in ntsc_rates:
        fps_decimal = fps_num / fps_den
        print(f"\nFrame Rate: {fps_decimal:.6f} fps ({fps_num}/{fps_den})")
        
        # Show bit timings
        bit_timings = createFpsBitTimingsFractional(fps_num, fps_den)
        print(f"  Zero bit timing: {bit_timings[0][0]}")
        print(f"  One bit timings: {bit_timings[1][0]}, {bit_timings[1][1]}")
        
        # Generate some events
        events = []
        gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
        for i, event in enumerate(gen):
            if i >= 3:
                break
            events.append(event)
        
        print(f"  First 3 events: {[float(e) for e in events]}")
        
        # Show frame alignment
        for i, event in enumerate(events):
            frame_pos = event * fps_num / fps_den
            print(f"    Event {i}: {float(event):.6f}s = frame {float(frame_pos):.3f}")
    
    print("\nFlash sequence demo (29.97 fps, 1 second):")
    print("=" * 45)
    
    fps_num, fps_den = 30000, 1001
    events = []
    gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
    for i, event in enumerate(gen):
        if event >= 1.0:  # 1 second
            break
        events.append(event)
    
    frame_duration = calculate_frame_duration(fps_num, fps_den)
    flash_duration = frame_duration * 3  # 3-frame flash
    
    flash_gen = genFlashSequenceFractional(
        flashCentreTimesSecs=events,
        idealFlashDurationSecs=flash_duration,
        sequenceDurationSecs=1,
        fps_num=fps_num,
        fps_den=fps_den
    )
    
    flash_frames = list(flash_gen)
    flash_count = sum(1 for color in flash_frames if color != (0, 0, 0))
    
    print(f"Generated {len(flash_frames)} frames with {flash_count} flash frames")
    print(f"Flash ratio: {flash_count/len(flash_frames)*100:.1f}%")
    
    # Show first few frames
    for i, color in enumerate(flash_frames[:10]):
        status = "FLASH" if color != (0, 0, 0) else "gap"
        frame_time = frame_to_seconds(i, fps_num, fps_den)
        print(f"  Frame {i:2d}: {float(frame_time):.6f}s - {status}")
    
    print("\nBeep sequence demo (23.976 fps, 0.5 seconds):")
    print("=" * 48)
    
    fps_num, fps_den = 24000, 1001
    events = []
    gen = genEventCentreTimesFractional(seqBits=3, fps_num=fps_num, fps_den=fps_den)
    for i, event in enumerate(gen):
        if event >= 0.5:  # 0.5 seconds
            break
        events.append(event)
    
    beep_duration = calculate_frame_duration(fps_num, fps_den) * 2  # 2-frame beep
    beep_gen = genBeepSequenceFractional(
        beepCentreTimesSecs=events,
        idealBeepDurationSecs=beep_duration,
        sequenceDurationSecs=0.5,
        sampleRateHz=48000,
        fps_num=fps_num,
        fps_den=fps_den,
        toneHz=1000,
        amplitude=8000
    )
    
    beep_samples = list(beep_gen)
    beep_count = sum(1 for sample in beep_samples if abs(sample) > 100)
    
    print(f"Generated {len(beep_samples)} samples with {beep_count} beep samples")
    print(f"Beep ratio: {beep_count/len(beep_samples)*100:.1f}%")