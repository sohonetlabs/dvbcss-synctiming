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
Tests for tuple unpacking fixes in detect.py
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestTupleUnpackingFixes(unittest.TestCase):
    """Test that tuple unpacking is fixed for Python 3 compatibility"""
    
    def test_convert_a_to_b_initialization(self):
        """Test ConvertAtoB can be initialized with tuple arguments"""
        from detect import ConvertAtoB
        
        # Test basic initialization
        converter = ConvertAtoB((0, 50), (10, 70))
        self.assertIsNotNone(converter)
        
        # Test the conversion works as expected
        self.assertAlmostEqual(converter(0), 50.0)
        self.assertAlmostEqual(converter(5), 60.0)
        self.assertAlmostEqual(converter(10), 70.0)
        
        # Test extrapolation
        self.assertAlmostEqual(converter(15), 80.0)
        self.assertAlmostEqual(converter(-5), 40.0)
    
    def test_error_bound_interpolator_initialization(self):
        """Test ErrorBoundInterpolator can be initialized with tuple arguments"""
        from detect import ErrorBoundInterpolator
        
        # Test basic initialization
        interpolator = ErrorBoundInterpolator((0, 1.0), (10, 2.0))
        self.assertIsNotNone(interpolator)
        
        # Test interpolation works
        self.assertAlmostEqual(interpolator(0), 1.0)
        self.assertAlmostEqual(interpolator(10), 2.0)
        self.assertAlmostEqual(interpolator(5), 1.5)
        
        # Test bounds checking
        with self.assertRaises(ValueError):
            interpolator(-1)  # Below lower bound
        
        with self.assertRaises(ValueError):
            interpolator(11)  # Above upper bound
        
        # Test invalid initialization (v1 >= v2)
        with self.assertRaises(ValueError):
            ErrorBoundInterpolator((10, 1.0), (10, 2.0))
        
        with self.assertRaises(ValueError):
            ErrorBoundInterpolator((10, 1.0), (5, 2.0))


if __name__ == '__main__':
    unittest.main()