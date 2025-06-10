"""
pytest configuration and fixtures for test_sequence_gen tests.

This file configures Hypothesis settings and provides common fixtures
for testing the test sequence generation functionality.
"""

import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis for thorough testing
settings.register_profile("default", 
                         max_examples=100,
                         verbosity=Verbosity.normal,
                         deadline=None)  # No deadline for long-running property tests

settings.register_profile("ci", 
                         max_examples=50,
                         verbosity=Verbosity.quiet,
                         deadline=5000)  # 5 second deadline for CI

settings.register_profile("debug", 
                         max_examples=10,
                         verbosity=Verbosity.verbose,
                         deadline=None)

# Use default profile
settings.load_profile("default")

# Common test fixtures can be added here
@pytest.fixture
def supported_fps_rates():
    """Fixture providing the currently supported integer frame rates."""
    return [24, 25, 30, 48, 50, 60]

@pytest.fixture  
def small_sequence_bits():
    """Fixture providing small sequence bit lengths for fast testing."""
    return [3, 4, 5]

@pytest.fixture
def test_duration_short():
    """Fixture providing short durations for fast testing."""
    return 2  # 2 seconds