"""
defines:
 - CBAR
 - CBARAO
 - BAROR
 - CBEAM3
 - CBEND
"""
# pylint: disable=R0904,R0902,E1101,E1103,C0111,C0302,C0103,W0101
from __future__ import (nested_scopes, generators, division, absolute_import,
                        print_function, unicode_literals)
from six import string_types

import numpy as np
from numpy.linalg import norm

from pyNastran.utils import integer_types
from pyNastran.bdf.field_writer_8 import set_blank_if_default
from pyNastran.bdf.cards.base_card import BaseCard, Element
from pyNastran.bdf.bdf_interface.assign_type import (
    integer, integer_or_blank, integer_double_or_blank, double_or_blank,
    integer_string_or_blank, string_or_blank, string, integer_or_double)
from pyNastran.bdf.field_writer_8 import print_card_8
from pyNastran.bdf.field_writer_16 import print_card_16


class LineElement(Element):  # CBAR, CBEAM, CBEAM3, CBEND
    def __init__(self):
        Element.__init__(self)
        self.pid_ref = None  # type: Optional[Any]

    def C(self):
        """torsional constant"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.C()

    def Area(self):
        """returns the area of the element face"""
        raise NotImplementedError('implement self.Area() for %s' % self.type)

    def E(self):
        """returns the Young's Modulus, :math:`E`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.mid_ref.E()

    def G(self):
        """returns the Shear Modulus, :math:`G`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.mid_ref.G()

    def J(self):
        """returns the Polar Moment of Inertia, :math:`J`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.J()

    def I11(self):
        """returns the Moment of Inertia, :math:`I_{11}`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.I11()

    def I22(self):
        """returns the Moment of Inertia, :math:`I_{22}`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.I22()

    def I12(self):
        """returns the Moment of Inertia, :math:`I_{12}`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.I12()

    def Nu(self):
        """Get Poisson's Ratio, :math:`\nu`"""
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.mid_ref.nu

    def Rho(self):
        """Get the material density, :math:`\rho`"""
        #print(str(self.pid), type(self.pid))
        #raise NotImplementedError('implement self.Rho() for %s' % self.type)
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.mid_ref.rho

    def Nsm(self):
        """Placeholder method for the non-structural mass, :math:`nsm`"""
        raise NotImplementedError('implement self.Area() for %s' % self.type)

    def MassPerLength(self):
        """
        Get the mass per unit length, :math:`\frac{m}{L}`
        """
        if self.pid_ref is None:
            raise RuntimeError('Element eid=%i has not been '
                               'cross referenced.\n%s' % (self.eid, str(self)))
        return self.pid_ref.MassPerLength()

    def Mass(self):
        r"""
        Get the mass of the element.

        .. math:: m = \left( \rho A + nsm \right) L
        """
        L = self.Length()
        mass = L * self.MassPerLength()
        #try:
            #mass = (self.Rho() * self.Area() + self.Nsm()) * L
        #except TypeError:
            #msg = 'TypeError on eid=%s pid=%s:\n' % (self.eid, self.Pid())
            #msg += 'rho = %s\narea = %s\nnsm = %s\nL = %s' % (self.Rho(),
            #                                                  self.Area(),
            #                                                  self.Nsm(), L)
            #raise TypeError(msg)

        return mass

    def cross_reference(self, model):
        """
        Cross links the card so referenced cards can be extracted directly

        Parameters
        ----------
        model : BDF()
            the BDF object
        """
        msg = ' which is required by %s eid=%s' % (self.type, self.eid)
        self.nodes_ref = model.Nodes(self.nodes, msg=msg)
        #self.g0 = model.nodes[self.g0]
        self.pid_ref = model.Property(self.pid, msg=msg)

    def uncross_reference(self):
        self.nodes = self.node_ids
        self.pid = self.Pid()
        self.nodes_ref = None
        self.pid_ref = None

    def Length(self):
        r"""
        Gets the length, :math:`L`, of the element.

        .. math:: L = \sqrt{  (n_{x2}-n_{x1})^2+(n_{y2}-n_{y1})^2+(n_{z2}-n_{z1})^2  }
        """
        L = norm(self.nodes_ref[1].get_position() - self.nodes_ref[0].get_position())
        return L

    def get_edge_ids(self):
        """
        Return the edge IDs
        """
        node_ids = self.node_ids
        return [(node_ids[0], node_ids[1])]


class BAROR(object):
    """
    +-------+-----+---+---+---+-------+-----+-------+------+
    |   1   |  2  | 3 | 4 | 5 |   6   |  7  |   8   |  9   |
    +=======+=====+===+===+===+=======+=====+=======+======+
    | BAROR | PID |   |   |   | G0/X1 |  X2 |  X3   | OFFT |
    +-------+-----+---+---+---+-------+-----+-------+------+
    | BAROR | 39  |   |   |   |  0.6  | 2.9 | -5.87 | GOG  |
    +-------+-----+---+---+---+-------+-----+-------+------+
    """
    type = 'BAROR'
    def __init__(self):
        self.n = 0
        self.property_id = None
        self.g0 = None
        self.x = None
        self.offt = None

    def add_card(self, card, comment=''):
        if self.n == 1:
            raise RuntimeError('only one BAROR is allowed')
        self.n = 1
        if comment:
            self.comment = comment

        self.property_id = integer_or_blank(card, 2, 'pid')

        # x / g0
        field5 = integer_double_or_blank(card, 5, 'g0_x1', 0.0)
        if isinstance(field5, integer_types):
            self.is_g0 = True
            self.g0 = field5
            self.x = [0., 0., 0.]
        elif isinstance(field5, float):
            self.is_g0 = False
            self.g0 = None
            self.x = np.array([field5,
                               double_or_blank(card, 6, 'x2', 0.0),
                               double_or_blank(card, 7, 'x3', 0.0)],
                              dtype='float64')
        self.offt = string_or_blank(card, 8, 'offt', 'GGG')
        assert len(card) <= 8, 'len(BAROR card) = %i\ncard=%s' % (len(card), card)


class CBARAO(BaseCard):
    type = 'CBARAO'
    """
    Per MSC 2016.1
    +--------+------+-------+------+-----+--------+-----+----+----+
    |   1    |  2   |   3   |  4   |  5  |    6   |  7  | 8  |  9 |
    +========+======+=======+======+=====+========+=====+====+====+
    | CBARAO | EID  | SCALE |  X1  | X2  |  X3    | X4  | X5 | X6 |
    +--------+------+-------+------+-----+--------+-----+----+----+
    | CBARAO | 1065 |  FR   | 0.2  | 0.4 |  0.6   | 0.8 |    |    |
    +--------+------+-------+------+-----+--------+-----+----+----+

    Alternate form (not supported):
    +--------+------+-------+------+-----+--------+-----+----+----+
    |   1    |  2   |   3   |  4   |  5  |    6   |  7  | 8  |  9 |
    +========+======+=======+======+=====+========+=====+====+====+
    | CBARAO | EID  | SCALE | NPTS | X1  | DELTAX |     |    |    |
    +--------+------+-------+------+-----+--------+-----+----+----+
    | CBARAO | 1065 |  FR   |  4   | 0.2 |  0.2   |     |    |    |
    +--------+------+-------+------+-----+--------+-----+----+----+
    """
    def __init__(self, eid, scale, x, comment=''):
        """
        Creates a CBARAO card, which defines additional output locations
        for the CBAR card.

        It also changes the OP2 element type from a CBAR-34 to a CBAR-100.
        However, it is ignored if there are no PLOAD1s in the model.
        Furthermore, the type is changed for the whole deck, regardless of
        whether there are PLOAD1s in the other load cases.

        Parameters
        ----------
        eid : int
            element id
        scale : str
            defines what x means
            LE : x is in absolute coordinates along the bar
            FR : x is in fractional
        x : List[float]
            the additional output locations (doesn't include the end points)
            len(x) <= 6
        comment : str; default=''
            a comment for the card

        MSC only
        """
        if comment:
            self.comment = comment
        self.eid = eid
        self.scale = scale
        self.x = np.unique(x).tolist()

    @classmethod
    def add_card(cls, card, comment=''):
        """
        Adds a CBARAO card from ``BDF.add_card(...)``

        Parameters
        ----------
        card : BDFCard()
            a BDFCard object
        comment : str; default=''
            a comment for the card
        """
        eid = integer(card, 1, 'eid')
        scale = string(card, 2, 'scale')
        x1_npoints = integer_or_double(card, 3, 'x1/npoints')
        if isinstance(x1_npoints, integer_types):
            npoints = x1_npoints
            x1 = double_or_blank(card, 4, 'x1')
            delta_x = double_or_blank(card, 4, 'delta_x')
            x = np.arange(x1, npoints, delta_x)
            raise NotImplementedError('card=%s x=%s' % (card, x))

        else:
            x = [
                x1_npoints,
                double_or_blank(card, 4, 'x2'),
                double_or_blank(card, 5, 'x3'),
                double_or_blank(card, 6, 'x4'),
                double_or_blank(card, 7, 'x5'),
                double_or_blank(card, 8, 'x6'),
            ]
        assert len(card) <= 9, 'len(CBARAO card) = %i\ncard=%s' % (len(card), card)
        return CBARAO(eid, scale, x, comment=comment)

    def _verify(self, xref=False):
        pass

    def raw_fields(self):
        list_fields = ['CBARAO', self.eid, self.scale] + self.x
        return list_fields

    def repr_fields(self):
        return self.raw_fields()

    def write_card(self, size=8, is_double=False):
        card = self.repr_fields()
        if size == 8:
            return self.comment + print_card_8(card)
        return self.comment + print_card_16(card)

class CBAR(LineElement):
    """
    +-------+-----+-----+-----+-----+-----+-----+-----+------+
    |   1   |  2  |  3  |  4  |  5  |  6  |  7  |  8  |   9  |
    +=======+=====+=====+=====+=====+=====+=====+=====+======+
    | CBAR  | EID | PID | GA  | GB  | X1  | X2  | X3  | OFFT |
    +-------+-----+-----+-----+-----+-----+-----+-----+------+
    |       | PA  | PB  | W1A | W2A | W3A | W1B | W2B | W3B  |
    +-------+-----+-----+-----+-----+-----+-----+-----+------+

    or

    +-------+-----+-----+-----+-----+-----+-----+-----+------+
    |   1   |  2  |  3  |  4  |  5  |  6  |  7  |  8  |   9  |
    +=======+=====+=====+=====+=====+=====+=====+=====+======+
    | CBAR  | EID | PID | GA  | GB  | G0  |     |     | OFFT |
    +-------+-----+-----+-----+-----+-----+-----+-----+------+
    |       | PA  | PB  | W1A | W2A | W3A | W1B | W2B | W3B  |
    +-------+-----+-----+-----+-----+-----+-----+-----+------+

    +-------+-------+-----+-------+-------+--------+-------+-------+-------+
    |   1   |   2   |  3  |   4   |   5   |    6   |   7   |   8   |   9   |
    +=======+=======+=====+=======+=======+========+=======+=======+=======+
    |  CBAR |   2   |  39 |   7   |   6   |  105   |       |       |  GGG  |
    +-------+-------+-----+-------+-------+--------+-------+-------+-------+
    |       |       | 513 |  0.0  |  0.0  |    -9. |  0.0  |  0.0  |   -9. |
    +-------+-------+-----+-------+-------+--------+-------+-------+-------+
    """
    type = 'CBAR'
    _field_map = {
        1: 'eid', 2:'pid', 3:'ga', 4:'gb',
        8:'offt', 9:'pa', 10:'pb',
    }

    def _update_field_helper(self, n, value):
        if n == 11:
            self.wa[0] = value
        elif n == 12:
            self.wa[1] = value
        elif n == 13:
            self.wa[2] = value
        elif n == 14:
            self.wb[0] = value
        elif n == 15:
            self.wb[1] = value
        elif n == 16:
            self.wb[2] = value
        else:
            if self.g0 is not None:
                if n == 5:
                    self.g0 = value
                else:
                    raise KeyError('Field %r=%r is an invalid %s entry.' % (n, value, self.type))
            else:
                if n == 5:
                    self.x[0] = value
                elif n == 6:
                    self.x[1] = value
                elif n == 7:
                    self.x[2] = value
                else:
                    raise KeyError('Field %r=%r is an invalid %s entry.' % (n, value, self.type))

    def __init__(self, eid, pid, nids,
                 x, g0, offt='GGG',
                 pa=0, pb=0, wa=None, wb=None, comment=''):
        """
        Adds a CBAR card

        Parameters
        ----------
        pid : int
            property id
        mid : int
            material id
        nids : List[int, int]
            node ids; connected grid points at ends A and B
        x : List[float, float, float]
            Components of orientation vector, from GA, in the displacement
            coordinate system at GA (default), or in the basic coordinate system
        g0 : int
            Alternate method to supply the orientation vector using grid
            point G0. Direction of is from GA to G0. is then transferred
            to End A
        offt : str; default='GGG'
            Offset vector interpretation flag
        pa / pb : int; default=0
            Pin Flag at End A/B.  Releases the specified DOFs
        wa / wb : List[float, float, float]
            Components of offset vectors from the grid points to the end
            points of the axis of the shear center
        comment : str; default=''
            a comment for the card
        """
        LineElement.__init__(self)
        if comment:
            self.comment = comment
        if wa is None:
            wa = np.zeros(3, dtype='float64')
        else:
            wa = np.asarray(wa)
        if wb is None:
            wb = np.zeros(3, dtype='float64')
        else:
            wb = np.asarray(wb)

        self.eid = eid
        self.pid = pid
        self.x = x
        self.g0 = g0
        self.ga = nids[0]
        self.gb = nids[1]
        self.offt = offt
        self.pa = pa
        self.pb = pb
        self.wa = wa
        self.wb = wb
        self.pid_ref = None
        self.ga_ref = None
        self.gb_ref = None

    def validate(self):
        if isinstance(self.offt, integer_types):
            assert self.offt in [1, 2], 'invalid offt; offt=%i' % self.offt
            raise NotImplementedError('invalid offt; offt=%i' % self.offt)
        elif not isinstance(self.offt, string_types):
            raise SyntaxError('invalid offt expected a string of length 3 '
                              'offt=%r; Type=%s' % (self.offt, type(self.offt)))

        if self.g0 in [self.ga, self.gb]:
            msg = 'G0=%s cannot be GA=%s or GB=%s' % (self.g0, self.ga, self.gb)
            raise RuntimeError(msg)

        msg = 'invalid offt parameter of %s...offt=%s' % (self.type, self.offt)
        # B,G,O
        assert self.offt[0] in ['G', 'B'], msg
        assert self.offt[1] in ['G', 'O', 'E'], msg
        assert self.offt[2] in ['G', 'O', 'E'], msg

    @classmethod
    def add_card(cls, card, comment=''):
        """
        Adds a CBAR card from ``BDF.add_card(...)``

        Parameters
        ----------
        card : BDFCard()
            a BDFCard object
        comment : str; default=''
            a comment for the card
        """
        eid = integer(card, 1, 'eid')
        pid = integer_or_blank(card, 2, 'pid', eid)
        ga = integer(card, 3, 'ga')
        gb = integer(card, 4, 'gb')
        x, g0 = init_x_g0(card, eid)

        # doesn't exist in NX nastran
        offt = integer_string_or_blank(card, 8, 'offt', 'GGG')
        #print('cls.offt = %r' % (cls.offt))

        pa = integer_or_blank(card, 9, 'pa', 0)
        pb = integer_or_blank(card, 10, 'pb', 0)

        wa = np.array([double_or_blank(card, 11, 'w1a', 0.0),
                       double_or_blank(card, 12, 'w2a', 0.0),
                       double_or_blank(card, 13, 'w3a', 0.0)], dtype='float64')

        wb = np.array([double_or_blank(card, 14, 'w1b', 0.0),
                       double_or_blank(card, 15, 'w2b', 0.0),
                       double_or_blank(card, 16, 'w3b', 0.0)], dtype='float64')
        assert len(card) <= 17, 'len(CBAR card) = %i\ncard=%s' % (len(card), card)
        return CBAR(eid, pid, [ga, gb], x, g0,
                    offt, pa, pb, wa, wb, comment=comment)

    @classmethod
    def add_op2_data(cls, data, comment=''):
        #: .. todo:: verify
        #data = [[eid,pid,ga,gb,pa,pb,w1a,w2a,w3a,w1b,w2b,w3b],[f,g0]]
        #data = [[eid,pid,ga,gb,pa,pb,w1a,w2a,w3a,w1b,w2b,w3b],[f,x1,x2,x3]]

        main = data[0]
        flag = data[1][0]
        if flag in [0, 1]:
            g0 = None
            x = np.array([data[1][1],
                          data[1][2],
                          data[1][3]], dtype='float64')
        else:
            g0 = data[1][1]
            x = None

        eid = main[0]
        pid = main[1]
        ga = main[2]
        gb = main[3]
        #self.offt = str(data[4]) # GGG
        offt = 'GGG'  #: .. todo:: offt can be an integer; translate to char
        pa = main[4]
        pb = main[5]

        wa = np.array([main[6], main[7], main[8]], dtype='float64')
        wb = np.array([main[9], main[10], main[11]], dtype='float64')
        return CBAR(eid, pid, [ga, gb], x, g0,
                    offt, pa, pb, wa, wb, comment=comment)

    def _verify(self, xref=False):
        eid = self.eid
        pid = self.Pid()
        edges = self.get_edge_ids()
        if xref:  # True
            assert self.pid_ref.type in ['PBAR', 'PBARL'], '%s%s' % (self, self.pid_ref)
            mid = self.Mid()
            A = self.Area()
            nsm = self.Nsm()
            mpl = self.MassPerLength()
            L = self.Length()
            mass = self.Mass()
            assert isinstance(mid, int), 'mid=%r' % mid
            assert isinstance(nsm, float), 'nsm=%r' % nsm
            assert isinstance(A, float), 'eid=%s A=%r' % (eid, A)
            assert isinstance(L, float), 'eid=%s L=%r' % (eid, L)
            assert isinstance(mpl, float), 'eid=%s mass_per_length=%r' % (eid, mpl)
            assert isinstance(mass, float), 'eid=%s mass=%r' % (eid, mass)
            assert L > 0.0, 'eid=%s L=%s' % (eid, L)

    def Mid(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        return self.pid_ref.Mid()

    def Area(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        A = self.pid_ref.Area()
        assert isinstance(A, float)
        return A

    def J(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        j = self.pid_ref.J()
        if not isinstance(j, float):
            msg = 'J=%r must be a float; CBAR eid=%s pid=%s pidType=%s' % (
                j, self.eid, self.pid_ref.pid, self.pid_ref.type)
            raise TypeError(msg)
        return j

    def Length(self):
        # TODO: consider w1a and w1b in the length formulation
        L = norm(self.gb_ref.get_position() - self.ga_ref.get_position())
        assert isinstance(L, float)
        return L

    def Nsm(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        nsm = self.pid_ref.Nsm()
        assert isinstance(nsm, float)
        return nsm

    def I1(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        return self.pid_ref.I1()

    def I2(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        return self.pid_ref.I2()

    def Centroid(self):
        if self.pid_ref is None:
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        return (self.ga_ref.get_position() + self.gb_ref.get_position()) / 2.

    def center_of_mass(self):
        return self.Centroid()

    def cross_reference(self, model):
        """
        Cross links the card so referenced cards can be extracted directly

        Parameters
        ----------
        model : BDF()
            the BDF object
        """
        #if self.g0:
        #    self.x = nodes[self.g0].get_position() - nodes[self.ga].get_position()
        msg = ' which is required by CBAR eid=%s' % (self.eid)
        self.ga_ref = model.Node(self.ga, msg=msg)
        self.gb_ref = model.Node(self.gb, msg=msg)
        self.pid_ref = model.Property(self.pid, msg=msg)
        if model.is_nx:
            assert self.offt == 'GGG', 'NX only support offt=GGG; offt=%r' % self.offt

    def uncross_reference(self):
        self.pid = self.Pid()
        self.ga = self.Ga()
        self.gb = self.Gb()
        self.ga_ref = None
        self.gb_ref = None
        self.pid_ref = None

    def Ga(self):
        if self.ga_ref is None:
            return self.ga
        return self.ga_ref.nid

    def Gb(self):
        if self.gb_ref is None:
            return self.gb
        return self.gb_ref.nid

    def get_x_g0_defaults(self):
        """
        X and G0 compete for the same fields, so the method exists to
        make it easier to write the card

        Returns
        -------
        x_g0 : varies
            g0 : List[int, None, None]
            x : List[float, float, float]
        """
        if self.g0 is not None:
            return (self.g0, None, None)
        else:
            #print('x =', self.x)
            #print('g0 =', self.g0)
            #x1 = set_blank_if_default(self.x[0], 0.0)
            #x2 = set_blank_if_default(self.x[1], 0.0)
            #x3 = set_blank_if_default(self.x[2], 0.0)
            return list(self.x)

    def get_orientation_vector(self, xyz):
        """
        Element offsets are defined in a Cartesian system located at the
        connecting grid point. The components of the offsets are always
        defined in units of translation, even if the displacement
        coordinate system is cylindrical or spherical.

        For example, in Figure 11-11, the grid point displacement
        coordinate system is cylindrical, and the offset vector is
        defined using Cartesian coordinates u1, u2, and u3 in units of
        translation.
        """
        if self.g0:
            v = xyz[self.g0] - xyz[self.Ga()]
        else:
            v = self.x
        assert self.offt == 'GGG', self.offt
        return v

    @property
    def node_ids(self):
        return [self.Ga(), self.Gb()]

    def get_edge_ids(self):
        return [tuple(sorted(self.node_ids))]

    @property
    def nodes(self):
        return [self.ga, self.gb]

    @nodes.setter
    def nodes(self, values):
        self.ga = values[0]
        self.gb = values[1]

    @property
    def nodes_ref(self):
        return [self.ga_ref, self.gb_ref]

    @nodes_ref.setter
    def nodes_ref(self, values):
        assert values is not None, values
        self.ga_ref = values[0]
        self.gb_ref = values[1]

    def raw_fields(self):
        """
        Gets the fields of the card in their full form
        """
        (x1, x2, x3) = self.get_x_g0_defaults()

        # offt doesn't exist in NX nastran
        offt = set_blank_if_default(self.offt, 'GGG')

        list_fields = ['CBAR', self.eid, self.Pid(), self.Ga(), self.Gb(), x1, x2,
                       x3, offt, self.pa, self.pb] + list(self.wa) + list(self.wb)
        return list_fields

    def repr_fields(self):
        """
        Gets the fields of the card in their reduced form
        """
        pa = set_blank_if_default(self.pa, 0)
        pb = set_blank_if_default(self.pb, 0)

        w1a = set_blank_if_default(self.wa[0], 0.0)
        w2a = set_blank_if_default(self.wa[1], 0.0)
        w3a = set_blank_if_default(self.wa[2], 0.0)

        w1b = set_blank_if_default(self.wb[0], 0.0)
        w2b = set_blank_if_default(self.wb[1], 0.0)
        w3b = set_blank_if_default(self.wb[2], 0.0)
        x1, x2, x3 = self.get_x_g0_defaults()

        # offt doesn't exist in NX nastran
        offt = set_blank_if_default(self.offt, 'GGG')

        list_fields = ['CBAR', self.eid, self.Pid(), self.Ga(), self.Gb(), x1, x2,
                       x3, offt, pa, pb, w1a, w2a, w3a, w1b, w2b, w3b]
        return list_fields

    def write_card(self, size=8, is_double=False):
        card = self.repr_fields()
        if size == 8:
            return self.comment + print_card_8(card)
        return self.comment + print_card_16(card)

    def write_card_16(self, is_double=False):
        card = self.repr_fields()
        return self.comment + print_card_16(card)


class CBEAM3(LineElement):  # was CBAR
    """
    Defines a three-node beam element
    """
    type = 'CBEAM3'

    def __init__(self, eid, pid, nids, x, g0,
                 wa, wb, wc, tw, s, comment=''):
        LineElement.__init__(self)
        if comment:
            self.comment = comment
        self.eid = eid
        self.pid = pid
        self.ga = nids[0]
        self.gb = nids[1]
        self.gc = nids[2]
        self.x = x
        self.g0 = g0
        self.wa = wa
        self.wb = wb
        self.wc = wc
        self.tw = tw
        self.s = s
        self.ga_ref = None
        self.gb_ref = None
        self.gc_ref = None
        self.pid_ref = None

    @classmethod
    def add_card(cls, card, comment=''):
        """
        Adds a CBEAM3 card from ``BDF.add_card(...)``

        Parameters
        ----------
        card : BDFCard()
            a BDFCard object
        comment : str; default=''
            a comment for the card
        """
        eid = integer(card, 1, 'eid')
        pid = integer_or_blank(card, 2, 'pid', eid)
        ga = integer(card, 3, 'ga')
        gb = integer(card, 4, 'gb')
        gc = integer(card, 5, 'gc')

        x, g0 = init_x_g0(card, eid)

        wa = np.array([double_or_blank(card, 9, 'w1a', 0.0),
                       double_or_blank(card, 10, 'w2a', 0.0),
                       double_or_blank(card, 11, 'w3a', 0.0)], dtype='float64')

        wb = np.array([double_or_blank(card, 12, 'w1b', 0.0),
                       double_or_blank(card, 13, 'w2b', 0.0),
                       double_or_blank(card, 14, 'w3b', 0.0)], dtype='float64')

        wc = np.array([double_or_blank(card, 15, 'w1c', 0.0),
                       double_or_blank(card, 16, 'w2c', 0.0),
                       double_or_blank(card, 17, 'w3c', 0.0)], dtype='float64')

        tw = np.array([double_or_blank(card, 18, 0., 'twa'),
                       double_or_blank(card, 19, 0., 'twb'),
                       double_or_blank(card, 20, 0., 'twc')], dtype='float64')

        s = np.array([integer_or_blank(card, 21, 'sa'),
                      integer_or_blank(card, 22, 'sb'),
                      integer_or_blank(card, 23, 'sc')], dtype='int32')
        assert len(card) <= 24, 'len(CBEAM3 card) = %i\ncard=%s' % (len(card), card)
        return CBEAM3(eid, pid, [ga, gb, gc], x, g0,
                      wa, wb, wc, tw, s, comment='')

    def cross_reference(self, model):
        """
        Cross links the card so referenced cards can be extracted directly

        Parameters
        ----------
        model : BDF()
            the BDF object
        """
        msg = ' which is required by CBEAM3 eid=%s' % (self.eid)
        self.ga_ref = model.Node(self.ga, msg=msg)
        self.gb_ref = model.Node(self.gb, msg=msg)
        self.gc_ref = model.Node(self.gc, msg=msg)
        self.pid_ref = model.Property(self.pid, msg=msg)

    def uncross_reference(self):
        self.ga = self.Ga()
        self.gb = self.Gb()
        self.gc = self.Gc()
        self.pid = self.Pid()
        self.ga_ref = None
        self.gb_ref = None
        self.gc_ref = None
        self.pid_ref = None

    def Length(self):
        """
        # TODO: consider w1a and w1b in the length formulation
        # TODO: add gc to length formula
        """
        L = norm(self.gb_ref.get_position() - self.ga_ref.get_position())
        assert isinstance(L, float)
        return L

    def Area(self):
        if isinstance(self.pid_ref, integer_types):
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        A = self.pid_ref.Area()
        assert isinstance(A, float)
        return A

    def Nsm(self):
        if isinstance(self.pid_ref, integer_types):
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        nsm = self.pid_ref.Nsm()
        assert isinstance(nsm, float)
        return nsm

    def Ga(self):
        if self.ga_ref is None:
            return self.ga
        return self.ga_ref.nid

    def Gb(self):
        if self.gb_ref is None:
            return self.gb
        return self.gb_ref.nid

    def Gc(self):
        if self.gc_ref is None:
            return self.gc
        return self.gc_ref.nid

    @property
    def node_ids(self):
        return [self.Ga(), self.Gb(), self.Gc()]

    def raw_fields(self):
        (x1, x2, x3) = self.get_x_g0_defaults()
        (ga, gb, gc) = self.node_ids
        list_fields = ['CBEAM3', self.eid, self.Pid(), ga, gb, gc, x1, x2, x3] + \
                  list(self.wa) + list(self.wb) + list(self.wc) + list(self.tw) + list(self.s)
        return list_fields

    def repr_fields(self):
        w1a = set_blank_if_default(self.wa[0], 0.0)
        w2a = set_blank_if_default(self.wa[1], 0.0)
        w3a = set_blank_if_default(self.wa[2], 0.0)
        w1b = set_blank_if_default(self.wb[0], 0.0)
        w2b = set_blank_if_default(self.wb[1], 0.0)
        w3b = set_blank_if_default(self.wb[2], 0.0)
        w1c = set_blank_if_default(self.wc[0], 0.0)
        w2c = set_blank_if_default(self.wc[1], 0.0)
        w3c = set_blank_if_default(self.wc[2], 0.0)

        twa = set_blank_if_default(self.tw[0], 0.0)
        twb = set_blank_if_default(self.tw[1], 0.0)
        twc = set_blank_if_default(self.tw[2], 0.0)

        (x1, x2, x3) = self.get_x_g0_defaults()
        (ga, gb, gc) = self.node_ids
        list_fields = ['CBEAM3', self.eid, self.Pid(), ga, gb, gc, x1, x2, x3,
                       w1a, w2a, w3a, w1b, w2b, w3b, w1c, w2c, w3c,
                       twa, twb, twc, self.s[0], self.s[1], self.s[2]]
        return list_fields

    def write_card(self, size=8, is_double=False):
        card = self.repr_fields()
        if size == 8:
            return self.comment + print_card_8(card)
        return self.comment + print_card_16(card)

    def _verify(self, xref=False):
        edges = self.get_edge_ids()


class CBEND(LineElement):
    type = 'CBEND'
    _field_map = {
        1: 'eid', 2:'pid', 3:'ga', 4:'gb', 8:'geom',
    }

    def _update_field_helper(self, n, value):
        if self.g0 is not None:
            if n == 5:
                self.g0 = value
            else:
                raise KeyError('Field %r=%r is an invalid %s entry.' % (n, value, self.type))
        else:
            if n == 5:
                self.x[0] = value
            elif n == 6:
                self.x[1] = value
            elif n == 7:
                self.x[2] = value
            else:
                raise KeyError('Field %r=%r is an invalid %s entry.' % (n, value, self.type))

    def __init__(self, eid, pid, nids, g0, x, geom, comment=''):
        """
        Creates a CEND card

        Parameters
        ----------
        eid : int
            element id
        pid : int
            property id (PBEND)
        nids : List[int, int]
            node ids; connected grid points at ends A and B
        g0 : int
            ???
        x : List[float, float, float]
            ???
        geom : ???
            ???
        comment : str; default=''
            a comment for the card
        """
        LineElement.__init__(self)
        if comment:
            self.comment = comment
        self.eid = eid
        self.pid = pid
        self.ga = nids[0]
        self.gb = nids[1]

        if g0 is None:
            assert x is not None, 'g0=%s x=%s; one must not be None' % (g0, x)
        self.g0 = g0
        self.x = x
        self.geom = geom
        assert self.geom in [1, 2, 3, 4], 'geom is invalid geom=%r' % self.geom
        self.ga_ref = None
        self.gb_ref = None
        self.pid_ref = None

    @classmethod
    def add_card(cls, card, comment=''):
        """
        Adds a CBEND card from ``BDF.add_card(...)``

        Parameters
        ----------
        card : BDFCard()
            a BDFCard object
        comment : str; default=''
            a comment for the card
        """
        eid = integer(card, 1, 'eid')
        pid = integer_or_blank(card, 2, 'pid', eid)
        ga = integer(card, 3, 'ga')
        gb = integer(card, 4, 'gb')
        x1_g0 = integer_double_or_blank(card, 5, 'x1_g0', 0.0)
        if isinstance(x1_g0, integer_types):
            g0 = x1_g0
            x = None
        elif isinstance(x1_g0, float):
            g0 = None
            x = np.array([double_or_blank(card, 5, 'x1', 0.0),
                          double_or_blank(card, 6, 'x2', 0.0),
                          double_or_blank(card, 7, 'x3', 0.0)], dtype='float64')
            if norm(x) == 0.0:
                msg = 'G0 vector defining plane 1 is not defined.\n'
                msg += 'G0 = %s\n' % g0
                msg += 'X  = %s\n' % x
                raise RuntimeError(msg)
        else:
            raise ValueError('invalid x1Go=%r on CBEND' % x1_g0)
        geom = integer(card, 8, 'geom')

        assert len(card) == 9, 'len(CBEND card) = %i\ncard=%s' % (len(card), card)
        return CBEND(eid, pid, [ga, gb], g0, x, geom, comment=comment)

    @classmethod
    def add_op2_data(cls, data, comment=''):
        #data = [[eid, pid, ga, gb, geom], [f, x1, x2, x3]]
        #data = [[eid, pid, ga, gb, geom], [f, g0]]

        main = data[0]
        flag = data[1][0]
        if flag in [0, 1]:
            g0 = None
            x = np.array([data[1][1],
                          data[1][2],
                          data[1][3]], dtype='float64')
        else:
            g0 = data[1][1]
            x = None

        eid = main[0]
        pid = main[1]
        ga = main[2]
        gb = main[3]
        geom = main[4]
        return CBEND(eid, pid, [ga, gb], g0, x, geom, comment=comment)

    def get_x_g0_defaults(self):
        if self.g0 is not None:
            return (self.g0, None, None)
        else:
            #print('x =', self.x)
            #print('g0 =', self.g0)
            #x1 = set_blank_if_default(self.x[0], 0.0)
            #x2 = set_blank_if_default(self.x[1], 0.0)
            #x3 = set_blank_if_default(self.x[2], 0.0)
            return list(self.x)

    def Length(self):
        # TODO: consider w1a and w1b in the length formulation
        L = norm(self.gb_ref.get_position() - self.ga_ref.get_position())
        assert isinstance(L, float)
        return L

        #prop = self.pid_ref
        #bend_radius = prop.rb
        #theta_bend = prop.thetab
        #length_oa = None
        #if self.geom == 1:
            #The center of curvature lies on the line AO
            #(or its extension) or vector .
            #pass
        #elif self.geom == 2:
            # The tangent of centroid arc at end A is
            # parallel to line AO or vector . Point O (or
            # vector) and the arc must be on the
            # same side of the chord .
            #pass
        #elif self.geom == 3:
            # The bend radius (RB) is specified on the
            # PBEND entry: Points A, B, and O (or
            # vector ) define a plane parallel or
            # coincident with the plane of the element
            # arc. Point O (or vector ) lies on the
            # opposite side of line AB from the center of
            # the curvature.
            #pass
        #elif self.geom == 4:
            # THETAB is specified on the PBEND entry.
            # Points A, B, and O (or vector ) define a
            # plane parallel or coincident with the plane
            # of the element arc. Point O (or vector )
            # lies on the opposite side of line AB from the
            # center of curvature.
            #pass
        #else:
            #raise RuntimeError('geom=%r is not supported on the CBEND' % self.geom)
        #return L

    def validate(self):
        if self.g0 is not None:
            assert isinstance(self.g0, integer_types), 'g0=%s must be an integer' % self.g0
        if self.g0 in [self.ga, self.gb]:
            msg = 'G0=%s cannot be GA=%s or GB=%s' % (self.g0, self.ga, self.gb)
            raise RuntimeError(msg)
        #BEND ELEMENT %1 BEND RADIUS OR ARC ANGLE INCONSISTENT
        #WITH GEOM OPTION
        #RB is nonzero on PBEND entry when GEOM option on CBEND entry is 1,
        #2, or 4 or RB is zero when GEOM option is 3 or AB is nonzero when
        #when GEOM option is 1, 2, or 3 or B is <= 0. or > 180, when
        #GEOM option is 4.

    @property
    def node_ids(self):
        return [self.Ga(), self.Gb()]

    @property
    def nodes(self):
        return [self.ga, self.gb]

    @nodes.setter
    def nodes(self, values):
        self.ga = values[0]
        self.gb = values[1]

    def Ga(self):
        if self.ga_ref is None:
            return self.ga
        return self.ga_ref.nid

    def Gb(self):
        if self.gb_ref is None:
            return self.gb
        return self.gb_ref.nid

    #def get_edge_ids(self):
        #return [tuple(sorted(self.node_ids))]

    @property
    def nodes_ref(self):
        return [self.ga_ref, self.gb_ref]

    @nodes_ref.setter
    def nodes_ref(self, values):
        assert values is not None, values
        self.ga_ref = values[0]
        self.gb_ref = values[1]

    def Area(self):
        if isinstance(self.pid, integer_types):
            msg = 'Element eid=%i has not been cross referenced.\n%s' % (self.eid, str(self))
            raise RuntimeError(msg)
        return self.pid_ref.Area()

    def _verify(self, xref):
        edges = self.get_edge_ids()

    def cross_reference(self, model):
        """
        Cross links the card so referenced cards can be extracted directly

        Parameters
        ----------
        model : BDF()
            the BDF object
        """
        msg = ' which is required by CBEND eid=%s' % (self.eid)
        #self.g0 = model.nodes[self.g0]
        self.ga_ref = model.Node(self.ga, msg=msg)
        self.gb_ref = model.Node(self.gb, msg=msg)
        self.pid_ref = model.Property(self.pid, msg=msg)

    def uncross_reference(self):
        node_ids = self.node_ids
        self.ga = node_ids[0]
        self.gb = node_ids[1]
        self.pid = self.Pid()
        self.ga_ref = None
        self.gb_ref = None
        self.pid_ref = None

    def raw_fields(self):
        (x1, x2, x3) = self.get_x_g0_defaults()
        list_fields = ['CBEND', self.eid, self.Pid(), self.Ga(), self.Gb(),
                       x1, x2, x3, self.geom]
        return list_fields

    def repr_fields(self):
        return self.raw_fields()

    def write_card(self, size=8, is_double=False):
        card = self.repr_fields()
        if size == 8:
            return self.comment + print_card_8(card)
        else:
            return self.comment + print_card_16(card)

def init_x_g0(card, eid):
    """common method to read the x/g0 field for the CBAR, CBEAM, CBEAM3"""
    field5 = integer_double_or_blank(card, 5, 'g0_x1', 0.0)
    if isinstance(field5, integer_types):
        g0 = field5
        x = None
    elif isinstance(field5, float):
        g0 = None
        x = np.array([field5,
                      double_or_blank(card, 6, 'x2', 0.0),
                      double_or_blank(card, 7, 'x3', 0.0)], dtype='float64')
        if norm(x) == 0.0:
            msg = 'G0 vector defining plane 1 is not defined.\n'
            msg += 'G0 = %s\n' % g0
            msg += 'X  = %s\n' % x
            raise RuntimeError(msg)
    else:
        msg = ('field5 on %s (G0/X1) is the wrong type...id=%s field5=%s '
               'type=%s' % (card.field(0), eid, field5, type(field5)))
        raise RuntimeError(msg)
    return x, g0
