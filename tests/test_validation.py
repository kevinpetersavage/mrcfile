# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
Tests for mrcfile __init__.py validate function.
"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import os
import shutil
import tempfile
import unittest
import warnings

import numpy as np

import mrcfile
from . import helpers


class ValidationTest(helpers.AssertRaisesRegexMixin, unittest.TestCase):
    
    """Unit tests for MRC validation function.
    
    """
    
    def setUp(self):
        super(ValidationTest, self).setUp()
        
        # Set up test files and names to be used
        self.test_data = helpers.get_test_data_path()
        self.test_output = tempfile.mkdtemp()
        self.temp_mrc_name = os.path.join(self.test_output, 'test_mrcfile.mrc')
        self.example_mrc_name = os.path.join(self.test_data, 'EMD-3197.map')
        self.gzip_mrc_name = os.path.join(self.test_data, 'emd_3197.map.gz')
        self.bzip2_mrc_name = os.path.join(self.test_data, 'EMD-3197.map.bz2')
        self.ext_header_mrc_name = os.path.join(self.test_data, 'EMD-3001.map')
        
        # Set up stream to catch print output from validate()
        self.print_stream = io.StringIO()
    
    def tearDown(self):
        self.print_stream.close()
        if os.path.exists(self.test_output):
            shutil.rmtree(self.test_output)
        super(ValidationTest, self).tearDown()
    
    def test_good_file(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(36, dtype=np.float32).reshape(3, 3, 4))
            mrc.voxel_size = 2.3
        result = mrcfile.validate(self.temp_mrc_name, self.print_stream)
        assert result == True
        print_output = self.print_stream.getvalue()
        assert len(print_output) == 0
    
    def test_emdb_file(self):
        result = mrcfile.validate(self.example_mrc_name, self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert print_output.strip() == ("File does not declare MRC format "
                                        "version 20140: nversion = 0")
    
    def test_gzip_emdb_file(self):
        result = mrcfile.validate(self.gzip_mrc_name, self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert print_output.strip() == ("File does not declare MRC format "
                                        "version 20140: nversion = 0")
    
    def test_bzip2_emdb_file(self):
        result = mrcfile.validate(self.bzip2_mrc_name, self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert print_output.strip() == ("File does not declare MRC format "
                                        "version 20140: nversion = 0")
    
    def test_emdb_cryst_file(self):
        result = mrcfile.validate(self.ext_header_mrc_name, self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert print_output.strip() == ("File does not declare MRC format "
                                        "version 20140: nversion = 0\n"
                                        "Extended header type is undefined or "
                                        "unrecognised: exttyp = ''")
    
    def check_temp_mrc_invalid_with_warning(self, message):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = mrcfile.validate(self.temp_mrc_name,
                                      print_file=self.print_stream)
            assert result == False
            print_output = self.print_stream.getvalue()
            assert message.lower() in print_output.lower()
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert message in str(w[0].message)
    
    def test_incorrect_map_id(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.map = b'fake'
        self.check_temp_mrc_invalid_with_warning("Map ID string")
    
    def test_incorrect_machine_stamp(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.machst = bytearray(b'    ')
        self.check_temp_mrc_invalid_with_warning("machine stamp")
    
    def test_invalid_mode(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(12, dtype=np.float32).reshape(1, 3, 4))
            mrc.header.mode = 8
        self.check_temp_mrc_invalid_with_warning("mode")
    
    def test_file_too_small(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(12, dtype=np.float32).reshape(1, 3, 4))
            mrc.header.nz = 2
        self.check_temp_mrc_invalid_with_warning("data block")
    
    def test_file_too_large(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(36, dtype=np.float32).reshape(3, 3, 4))
            mrc.header.nz = 2
        self.check_temp_mrc_invalid_with_warning("larger than expected")
    
    def test_negative_mx(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.mx = -10
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Header field 'mx' is negative" in print_output
    
    def test_negative_my(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.my = -10
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Header field 'my' is negative" in print_output
    
    def test_negative_mz(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.mz = -10
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Header field 'mz' is negative" in print_output
    
    def test_negative_ispg(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.ispg = -10
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Header field 'ispg' is negative" in print_output
    
    def test_negative_nlabl(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.nlabl = -3
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Header field 'nlabl' is negative" in print_output
    
    def test_negative_cella_x(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.cella.x = -10
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Cell dimension 'x' is negative" in print_output
    
    def test_invalid_axis_mapping(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.mapc = 3
            mrc.header.mapr = 4
            mrc.header.maps = -200
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Invalid axis mapping: found [-200, 3, 4]" in print_output
    
    def test_mz_correct_for_volume_stack(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(120, dtype=np.float32).reshape(3, 2, 4, 5))
        with warnings.catch_warnings(record=True):
            result = mrcfile.validate(self.temp_mrc_name,
                                      print_file=self.print_stream)
            assert result == True
    
    def test_mz_incorrect_for_volume_stack(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(np.arange(120, dtype=np.float32).reshape(3, 2, 4, 5))
            mrc.header.mz = 5
        with warnings.catch_warnings(record=True):
            result = mrcfile.validate(self.temp_mrc_name,
                                      print_file=self.print_stream)
            assert result == False
            print_output = self.print_stream.getvalue()
            assert ("Error in dimensions for volume stack: nz should be "
                    "divisible by mz. Found nz = 6, mz = 5" in print_output)
    
    def test_nlabl_too_large(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.label[1] = 'test label'
            mrc.header.nlabl = 3
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in header labels: "
                "nlabl is 3 but 2 labels contain text" in print_output)
    
    def test_nlabl_too_small(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.label[1] = 'test label'
            mrc.header.nlabl = 1
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in header labels: "
                "nlabl is 1 but 2 labels contain text" in print_output)
    
    def test_empty_labels_in_list(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.label[2] = 'test label'
            mrc.header.nlabl = 2
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in header labels: empty labels appear between "
                "text-containing labels" in print_output)
    
    def test_incorrect_format_version(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.header.nversion = 20139
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "File does not declare MRC format version 20140" in print_output
    
    def test_missing_exttyp(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_extended_header(np.arange(10))
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Extended header type is undefined or unrecognised" in print_output
    
    def test_unknown_exttyp(self):
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_extended_header(np.arange(10))
            mrc.header.exttyp = 'Fake'
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert "Extended header type is undefined or unrecognised" in print_output
    
    def test_incorrect_rms(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.rms = 9.0
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in data statistics: RMS deviation is {0} but the value "
                "in the header is 9.0".format(data.std()) in print_output)
    
    def test_rms_undetermined(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.rms = -15
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == True
    
    def test_incorrect_dmin(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmin = -11
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in data statistics: minimum is {0} but the value "
                "in the header is -11".format(data.min()) in print_output)
    
    def test_incorrect_dmax(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmax = 15
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in data statistics: maximum is {0} but the value "
                "in the header is 15".format(data.max()) in print_output)
    
    def test_min_and_max_undetermined(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmin = 30.1
            mrc.header.dmax = 30.0
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == True
    
    def test_incorrect_dmean(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmean = -2.5
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in data statistics: mean is {0} but the value "
                "in the header is -2.5".format(data.mean()) in print_output)
    
    def test_incorrect_dmean_with_undetermined_dmin_and_dmax(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmin = 20
            mrc.header.dmax = -30.1
            mrc.header.dmean = -2.5
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == False
        print_output = self.print_stream.getvalue()
        assert ("Error in data statistics: mean is {0} but the value "
                "in the header is -2.5".format(data.mean()) in print_output)
    
    def test_mean_undetermined(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmean = -11
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == True
    
    def test_min_max_and_mean_undetermined(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(2, 3, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.header.dmin = 30.1
            mrc.header.dmax = 30.0
            mrc.header.dmean = 29.9
        result = mrcfile.validate(self.temp_mrc_name,
                                  print_file=self.print_stream)
        assert result == True
    
    def test_many_problems_simultaneously(self):
        data = np.arange(-10, 20, dtype=np.float32).reshape(3, 2, 5)
        with mrcfile.new(self.temp_mrc_name) as mrc:
            mrc.set_data(data)
            mrc.set_extended_header(data)
            mrc.header.nz = 2
            mrc.header.my = -1000
            mrc.header.mz = -5
            mrc.header.cella.y = -12.1
            mrc.header.mapc = 5
            mrc.header.dmin = 10
            mrc.header.dmax = 11
            mrc.header.dmean = 19.0
            mrc.header.ispg = -20
            mrc.header.exttyp = 'fake'
            mrc.header.nversion = 0
            mrc.header.rms = 0.0
            mrc.header.nlabl = 4
            mrc.header.label[9] = 'test label'
        with warnings.catch_warnings(record=True):
            result = mrcfile.validate(self.temp_mrc_name,
                                      print_file=self.print_stream)
            assert result == False
            print_output = self.print_stream.getvalue()
            assert len(print_output.split('\n')) == 15


if __name__ == '__main__':
    unittest.main()
