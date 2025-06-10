#!/usr/bin/env python3
"""
Python 3 compatibility smoke tests.

These tests verify that the basic functionality works correctly after
porting from Python 2 to Python 3.
"""

import sys
import os
import unittest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPython3Compatibility(unittest.TestCase):
    """Test that basic functionality works in Python 3"""
    
    def test_python3_imports(self):
        """Verify all modules import correctly in Python 3"""
        # These should not raise SyntaxError or ImportError
        import generate
        import video
        import audio
        import eventTimingGen
        
        # If we get here, imports worked
        self.assertTrue(True)
    
    def test_basic_functionality(self):
        """Verify basic functionality works in Python 3"""
        from generate import genEventCentreTimes, fpsBitTimings
        
        # Test that we can generate events (take only first 10 from infinite generator)
        events = []
        gen = genEventCentreTimes(4, 25)
        for i, event in enumerate(gen):
            if i >= 10:
                break
            events.append(event)
        
        self.assertGreater(len(events), 0, "Should generate some events")
        
        # Test that fpsBitTimings exists and has expected structure
        self.assertGreater(len(fpsBitTimings), 0, "fpsBitTimings should not be empty")
        
        # Test a specific frame rate
        self.assertIn(25, fpsBitTimings, "25 fps should be supported")
        self.assertIn(0, fpsBitTimings[25], "Zero bit timing should exist")
        self.assertIn(1, fpsBitTimings[25], "One bit timing should exist")
    
    def test_event_generation_works(self):
        """Test that event generation produces sensible results"""
        from generate import genEventCentreTimes
        
        # Take first 15 events from infinite generator
        events = []
        gen = genEventCentreTimes(seqBits=3, fps=25)
        for i, event in enumerate(gen):
            if i >= 15:
                break
            events.append(event)
        
        # Should have some events
        self.assertGreater(len(events), 0)
        
        # Events should be in ascending order
        for i in range(len(events) - 1):
            self.assertLess(events[i], events[i+1], 
                           "Events should be in ascending order")
        
        # All events should be non-negative
        self.assertTrue(all(e >= 0 for e in events), 
                       "All events should be non-negative")
    
    def test_video_module_functionality(self):
        """Test basic video module functionality"""
        from video import frameNumToTimecode
        
        # Test basic timecode generation
        timecode = frameNumToTimecode(0, 25)
        self.assertEqual(timecode, "00:00:00:00", "Frame 0 should be 00:00:00:00")
        
        timecode = frameNumToTimecode(25, 25)
        self.assertEqual(timecode, "00:00:01:00", "Frame 25 at 25fps should be 00:00:01:00")
    
    def test_audio_module_imports(self):
        """Test that audio module imports without issues"""
        import audio
        
        # Should have the expected functions
        self.assertTrue(hasattr(audio, 'genBeepSequence'), 
                       "audio module should have genBeepSequence")
        self.assertTrue(hasattr(audio, 'saveAsWavFile'), 
                       "audio module should have saveAsWavFile")


if __name__ == '__main__':
    unittest.main()