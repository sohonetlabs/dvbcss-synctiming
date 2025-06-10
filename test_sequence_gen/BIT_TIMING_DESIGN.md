# Bit Timing Design for Fractional Frame Rates

This document explains the technical design decisions behind bit timing patterns in the DVB CSS synchronization timing measurement system, particularly for fractional frame rates.

## Overview

The system generates test sequences with embedded timing patterns (flashes and beeps) that allow measurement devices to detect synchronization accuracy. These patterns must be detectable across different frame rates while maintaining precise timing.

## Historical Context: Integer Frame Rates

The original system used simple timing patterns based on integer frame rates:

```python
# Original fpsBitTimings structure
fpsBitTimings = {
    25: { 0: [3.5/25],           # Zero bit: pulse at 3.5/25 = 0.14 seconds
          1: [3.5/25, 9.5/25] }, # One bit: pulses at 0.14s and 0.38s
    30: { 0: [3.5/30],           # Zero bit: pulse at 3.5/30 = 0.1167 seconds  
          1: [3.5/30, 9.5/30] }, # One bit: pulses at 0.1167s and 0.3167s
    60: { 0: [3.5/30],           # 60 fps uses 30 fps base!
          1: [3.5/30, 9.5/30] }, # Same timings as 30 fps
}
```

**Key Observation**: Even in the original design, 60 fps used the same timings as 30 fps. This established the "base fps" concept.

## Design Challenge: Fractional Frame Rates

When adding fractional frame rates like 29.97 fps (30000/1001), we faced a choice:

### Option 1: Exact Fractional Timing (Not Used)
```python
# Calculate exact timings based on fractional frame rate
frame_duration = 1001/30000  # ≈ 0.03337 seconds
zero_timing = 3.5 * frame_duration = 3.5 * 1001/30000 = 7007/60000 seconds
```

**Problems with this approach:**
- Different timing patterns for each fractional rate
- Detection algorithms would need rate-specific calibration
- Hardware compatibility issues
- More complex pattern recognition

### Option 2: Base FPS Timing (Adopted)
```python
# Use base fps for timing calculations
base_fps = 30  # For 29.97 fps family
zero_timing = 3.5 / base_fps = 3.5/30 = 7/60 seconds
```

**Benefits of this approach:**
- Consistent patterns across frame rate families
- Hardware compatibility maintained
- Simple detection algorithms
- Proven broadcast engineering practice

## Base FPS Mapping Rules

The mapping from fractional frame rates to base fps follows these rules:

```python
def determine_base_fps(fps_num, fps_den):
    fps_decimal = fps_num / fps_den
    
    if abs(fps_decimal - 23.976) < 0.1:  # 24000/1001
        return 24
    elif abs(fps_decimal - 29.97) < 0.1:  # 30000/1001  
        return 30
    elif abs(fps_decimal - 47.952) < 0.1: # 48000/1001
        return 24  # Uses 24 fps base like 48 fps
    elif abs(fps_decimal - 59.94) < 0.1:  # 60000/1001
        return 30  # Uses 30 fps base like 60 fps
    elif abs(fps_decimal - 119.88) < 0.1: # 120000/1001
        return 30  # Uses 30 fps base like 120 fps
    else:
        # For other rates, use closest base
        return round(fps_decimal)
```

## Mathematical Example: 29.97 fps

Let's trace through a complete example:

### 1. Base FPS Determination
- Input: 29.97 fps (30000/1001)
- Base FPS: 30

### 2. Bit Timing Calculation  
```python
# Standard bit positions: 3.5 and 9.5 frame units
zero_timing = 3.5 / 30 = 7/60 = 0.11666... seconds
one_timing_1 = 3.5 / 30 = 7/60 = 0.11666... seconds
one_timing_2 = 9.5 / 30 = 19/60 = 0.31666... seconds
```

### 3. Frame Alignment
```python
# Frame duration at 29.97 fps
frame_duration = 1001/30000 ≈ 0.033367 seconds

# Zero bit position in frame units
frame_position = 0.11666... / 0.033367 ≈ 3.496 frames

# The flash appears at the center of frame 3 (3.5 frames from start)
```

### 4. Timing Verification
```python
# At exactly 30.00 fps:
frame_duration_30 = 1/30 ≈ 0.033333 seconds
frame_position_30 = 0.11666... / 0.033333 = 3.5 frames exactly

# At 29.97 fps:
frame_duration_2997 = 1001/30000 ≈ 0.033367 seconds  
frame_position_2997 = 0.11666... / 0.033367 ≈ 3.496 frames

# Difference: 0.004 frames (0.13ms) - negligible for detection
```

## Detection Compatibility

### Hardware Perspective
Detection hardware looks for:
1. **Flash patterns** at specific absolute times (0.1167s, 0.3167s, etc.)
2. **Consistent intervals** between patterns
3. **Predictable repetition** of the sequence

The base fps approach ensures all three criteria are met regardless of whether content is 30.00 fps or 29.97 fps.

### Software Perspective
Detection algorithms can use the same thresholds and timing windows:

```python
# Detection window for zero bit (same for both rates)
expected_time = 7/60  # 0.1167 seconds
tolerance = 0.005     # ±5ms window

# Works for both:
# - 30.00 fps: flash at exactly 0.1167s  
# - 29.97 fps: flash at exactly 0.1167s (different frame position)
```

## Alternative Approaches Considered

### 1. Proportional Scaling
Scale all timings proportionally with frame rate:
```python
scaling_factor = actual_fps / base_fps
adjusted_timing = base_timing * scaling_factor
```
**Rejected**: Creates rate-specific patterns, breaks compatibility.

### 2. Hybrid Approach  
Use base fps for detection, exact fps for generation:
```python
detection_timing = base_timing
generation_timing = exact_timing  
```
**Rejected**: Complexity without significant benefit.

### 3. Configurable Base
Allow users to choose base fps:
```python
--base-fps 30 --actual-fps 29.97
```
**Rejected**: User complexity, potential for misconfiguration.

## Implementation Details

### Current Implementation
```python
def createFpsBitTimingsFractional(fps_num: int, fps_den: int) -> dict:
    base_fps = determine_base_fps(fps_num, fps_den)
    
    return {
        0: [Fraction(35, 10 * base_fps)],  # 3.5 / base_fps
        1: [Fraction(35, 10 * base_fps),   # 3.5 / base_fps  
            Fraction(95, 10 * base_fps)]   # 9.5 / base_fps
    }
```

### Fraction Simplification
The timings are stored as simplified fractions:
```python
# 3.5/30 = 7/60 (automatically simplified)
# 9.5/30 = 19/60 (automatically simplified)
```

This maintains exact precision while using the most reduced form.

## Testing and Verification

### Mathematical Verification
The `test_math_verification.py` test suite verifies:
- ✅ Bit timings follow base fps rules
- ✅ Frame alignment is accurate  
- ✅ Pattern detection is consistent
- ✅ No precision loss in calculations

### Real-World Testing
Broadcast professionals should verify:
- Detection accuracy across equipment
- Timing measurement precision
- Compatibility with existing workflows
- Performance in various content types

## Conclusion

The base fps approach for bit timing provides:

1. **Backward Compatibility**: Existing detection systems work unchanged
2. **Engineering Simplicity**: One algorithm handles multiple frame rates  
3. **Broadcast Standards**: Follows established industry practices
4. **Mathematical Precision**: Exact rational arithmetic throughout
5. **Future Flexibility**: Easy to extend to new fractional rates

This design ensures that the DVB CSS synchronization timing system can accurately measure sync performance across the full range of modern broadcast frame rates while maintaining compatibility with existing infrastructure.