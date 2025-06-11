#!/usr/bin/env python3
"""
Frame Timing Calculations for Fractional Frame Rates

This module provides precise frame timing calculations using exact rational arithmetic.
Supports both integer and fractional frame rates with perfect precision.

Phase 4.1: Frame Timing Calculations Implementation (GREEN phase)
- frame_to_seconds: Convert frame number to exact time
- seconds_to_frame: Convert time to frame number  
- calculate_frame_duration: Calculate exact frame duration
- calculate_sequence_duration: Calculate total sequence duration
- validate_fps_rational: Validate frame rate rational inputs
"""

from fractions import Fraction
from typing import Union

# Reasonable frame rate bounds for validation
MIN_FRAME_RATE = 0.1  # 0.1 fps minimum
MAX_FRAME_RATE = 500.0  # 500 fps maximum


def frame_to_seconds(frame_num: int, fps_num: int, fps_den: int) -> Fraction:
    """
    Convert frame number to exact time in seconds using rational arithmetic.
    
    For a frame rate of fps_num/fps_den, frame N occurs at time:
    time = N * (fps_den / fps_num) seconds
    
    Args:
        frame_num: Frame number (0-based)
        fps_num: Frame rate numerator  
        fps_den: Frame rate denominator
        
    Returns:
        Exact time as Fraction object
        
    Example:
        frame_to_seconds(100, 30000, 1001) → Fraction(100100, 30000)
        # Frame 100 at 29.97 fps = 100 * (1001/30000) seconds
    """
    validate_fps_rational(fps_num, fps_den)
    
    if frame_num < 0:
        raise ValueError(f"Frame number must be non-negative, got {frame_num}")
    
    # time = frame_num * (fps_den / fps_num)
    return Fraction(frame_num * fps_den, fps_num)


def seconds_to_frame(time_secs: Union[Fraction, float, int], fps_num: int, fps_den: int) -> int:
    """
    Convert time in seconds to frame number using rational arithmetic.
    
    For a frame rate of fps_num/fps_den, time T corresponds to frame:
    frame = floor(T * fps_num / fps_den)
    
    Args:
        time_secs: Time in seconds (Fraction, float, or int)
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Frame number (integer, 0-based)
        
    Example:
        seconds_to_frame(Fraction(1001, 30000), 30000, 1001) → 1
        # Time 1001/30000 seconds at 29.97 fps = frame 1
    """
    validate_fps_rational(fps_num, fps_den)
    
    # Convert input to Fraction for exact arithmetic
    if isinstance(time_secs, (int, float)):
        time_fraction = Fraction(time_secs).limit_denominator(max_denominator=1000000)
    else:
        time_fraction = time_secs
    
    if time_fraction < 0:
        raise ValueError(f"Time must be non-negative, got {time_fraction}")
    
    # frame = floor(time * fps_num / fps_den)
    frame_exact = time_fraction * fps_num / fps_den
    return int(frame_exact)  # floor for positive numbers


def calculate_frame_duration(fps_num: int, fps_den: int) -> Fraction:
    """
    Calculate exact duration of one frame using rational arithmetic.
    
    Frame duration = 1 / frame_rate = fps_den / fps_num
    
    Args:
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Frame duration as exact Fraction
        
    Example:
        calculate_frame_duration(30000, 1001) → Fraction(1001, 30000)
        # Duration of one frame at 29.97 fps
    """
    validate_fps_rational(fps_num, fps_den)
    
    return Fraction(fps_den, fps_num)


def calculate_sequence_duration(n_frames: int, fps_num: int, fps_den: int) -> Fraction:
    """
    Calculate exact total duration for a sequence of frames.
    
    Total duration = n_frames * frame_duration = n_frames * fps_den / fps_num
    
    Args:
        n_frames: Number of frames in sequence
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Total duration as exact Fraction
        
    Example:
        calculate_sequence_duration(30000, 30000, 1001) → Fraction(1001, 1)
        # 30000 frames at 29.97 fps = exactly 1001 seconds
    """
    validate_fps_rational(fps_num, fps_den)
    
    if n_frames < 0:
        raise ValueError(f"Number of frames must be non-negative, got {n_frames}")
    
    if n_frames == 0:
        return Fraction(0)
    
    # duration = n_frames * (fps_den / fps_num)
    return Fraction(n_frames * fps_den, fps_num)


def validate_fps_rational(fps_num: int, fps_den: int) -> None:
    """
    Validate frame rate rational inputs.
    
    Args:
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Raises:
        ValueError: If inputs are invalid or frame rate is unreasonable
    """
    # Check types
    if not isinstance(fps_num, int):
        raise ValueError(f"Frame rate numerator must be integer, got {type(fps_num)}")
    
    if not isinstance(fps_den, int):
        raise ValueError(f"Frame rate denominator must be integer, got {type(fps_den)}")
    
    # Check positive values
    if fps_num <= 0:
        raise ValueError(f"Frame rate numerator must be positive, got {fps_num}")
    
    if fps_den <= 0:
        raise ValueError(f"Frame rate denominator must be positive, got {fps_den}")
    
    # Check reasonable range
    fps_value = fps_num / fps_den
    
    if fps_value < MIN_FRAME_RATE:
        raise ValueError(f"Frame rate out of reasonable range: {fps_value} fps "
                        f"(minimum: {MIN_FRAME_RATE} fps)")
    
    if fps_value >= MAX_FRAME_RATE:
        raise ValueError(f"Frame rate out of reasonable range: {fps_value} fps "
                        f"(maximum: {MAX_FRAME_RATE} fps)")


def format_time_rational(time_fraction: Fraction, precision: int = 6) -> str:
    """
    Format rational time for human display.
    
    Args:
        time_fraction: Time as Fraction
        precision: Decimal places for display
        
    Returns:
        Human-readable time string
    """
    if time_fraction.denominator == 1:
        return f"{time_fraction.numerator} seconds"
    else:
        decimal = float(time_fraction)
        return f"{decimal:.{precision}f} seconds ({time_fraction.numerator}/{time_fraction.denominator})"


def get_timing_info(fps_num: int, fps_den: int) -> dict:
    """
    Get comprehensive timing information for a frame rate.
    
    Args:
        fps_num: Frame rate numerator
        fps_den: Frame rate denominator
        
    Returns:
        Dictionary with timing information
    """
    validate_fps_rational(fps_num, fps_den)
    
    frame_duration = calculate_frame_duration(fps_num, fps_den)
    fps_decimal = fps_num / fps_den
    
    return {
        'fps_rational': (fps_num, fps_den),
        'fps_decimal': fps_decimal,
        'frame_duration_fraction': frame_duration,
        'frame_duration_seconds': float(frame_duration),
        'frames_per_minute': fps_decimal * 60,
        'frames_per_hour': fps_decimal * 3600,
        'milliseconds_per_frame': float(frame_duration) * 1000,
        'microseconds_per_frame': float(frame_duration) * 1000000,
    }


if __name__ == "__main__":
    # Demo usage
    print("Frame Timing Calculations Demo")
    print("=" * 40)
    
    # Test with common frame rates
    test_rates = [
        (24, 1),        # 24 fps cinema
        (25, 1),        # 25 fps PAL
        (30, 1),        # 30 fps
        (24000, 1001),  # 23.976 fps NTSC film
        (30000, 1001),  # 29.97 fps NTSC
        (60000, 1001),  # 59.94 fps NTSC HD
    ]
    
    for fps_num, fps_den in test_rates:
        fps_decimal = fps_num / fps_den
        print(f"\nFrame Rate: {fps_decimal:.6f} fps ({fps_num}/{fps_den})")
        
        # Frame duration
        duration = calculate_frame_duration(fps_num, fps_den)
        print(f"  Frame duration: {format_time_rational(duration)}")
        
        # Example frame timings
        for frame in [0, 1, 10, 100]:
            time = frame_to_seconds(frame, fps_num, fps_den)
            print(f"  Frame {frame:3d}: {format_time_rational(time, 3)}")
        
        # Round-trip test
        test_time = Fraction(5, 1)  # 5 seconds
        frame = seconds_to_frame(test_time, fps_num, fps_den)
        back_time = frame_to_seconds(frame, fps_num, fps_den)
        print(f"  Round-trip: {test_time}s → frame {frame} → {format_time_rational(back_time, 3)}")
    
    print("\nTiming precision test:")
    print("=" * 25)
    
    # Show precision difference between float and Fraction
    fps_num, fps_den = 30000, 1001
    frame_num = 1000
    
    # Exact rational calculation
    exact_time = frame_to_seconds(frame_num, fps_num, fps_den)
    exact_float = float(exact_time)
    
    # Float calculation (what most systems do)
    fps_float = fps_num / fps_den
    float_time = frame_num / fps_float
    
    error = abs(exact_float - float_time)
    print(f"Frame {frame_num} at {fps_num}/{fps_den} fps:")
    print(f"  Exact rational: {exact_time} = {exact_float:.15f} seconds")
    print(f"  Float calculation: {float_time:.15f} seconds")
    print(f"  Precision error: {error:.2e} seconds")
    print(f"  Error in microseconds: {error * 1e6:.3f} μs")