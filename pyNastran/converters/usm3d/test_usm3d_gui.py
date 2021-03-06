"""
tests Usm3d
"""
import os
import unittest

import pyNastran
from pyNastran.gui.testing_methods import FakeGUIMethods
#from pyNastran.bdf.bdf import BDF
from pyNastran.converters.usm3d.usm3d_io import Usm3dIO
from pyNastran.utils.log import get_logger


PKG_PATH = pyNastran.__path__[0]
MODEL_PATH = os.path.join(PKG_PATH, 'converters', 'usm3d', 'box')


class Usm3dGUI(Usm3dIO, FakeGUIMethods):
    def __init__(self):
        FakeGUIMethods.__init__(self)
        Usm3dIO.__init__(self)


class TestUsm3dGUI(unittest.TestCase):

    def test_usm3d_geometry_01(self):
        """tests the box.cogwg/box.flo turbulent model"""
        log = get_logger(level='error', encoding='utf-8')
        geometry_filename = os.path.join(MODEL_PATH, 'box.cogsg')
        flo_filename = os.path.join(MODEL_PATH, 'box.flo')

        test = Usm3dGUI()
        test.log = log
        test.load_usm3d_geometry(geometry_filename)
        test.load_usm3d_results(flo_filename)
        test.on_reload_usm3d()

        test.load_usm3d_geometry(geometry_filename)
        test.load_usm3d_results(flo_filename)
        test.on_reload_usm3d()

if __name__ == '__main__':  # pragma: no cover
    unittest.main()

