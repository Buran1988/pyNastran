import os
import unittest

import pyNastran
from pyNastran.gui.testing_methods import FakeGUIMethods
from pyNastran.converters.panair.panair_io import PanairIO
from pyNastran.utils.log import get_logger

PKG_PATH = pyNastran.__path__[0]
MODEL_PATH = os.path.join(PKG_PATH, 'converters', 'panair', 'M100')


class PanairGUI(PanairIO, FakeGUIMethods):
    def __init__(self):
        FakeGUIMethods.__init__(self)
        PanairIO.__init__(self)


class TestPanairGUI(unittest.TestCase):

    def test_m100_geometry(self):
        log = get_logger(level='warning')
        geometry_filename = os.path.join(MODEL_PATH, 'M100.inp')
        #agps_filename = os.path.join(MODEL_PATH, 'agps')
        #out_filename = os.path.join(MODEL_PATH, 'panair.out')

        test = PanairGUI()
        test.log = log
        test.load_panair_geometry(geometry_filename)

    def test_m100_results(self):
        log = get_logger(level='warning')
        geometry_filename = os.path.join(MODEL_PATH, 'M100.inp')
        agps_filename = os.path.join(MODEL_PATH, 'agps')
        out_filename = os.path.join(MODEL_PATH, 'panair.out')

        test = PanairGUI()
        test.log = log
        test.load_panair_geometry(geometry_filename)
        test.load_panair_results(agps_filename)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
