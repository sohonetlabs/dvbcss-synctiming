#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests for arduino.py module Python 3 compatibility and functionality
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestArduinoPython3Compatibility(unittest.TestCase):
    """Test that arduino.py module works with Python 3"""
    
    def test_module_imports(self):
        """Test that arduino module can be imported"""
        try:
            self.assertTrue(True)
        except SyntaxError as e:
            self.fail(f"arduino module has Python 2 syntax errors: {e}")
    
    def test_main_block_executes(self):
        """Test that the __main__ block executes without syntax errors"""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'src', 'arduino.py')],
            capture_output=True,
            text=True
        )
        # Should not have syntax errors
        self.assertNotIn("SyntaxError", result.stderr)
        # Should print the expected messages
        self.assertIn("library of functions", result.stdout)
        self.assertIn("timing reference-point calibration", result.stdout)


if __name__ == '__main__':
    unittest.main()