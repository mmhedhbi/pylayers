from pylayers.util.geomutil import *
from pylayers.util.plotutil import *
import shapely.geometry as shg
import numpy as np
import scipy as sp
from numpy.testing import ( TestCase, assert_almost_equal, assert_raises, assert_equal, assert_, run_module_suite)

class Tesonb(TestCase):
    def test_onb(self):
        print "testing geomutil.onb"
        A = np.array([[0,0,0,0],[1,2,3,4],[0,0,0,0]])
        B = np.array([[0,0,0,0],[1,2,3,4],[10,10,10,10]])
        v = np.array([[1,1,1,1],[0,0,0,0],[0,0,0,0]])
        T = onb(A,B,v)
        print np.shape(T)
        print T[:,0,:]
        print T[:,1,:]
        print T[:,2,:]
        assert_equal(np.shape(T),(4,3,3))


    def test_ptconvex2(self):
        print "testing geomutil.ptconvex2"

        points  = shg.MultiPoint([(0, 0), (0, 1), (3.2, 1), (3.2, 0.7), (0.4, 0.7), (0.4, 0)])
        polyg   = Polygon(points)
        cvex,ccave   = polyg.ptconvex2() 
        assert_equal(cvex,[-5] )
        assert_equal(ccave,[-1, -2, -3, -4, -6] )
        points  = shg.MultiPoint([(0, 0), (0, 1), (-3.2, 1), (-3.2, 0.7), (-0.4, 0.7), (-0.4, 0)])
        polyg   = Polygon(points)
        cvex,ccave   = polyg.ptconvex2() 
        assert_equal(cvex,[-5] )
        assert_equal(ccave,[-1, -2, -3, -4, -6] )

if __name__ == "__main__":
    run_module_suite()
