import os
import unittest

from pyNastran.gui.testing_methods import FakeGUIMethods
from pyNastran.converters.shabp.shabp_io import ShabpIO
from pyNastran.utils.log import get_logger
import pyNastran

pkg_path = pyNastran.__path__[0]
model_path = os.path.join(pkg_path, 'converters', 'shabp')


class ShabpGUI(ShabpIO, FakeGUIMethods):
    def __init__(self):
        FakeGUIMethods.__init__(self)
        ShabpIO.__init__(self)


class TestShabpGUI(unittest.TestCase):

    def test_shabp_geometry_01(self):
        log = get_logger(level='warning')
        test = ShabpGUI()
        test.log = log
        shabp_infilename = os.path.join(model_path, 'models', 'flap', 'flap_inviscid.mk5')
        test.load_shabp_geometry(shabp_infilename)

    def _test_shabp_geometry_02(self):
        test = ShabpGUI()
        shabp_infilename = os.path.join(model_path, 'models', 'orbiter.mk5')
        test.load_shabp_geometry(shabp_infilename)

    def _test_shabp_geometry_03(self):
        test = ShabpGUI()
        shabp_infilename = os.path.join(model_path, 'models', 'shuttle.mk5')
        test.load_shabp_geometry(shabp_infilename)

    def test_shabp_geometry_04(self):
        test = ShabpGUI()
        shabp_infilename = os.path.join(model_path, 'models', 'nose', 'noseX_working.mk5')
        test.load_shabp_geometry(shabp_infilename)


    def test_shabp_results(self):
        pass
        #geometry_filename = os.path.join(model_path, 'M100.inp')
        #agps_filename = os.path.join(model_path, 'agps')
        #out_filename = os.path.join(model_path, 'panair.out')

        #test = ShabpGUI()
        #test.load_panair_geometry(geometry_filename)
        #test.load_panair_results(agps_filename)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

