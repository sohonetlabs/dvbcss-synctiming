# Fractional Frame Rate Support for DVB CSS Synchronization Timing

This directory contains the enhanced test sequence generator with support for fractional frame rates commonly used in broadcast and cinema applications.

## Quick Start

```bash
# Generate test sequence at 23.976 fps (NTSC film rate)
python src/generate_fractional.py --fps-ntsc-film --duration 10

# Generate 1080p at 59.94 fps
python src/generate_fractional.py --preset-1080p59.94 --duration 5

# Generate DCI 4K at 24 fps
python src/generate_fractional.py --preset-cinema-4k --duration 10
```

## Features

### Fractional Frame Rates
- **23.976 fps** (24000/1001) - NTSC film rate
- **29.97 fps** (30000/1001) - NTSC video
- **59.94 fps** (60000/1001) - NTSC HD
- **119.88 fps** (120000/1001) - NTSC 4K/8K

### Broadcast Shortcuts
- `--fps-ntsc-film` - 23.976 fps
- `--fps-ntsc` - 29.97 fps
- `--fps-ntsc-hd` - 59.94 fps
- `--fps-pal` - 25 fps
- `--fps-pal-hd` - 50 fps
- `--fps-film` - 24 fps

### Resolution Presets
- `--size-4k-full` - 4096x2160 (DCI 4K)
- `--size-hd-1080` - 1920x1080 (Full HD)
- `--size-uhd-4k` - 3840x2160 (UHD 4K)
- `--size-2k-scope` - 2048x858 (Cinemascope)

### Complete Format Presets
- `--preset-1080p59.94` - 1080p at 59.94 fps
- `--preset-cinema-4k` - DCI 4K at 24 fps
- `--preset-ntsc-sd` - NTSC Standard Definition

## Usage Examples

### Basic Usage
```bash
# Decimal frame rate
python src/generate_fractional.py --fps 23.976 --duration 10

# Rational frame rate
python src/generate_fractional.py --fps 24000/1001 --duration 10

# Integer frame rate (backward compatible)
python src/generate_fractional.py --fps 25 --duration 10
```

### Professional Workflows
```bash
# Cinema workflow: DCI 4K at 23.976 fps
python src/generate_fractional.py --fps-ntsc-film --size-4k-full \
    --title "Cinema Test" --duration 10

# Broadcast workflow: 1080i at 59.94 fields/second
python src/generate_fractional.py --fps-ntsc --size-hd-1080 --fields \
    --title "Broadcast Test" --duration 10

# High frame rate: 4K at 119.88 fps
python src/generate_fractional.py --fps-ntsc-4k --size-uhd-4k \
    --title "HFR Test" --duration 5
```

### Custom Output Paths
```bash
python src/generate_fractional.py --preset-1080p59.94 \
    --frame-filename output/frames/frame_%06d.png \
    --wav-filename output/audio/test.wav \
    --metadata-filename output/metadata.json \
    --duration 10
```

## Technical Details

### Exact Rational Arithmetic
All timing calculations use Python's `fractions.Fraction` for exact precision:
- No floating-point rounding errors
- Frame-accurate synchronization
- Sample-accurate audio generation

### Bit Timing Design and Base FPS

The fractional frame rate implementation uses a "base fps" concept for bit timing patterns to maintain compatibility with existing detection systems:

#### Base FPS Mapping
```python
23.976 fps (24000/1001) → uses 24 fps base timing
29.97 fps (30000/1001)  → uses 30 fps base timing
59.94 fps (60000/1001)  → uses 30 fps base timing
```

#### Why Base FPS?
1. **Detection Compatibility**: Same detection algorithms work across frame rate families
2. **Hardware Consistency**: No need for rate-specific calibration 
3. **Pattern Recognition**: Broadcast equipment expects consistent timing patterns

#### Example: 29.97 fps Timing
```python
# Uses 30 fps base, so bit timings are:
zero_bit = 3.5/30 = 7/60 = 0.1167 seconds
one_bit_1 = 3.5/30 = 7/60 = 0.1167 seconds  
one_bit_2 = 9.5/30 = 19/60 = 0.3167 seconds

# At 29.97 fps frame rate:
# Zero bit occurs at frame position: 0.1167 × (30000/1001) ≈ 3.496
# Flash appears in middle of frame 3 (3.5 frames from start)
```

This ensures that detection hardware designed for 30 fps also works perfectly with 29.97 fps content.

📊 **See TIMING_DIAGRAMS.md for detailed visual diagrams and timing charts.**

### Metadata Format
The generated `metadata.json` includes:
- Original fields for backward compatibility (`fps`, `size`, `durationSecs`)
- New fractional fields (`fps_rational`, `frame_duration_exact`)
- Timing precision indicator (`timing_precision: "exact_rational"`)

### File Structure
```
test_sequence_gen/
├── src/
│   ├── generate_fractional.py      # Main CLI tool
│   ├── frame_rate_parser.py        # Parse fractional rates
│   ├── frame_timing.py             # Exact timing calculations
│   ├── fractional_event_generation.py  # Event generation
│   └── cli_fractional_integration.py   # CLI argument parsing
├── tests/
│   └── test_*.py                   # Comprehensive test suite
└── demo_fractional.py              # Interactive demo
```

## Requirements
- Python 3.6+
- Pillow (PIL) for image generation
- NumPy for audio generation

## Testing
The implementation includes 168+ tests using pytest and Hypothesis:
```bash
pytest tests/
```

## Default Output
By default, files are saved to:
- `build/audio.wav` - Audio file
- `build/img_%06d.png` - Frame images
- `build/metadata.json` - Metadata file

Directories are created automatically if they don't exist.