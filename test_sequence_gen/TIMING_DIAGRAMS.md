# Bit Timing Diagrams for Fractional Frame Rates

This document provides visual diagrams to illustrate the bit timing design and base fps concept.

## Frame Rate Comparison: 30.00 fps vs 29.97 fps

### Timeline Diagram
```
Time (seconds):  0.000   0.033   0.067   0.100   0.133   0.167   0.200   0.233   0.267   0.300   0.333
                   |       |       |       |       |       |       |       |       |       |       |

30.00 fps frames: [Frame0][Frame1][Frame2][Frame3][Frame4][Frame5][Frame6][Frame7][Frame8][Frame9][Frame10]
                     ^       ^       ^       ^       ^       ^       ^       ^       ^       ^       ^
                   0.000   0.033   0.067   0.100   0.133   0.167   0.200   0.233   0.267   0.300   0.333

29.97 fps frames: [Frame0 ][Frame1 ][Frame2 ][Frame3 ][Frame4 ][Frame5 ][Frame6 ][Frame7 ][Frame8 ][Frame9 ]
                     ^        ^        ^        ^        ^        ^        ^        ^        ^        ^
                   0.000    0.0334   0.0667   0.1001   0.1334   0.1668   0.2001   0.2335   0.2668   0.3002

Bit Timing (Base): 
Zero bit flash:                              ●
One bit flash 1:                             ●
One bit flash 2:                                                                                     ●
                                          0.1167                                                   0.3167
```

### Key Observations
- **Same absolute timing**: Both frame rates use identical bit timing positions (0.1167s, 0.3167s)
- **Different frame alignment**: Flashes occur at slightly different frame positions
- **Detection compatibility**: Hardware sees the same timing pattern regardless of frame rate

## Bit Timing Pattern Details

### Zero Bit Pattern
```
Base FPS = 30
Zero bit timing = 3.5/30 = 7/60 = 0.11666... seconds

30.00 fps:                29.97 fps:
Frame:  0  1  2  3  4     Frame:  0  1  2  3  4
Time: |--+--+--+--+--|   Time: |--+--+--+--+--|
      0 .033.067.100.133        0 .033.067.100.133
             ●                           ●
         (Frame 3.5)                (Frame 3.496)
```

### One Bit Pattern  
```
Base FPS = 30
One bit timing 1 = 3.5/30 = 7/60 = 0.11666... seconds
One bit timing 2 = 9.5/30 = 19/60 = 0.31666... seconds

30.00 fps:                              29.97 fps:
Frame:  0  1  2  3  4  5  6  7  8  9    Frame:  0  1  2  3  4  5  6  7  8  9
Time: |--+--+--+--+--+--+--+--+--+--|  Time: |--+--+--+--+--+--+--+--+--+--|
      0    .1   .2   .3   .4            0    .1   .2   .3   .4
             ●                 ●                   ●                 ●
         (Frame 3.5)     (Frame 9.5)         (Frame 3.496)   (Frame 9.49)
```

## Frame Alignment Comparison

### Exact Frame Positioning
```
Frame Rate: 30.00 fps (exact)
Frame duration: 1/30 = 0.033333... seconds

Frame boundaries:    0.000   0.033   0.067   0.100   0.133   0.167
Frame numbers:         0       1       2       3       4       5
Zero bit at 0.1167:                            ●
Frame position:                             3.500 (exact center)


Frame Rate: 29.97 fps (30000/1001)  
Frame duration: 1001/30000 = 0.033367... seconds

Frame boundaries:    0.000   0.033   0.067   0.100   0.134   0.167
Frame numbers:         0       1       2       3       4       5  
Zero bit at 0.1167:                            ●
Frame position:                             3.496 (slightly off-center)

Difference: 0.004 frames = 0.13 milliseconds (negligible for detection)
```

## Base FPS Mapping Diagram

### NTSC Frame Rate Family (1001 denominator)
```
Exact Frame Rate        Base FPS Used       Bit Timing Calculation
┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 23.976 fps      │───▶│ 24 fps base │────▶│ 3.5/24 = 0.1458s     │
│ (24000/1001)    │    │             │     │ 9.5/24 = 0.3958s     │
└─────────────────┘    └─────────────┘     └──────────────────────┘

┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 29.97 fps       │───▶│ 30 fps base │────▶│ 3.5/30 = 0.1167s     │
│ (30000/1001)    │    │             │     │ 9.5/30 = 0.3167s     │
└─────────────────┘    └─────────────┘     └──────────────────────┘

┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 59.94 fps       │───▶│ 30 fps base │────▶│ 3.5/30 = 0.1167s     │
│ (60000/1001)    │    │ (same as 60)│     │ 9.5/30 = 0.3167s     │
└─────────────────┘    └─────────────┘     └──────────────────────┘
```

### PAL/Film Frame Rate Family
```
Exact Frame Rate        Base FPS Used       Bit Timing Calculation
┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 24 fps          │───▶│ 24 fps base │────▶│ 3.5/24 = 0.1458s     │
│ (24/1)          │    │             │     │ 9.5/24 = 0.3958s     │
└─────────────────┘    └─────────────┘     └──────────────────────┘

┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 25 fps          │───▶│ 25 fps base │────▶│ 3.5/25 = 0.14s       │
│ (25/1)          │    │             │     │ 9.5/25 = 0.38s       │
└─────────────────┘    └─────────────┘     └──────────────────────┘

┌─────────────────┐    ┌─────────────┐     ┌──────────────────────┐
│ 50 fps          │───▶│ 25 fps base │────▶│ 3.5/25 = 0.14s       │
│ (50/1)          │    │ (same as 25)│     │ 9.5/25 = 0.38s       │
└─────────────────┘    └─────────────┘     └──────────────────────┘
```

## Detection Window Analysis

### Hardware Detection Tolerance
```
Expected Zero Bit Time: 0.1167 seconds (7/60)
Detection Window: ±5ms (typical hardware tolerance)

Detection Window:    0.1117s ◄────────────────► 0.1217s
                            │        ●        │
                            └── 0.1167s ──────┘
                          (Target time)

30.00 fps flash:           ●                    ✓ DETECTED
29.97 fps flash:           ●                    ✓ DETECTED  
28.00 fps (hypothetical):  ●                    ✓ DETECTED
32.00 fps (hypothetical):  ●                    ✓ DETECTED

All frame rates in the 30 fps family are detected reliably!
```

## Mathematical Precision Diagram

### Rational Arithmetic vs Floating Point
```
Frame Rate: 29.97 fps (30000/1001)

Exact Rational Calculation:
├─ Frame duration = Fraction(1001, 30000)
├─ 100 frames = 100 × 1001/30000 = 100100/30000 = 3.3366666... seconds
└─ Zero bit timing = Fraction(7, 60) = 0.11666666... seconds (exact)

Floating Point Calculation (what most systems do):
├─ Frame duration = 30000/1001 ≈ 0.033366666666667
├─ 100 frames = 100 × 0.033366666666667 ≈ 3.3366666666667
└─ Accumulated error after many calculations ≈ microseconds

Precision Advantage:
┌──────────────────┐     ┌──────────────────┐
│ Floating Point   │ vs  │ Rational Math    │
├──────────────────┤     ├──────────────────┤
│ ~15 digits       │     │ Infinite digits  │
│ Rounding errors  │     │ Exact precision  │
│ Error accumulation│     │ No drift         │
└──────────────────┘     └──────────────────┘
```

## Broadcast Workflow Diagram

### Production to Measurement Flow
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Content       │    │  Test Sequence   │    │   Measurement   │
│   Production    │    │   Generator      │    │     Device      │
│                 │    │                  │    │                 │
│ • 29.97 fps     │───▶│ • Same fps       │───▶│ • Detects at    │
│ • Broadcast     │    │ • Base fps timing│    │   base fps      │
│   timing        │    │ • Flash/beep     │    │   intervals     │
│                 │    │   patterns       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                           │
                              ▼                           ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │ Exact rational   │    │ Hardware looks  │
                    │ timing calc:     │    │ for flashes at: │
                    │ • 7/60 seconds   │    │ • 0.1167s ±5ms  │
                    │ • 19/60 seconds  │    │ • 0.3167s ±5ms  │
                    └──────────────────┘    └─────────────────┘
```

## Implementation Architecture Diagram

### Module Relationships
```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface                            │
│  generate_fractional.py --fps-ntsc --duration 10           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Frame Rate Parser                              │
│  "29.97" → (30000, 1001) → base_fps = 30                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│             Bit Timing Generator                            │
│  base_fps = 30 → timings = {0: [7/60], 1: [7/60, 19/60]}  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            Event Sequence Generator                         │
│  MLS sequence + bit timings → event times (Fractions)      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Flash/Beep Sequence Generator                       │
│  event times + frame rate → flash/beep patterns            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Output Generation                              │
│  PNG frames (29.970 fps) + WAV audio + JSON metadata       │
└─────────────────────────────────────────────────────────────┘
```

This visual documentation helps explain why the base fps approach maintains compatibility while providing exact timing for fractional frame rates.