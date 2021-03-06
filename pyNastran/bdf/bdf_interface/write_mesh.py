# coding: utf-8
"""
This file defines:
  - WriteMesh
"""
from __future__ import (nested_scopes, generators, division, absolute_import,
                        print_function, unicode_literals)
import sys
import io
from typing import List, Dict, Union, Optional, Tuple, Any, cast
from codecs import open
from six import string_types, iteritems, itervalues, PY2, StringIO

from pyNastran.bdf.utils import print_filename
from pyNastran.bdf.field_writer_8 import print_card_8
from pyNastran.bdf.field_writer_16 import print_card_16
from pyNastran.bdf.bdf_interface.attributes import BDFAttributes
from pyNastran.bdf.cards.nodes import write_xpoints


class WriteMesh(BDFAttributes):
    """
    Defines methods for writing cards

    Major methods:
      - model.write_bdf(...)
      - model.echo_bdf(...)
      - model.auto_reject_bdf(...)
    """
    def __init__(self):
        """creates methods for writing cards"""
        BDFAttributes.__init__(self)
        self._auto_reject = True
        self.cards_to_read = set([])

    def get_encoding(self, encoding=None):
        # type: (Optional[str]) -> str
        """gets the file encoding"""
        if encoding is not None:
            pass
        else:
            encoding = self._encoding
            if encoding is None:
                encoding = sys.getdefaultencoding()
        encoding = cast(str, encoding)
        return encoding

    def _output_helper(self, out_filename, interspersed, size, is_double):
        # type: (Optional[str], bool, int, bool) -> str
        """
        Performs type checking on the write_bdf inputs
        """
        if out_filename is None:
            from pyNastran.utils.gui_io import save_file_dialog
            wildcard_wx = "Nastran BDF (*.bdf; *.dat; *.nas; *.pch)|" \
                "*.bdf;*.dat;*.nas;*.pch|" \
                "All files (*.*)|*.*"
            wildcard_qt = "Nastran BDF (*.bdf *.dat *.nas *.pch);;All files (*)"
            title = 'Save BDF/DAT/PCH'
            out_filename = save_file_dialog(title, wildcard_wx, wildcard_qt)
            assert out_filename is not None, out_filename

        if PY2:
            if not (hasattr(out_filename, 'read') and hasattr(out_filename, 'write')
                   ) or isinstance(out_filename, (file, StringIO)):
                return out_filename
            elif not isinstance(out_filename, string_types):
                msg = 'out_filename=%r must be a string; type=%s' % (
                    out_filename, type(out_filename))
                raise TypeError(msg)
        else:
            if not(hasattr(out_filename, 'read') and hasattr(out_filename, 'write')
                  ) or isinstance(out_filename, io.IOBase):
                return out_filename
            elif not isinstance(out_filename, string_types):
                msg = 'out_filename=%r must be a string; type=%s' % (
                    out_filename, type(out_filename))
                raise TypeError(msg)

        if size == 8:
            assert is_double is False, 'is_double=%r' % is_double
        elif size == 16:
            assert is_double in [True, False], 'is_double=%r' % is_double
        else:
            assert size in [8, 16], size

        assert isinstance(interspersed, bool)
        fname = print_filename(out_filename)
        self.log.debug("***writing %s" % fname)
        return out_filename

    def write_caero_model(self, caero_bdf_filename='caero.bdf'):
        # type: (str) -> None
        """write the CAERO cards as CQUAD4s that can be visualized"""
        bdf_file = open(caero_bdf_filename, 'w')
        bdf_file.write('CEND\n')
        bdf_file.write('BEGIN BULK\n')
        bdf_file.write('$ punch=True\n')
        i = 1

        mid = 1
        bdf_file.write('MAT1,%s,3.0E7,,0.3\n' % mid)
        for aesurf_id, aesurf in iteritems(self.aesurf):
            cid = aesurf.cid1
            bdf_file.write('PSHELL,%s,%s,0.1\n' % (aesurf_id, aesurf_id))
            #print(cid)
            #ax, ay, az = cid.i
            #bx, by, bz = cid.j
            #cx, cy, cz = cid.k
            #bdf_file.write('CORD2R,%s,,%s,%s,%s,%s,%s,%s\n' % (cid, ax, ay, az, bx, by, bz))
            #bdf_file.write(',%s,%s,%s\n' % (cx, cy, cz))
            #print(cid)
            bdf_file.write(str(cid))
            #aesurf.elements
        for eid, caero in sorted(iteritems(self.caeros)):
            assert eid != 1, 'CAERO eid=1 is reserved for non-flaps'
            scaero = str(caero).rstrip().split('\n')
            bdf_file.write('$ ' + '\n$ '.join(scaero) + '\n')
            points, elements = caero.panel_points_elements()
            npoints = points.shape[0]
            #nelements = elements.shape[0]
            for ipoint, point in enumerate(points):
                x, y, z = point
                bdf_file.write('GRID,%s,,%s,%s,%s\n' % (i + ipoint, x, y, z))

            pid = eid
            mid = eid
            #if 0:
                #bdf_file.write('PSHELL,%s,%s,0.1\n' % (pid, mid))
                #bdf_file.write('MAT1,%s,3.0E7,,0.3\n' % mid)
            #else:
            bdf_file.write('PSHELL,%s,%s,0.1\n' % (1, 1))
            bdf_file.write('MAT1,%s,3.0E7,,0.3\n' % 1)

            j = 0
            for elem in elements + i:
                p1, p2, p3, p4 = elem
                eid2 = j + eid
                pidi = None
                for aesurf_id, aesurf in iteritems(self.aesurf):
                    aelist_id = aesurf.AELIST_id1()
                    aelist = self.aelists[aelist_id]
                    if eid2 in aelist.elements:
                        pidi = aesurf_id
                        break
                if pidi is None:
                    #pidi = pid
                    pidi = 1
                bdf_file.write('CQUAD4,%s,%s,%s,%s,%s,%s\n' % (j + eid, pidi, p1, p2, p3, p4))
                j += 1
            i += npoints
            #break
            #j += nelements
        bdf_file.write('ENDDATA\n')

    def write_bdf(self, out_filename=None, encoding=None,
                  size=8, is_double=False,
                  interspersed=False, enddata=None, close=True):
        # type: (Optional[Union[str, StringIO]], Optional[str], int, bool, bool, Optional[bool], bool) -> None
        """
        Writes the BDF.

        Parameters
        ----------
        out_filename : varies; default=None
            str        - the name to call the output bdf
            file       - a file object
            StringIO() - a StringIO object
            None       - pops a dialog
        encoding : str; default=None -> system specified encoding
            the unicode encoding
            latin1, and utf8 are generally good options
        size : int; {8, 16}
            the field size
        is_double : bool; default=False
            False : small field
            True : large field
        interspersed : bool; default=True
            Writes a bdf with properties & elements
            interspersed like how Patran writes the bdf.  This takes
            slightly longer than if interspersed=False, but makes it
            much easier to compare to a Patran-formatted bdf and is
            more clear.
        enddata : bool; default=None
            bool - enable/disable writing ENDDATA
            None - depends on input BDF
        close : bool; default=True
            should the output file be closed
        """
        #self.write_caero_model()
        out_filename = self._output_helper(out_filename,
                                           interspersed, size, is_double)
        self.log.debug('---starting BDF.write_bdf of %s---' % out_filename)
        encoding = self.get_encoding(encoding)
        #assert encoding.lower() in ['ascii', 'latin1', 'utf8'], encoding

        if hasattr(out_filename, 'read') and hasattr(out_filename, 'write'):
            bdf_file = out_filename
        else:
            bdf_file = open(out_filename, 'w', encoding=encoding)
        self._write_header(bdf_file, encoding)
        self._write_params(bdf_file, size, is_double)
        self._write_nodes(bdf_file, size, is_double)

        if interspersed:
            self._write_elements_interspersed(bdf_file, size, is_double)
        else:
            self._write_elements(bdf_file, size, is_double)
            self._write_properties(bdf_file, size, is_double)
        self._write_materials(bdf_file, size, is_double)

        self._write_masses(bdf_file, size, is_double)
        self._write_common(bdf_file, size, is_double)
        if (enddata is None and 'ENDDATA' in self.card_count) or enddata:
            bdf_file.write('ENDDATA\n')
        if close:
            bdf_file.close()

    def _write_header(self, bdf_file, encoding):
        # type: (Any, bool) -> None
        """
        Writes the executive and case control decks.
        """
        if self.punch is None:
            # writing a mesh without using read_bdf
            if self.system_command_lines or self.executive_control_lines or self.case_control_deck:
                self.punch = False
            else:
                self.punch = True

        if self.nastran_format:
            bdf_file.write('$pyNastran: version=%s\n' % self.nastran_format)
            bdf_file.write('$pyNastran: punch=%s\n' % self.punch)
            bdf_file.write('$pyNastran: encoding=%s\n' % encoding)
            bdf_file.write('$pyNastran: nnodes=%s\n' % len(self.nodes))
            bdf_file.write('$pyNastran: nelements=%s\n' % len(self.elements))

        if not self.punch:
            self._write_executive_control_deck(bdf_file)
            self._write_case_control_deck(bdf_file)

    def _write_executive_control_deck(self, bdf_file):
        # type: (Any) -> None
        """
        Writes the executive control deck.
        """
        msg = ''
        for line in self.system_command_lines:
            msg += line + '\n'

        if self.executive_control_lines:
            msg += '$EXECUTIVE CONTROL DECK\n'
            if self.sol == 600:
                new_sol = 'SOL 600,%s' % self.sol_method
            else:
                new_sol = 'SOL %s' % self.sol

            if self.sol_iline is not None:
                self.executive_control_lines[self.sol_iline] = new_sol

            for line in self.executive_control_lines:
                msg += line + '\n'
            bdf_file.write(msg)

    def _write_case_control_deck(self, bdf_file):
        # type: (Any) -> None
        """
        Writes the Case Control Deck.
        """
        if self.case_control_deck:
            msg = '$CASE CONTROL DECK\n'
            msg += str(self.case_control_deck)
            assert 'BEGIN BULK' in msg, msg
            bdf_file.write(''.join(msg))

    def _write_elements(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the elements in a sorted order
        """
        if self.elements:
            bdf_file.write('$ELEMENTS\n')
            if self.is_long_ids:
                for (eid, element) in sorted(iteritems(self.elements)):
                    bdf_file.write(element.write_card_16(is_double))
            else:
                for (eid, element) in sorted(iteritems(self.elements)):
                    try:
                        bdf_file.write(element.write_card(size, is_double))
                    except:
                        print('failed printing element...'
                              'type=%s eid=%s' % (element.type, eid))
                        raise
        if self.ao_element_flags:
            for (eid, element) in sorted(iteritems(self.ao_element_flags)):
                bdf_file.write(element.write_card(size, is_double))
        self._write_nsm(bdf_file, size, is_double)

    def _write_nsm(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the nsm in a sorted order
        """
        if self.nsms:
            msg = ['$NSM\n']
            for (key, nsms) in sorted(iteritems(self.nsms)):
                for nsm in nsms:
                    try:
                        msg.append(nsm.write_card(size, is_double))
                    except:
                        print('failed printing nsm...type=%s key=%r'
                              % (nsm.type, key))
                        raise
            bdf_file.write(''.join(msg))

    def _write_elements_interspersed(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the elements and properties in and interspersed order
        """
        missing_properties = []
        if self.properties:
            bdf_file.write('$ELEMENTS_WITH_PROPERTIES\n')

        eids_written = []  # type: List[int]
        pids = sorted(self.properties.keys())
        pid_eids = self.get_element_ids_dict_with_pids(pids)

        msg = []
        #failed_element_types = set([])
        for (pid, eids) in sorted(iteritems(pid_eids)):
            prop = self.properties[pid]
            if eids:
                msg.append(prop.write_card(size, is_double))
                eids.sort()
                for eid in eids:
                    element = self.elements[eid]
                    try:
                        msg.append(element.write_card(size, is_double))
                    except:
                        print('failed printing element...' 'type=%r eid=%s'
                              % (element.type, eid))
                        raise
                eids_written += eids
            else:
                missing_properties.append(prop.write_card(size, is_double))
        bdf_file.write(''.join(msg))

        eids_missing = set(self.elements.keys()).difference(set(eids_written))
        if eids_missing:
            msg = ['$ELEMENTS_WITH_NO_PROPERTIES '
                   '(PID=0 and unanalyzed properties)\n']
            for eid in sorted(eids_missing):
                element = self.elements[eid]
                try:
                    msg.append(element.write_card(size, is_double))
                except:
                    print('failed printing element...'
                          'type=%s eid=%s' % (element.type, eid))
                    raise
            bdf_file.write(''.join(msg))

        if missing_properties or self.pdampt or self.pbusht or self.pelast:
            msg = ['$UNASSOCIATED_PROPERTIES\n']
            for card in sorted(itervalues(self.pbusht)):
                msg.append(card.write_card(size, is_double))
            for card in sorted(itervalues(self.pdampt)):
                msg.append(card.write_card(size, is_double))
            for card in sorted(itervalues(self.pelast)):
                msg.append(card.write_card(size, is_double))
            for card in missing_properties:
                # this is a string...
                #print("missing_property = ", card
                msg.append(card)
            bdf_file.write(''.join(msg))
        self._write_nsm(bdf_file, size, is_double)

    def _write_aero(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the aero cards"""
        if self.caeros or self.paeros or self.monitor_points or self.splines:
            msg = ['$AERO\n']
            for (unused_id, caero) in sorted(iteritems(self.caeros)):
                msg.append(caero.write_card(size, is_double))
            for (unused_id, paero) in sorted(iteritems(self.paeros)):
                msg.append(paero.write_card(size, is_double))
            for (unused_id, spline) in sorted(iteritems(self.splines)):
                msg.append(spline.write_card(size, is_double))
            for monitor_point in self.monitor_points:
                msg.append(monitor_point.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_aero_control(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the aero control surface cards"""
        if(self.aecomps or self.aefacts or self.aeparams or self.aelinks or
           self.aelists or self.aestats or self.aesurf or self.aesurfs):
            msg = ['$AERO CONTROL SURFACES\n']
            for (unused_id, aelinks) in sorted(iteritems(self.aelinks)):
                for aelink in aelinks:
                    msg.append(aelink.write_card(size, is_double))

            for (unused_id, aecomp) in sorted(iteritems(self.aecomps)):
                msg.append(aecomp.write_card(size, is_double))
            for (unused_id, aeparam) in sorted(iteritems(self.aeparams)):
                msg.append(aeparam.write_card(size, is_double))
            for (unused_id, aestat) in sorted(iteritems(self.aestats)):
                msg.append(aestat.write_card(size, is_double))

            for (unused_id, aelist) in sorted(iteritems(self.aelists)):
                msg.append(aelist.write_card(size, is_double))
            for (unused_id, aesurf) in sorted(iteritems(self.aesurf)):
                msg.append(aesurf.write_card(size, is_double))
            for (unused_id, aesurfs) in sorted(iteritems(self.aesurfs)):
                msg.append(aesurfs.write_card(size, is_double))
            for (unused_id, aefact) in sorted(iteritems(self.aefacts)):
                msg.append(aefact.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_static_aero(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the static aero cards"""
        if self.aeros or self.trims or self.divergs:
            msg = ['$STATIC AERO\n']
            # static aero
            if self.aeros:
                msg.append(self.aeros.write_card(size, is_double))
            for (unused_id, trim) in sorted(iteritems(self.trims)):
                msg.append(trim.write_card(size, is_double))
            for (unused_id, diverg) in sorted(iteritems(self.divergs)):
                msg.append(diverg.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _find_aero_location(self):
        # type: () -> Tuple[bool, bool]
        """Determines where the AERO card should be written"""
        write_aero_in_flutter = False
        write_aero_in_gust = False
        if self.aero:
            if self.flfacts or self.flutters or self.mkaeros:
                write_aero_in_flutter = True
            elif self.gusts:
                write_aero_in_gust = True
            else:
                # an AERO card exists, but no FLUTTER, FLFACT, MKAEROx or GUST card
                write_aero_in_flutter = True
        return write_aero_in_flutter, write_aero_in_gust

    def _write_flutter(self, bdf_file, size=8, is_double=False, write_aero_in_flutter=True):
        # type: (Any, int, bool, bool) -> None
        """Writes the flutter cards"""
        if (write_aero_in_flutter and self.aero) or self.flfacts or self.flutters or self.mkaeros:
            msg = ['$FLUTTER\n']
            if write_aero_in_flutter:
                msg.append(self.aero.write_card(size, is_double))
            for (unused_id, flutter) in sorted(iteritems(self.flutters)):
                msg.append(flutter.write_card(size, is_double))
            for (unused_id, flfact) in sorted(iteritems(self.flfacts)):
                msg.append(flfact.write_card(size, is_double))
            for mkaero in self.mkaeros:
                msg.append(mkaero.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_gust(self, bdf_file, size=8, is_double=False, write_aero_in_gust=True):
        # type: (Any, int, bool, bool) -> None
        """Writes the gust cards"""
        if (write_aero_in_gust and self.aero) or self.gusts:
            msg = ['$GUST\n']
            if write_aero_in_gust:
                for (unused_id, aero) in sorted(iteritems(self.aero)):
                    msg.append(aero.write_card(size, is_double))
            for (unused_id, gust) in sorted(iteritems(self.gusts)):
                msg.append(gust.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_common(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Write the common outputs so none get missed...

        Parameters
        ----------
        bdf_file : file
            the file object
        size : int (default=8)
            the field width
        is_double : bool (default=False)
            is this double precision

        Returns
        -------
        msg : str
            part of the bdf
        """
        self._write_rigid_elements(bdf_file, size, is_double)
        self._write_dmigs(bdf_file, size, is_double)
        self._write_loads(bdf_file, size, is_double)
        self._write_dynamic(bdf_file, size, is_double)
        self._write_aero(bdf_file, size, is_double)
        self._write_aero_control(bdf_file, size, is_double)
        self._write_static_aero(bdf_file, size, is_double)

        write_aero_in_flutter, write_aero_in_gust = self._find_aero_location()
        self._write_flutter(bdf_file, size, is_double, write_aero_in_flutter)
        self._write_gust(bdf_file, size, is_double, write_aero_in_gust)

        self._write_thermal(bdf_file, size, is_double)
        self._write_thermal_materials(bdf_file, size, is_double)

        self._write_constraints(bdf_file, size, is_double)
        self._write_optimization(bdf_file, size, is_double)
        self._write_tables(bdf_file, size, is_double)
        self._write_sets(bdf_file, size, is_double)
        self._write_superelements(bdf_file, size, is_double)
        self._write_contact(bdf_file, size, is_double)
        self._write_rejects(bdf_file, size, is_double)
        self._write_coords(bdf_file, size, is_double)

    def _write_constraints(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the constraint cards sorted by ID"""
        if self.suport or self.suport1:
            msg = ['$CONSTRAINTS\n']  # type: List[str]
            for suport in self.suport:
                msg.append(suport.write_card(size, is_double))
            for suport_id, suport in sorted(iteritems(self.suport1)):
                msg.append(suport.write_card(size, is_double))
            bdf_file.write(''.join(msg))

        if self.spcs or self.spcadds or self.spcoffs:
            #msg = ['$SPCs\n']
            #str_spc = str(self.spcObject) # old
            #if str_spc:
                #msg.append(str_spc)
            #else:
            msg = ['$SPCs\n']
            for (unused_id, spcadds) in sorted(iteritems(self.spcadds)):
                for spcadd in spcadds:
                    msg.append(str(spcadd))
            for (unused_id, spcs) in sorted(iteritems(self.spcs)):
                for spc in spcs:
                    msg.append(str(spc))
            for (unused_id, spcoffs) in sorted(iteritems(self.spcoffs)):
                for spc in spcoffs:
                    msg.append(str(spc))
            bdf_file.write(''.join(msg))

        if self.mpcs or self.mpcadds:
            msg = ['$MPCs\n']
            for (unused_id, mpcadds) in sorted(iteritems(self.mpcadds)):
                for mpcadd in mpcadds:
                    msg.append(str(mpcadd))
            for (unused_id, mpcs) in sorted(iteritems(self.mpcs)):
                for mpc in mpcs:
                    msg.append(mpc.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_contact(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the contact cards sorted by ID"""
        is_contact = (self.bcrparas or self.bctadds or self.bctparas
                      or self.bctsets or self.bsurf or self.bsurfs)
        if is_contact:
            msg = ['$CONTACT\n']  # type: List[str]
            for (unused_id, bcrpara) in sorted(iteritems(self.bcrparas)):
                msg.append(bcrpara.write_card(size, is_double))
            for (unused_id, bctadds) in sorted(iteritems(self.bctadds)):
                msg.append(bctadds.write_card(size, is_double))
            for (unused_id, bctpara) in sorted(iteritems(self.bctparas)):
                msg.append(bctpara.write_card(size, is_double))

            for (unused_id, bctset) in sorted(iteritems(self.bctsets)):
                msg.append(bctset.write_card(size, is_double))
            for (unused_id, bsurfi) in sorted(iteritems(self.bsurf)):
                msg.append(bsurfi.write_card(size, is_double))
            for (unused_id, bsurfsi) in sorted(iteritems(self.bsurfs)):
                msg.append(bsurfsi.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_coords(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the coordinate cards in a sorted order"""
        msg = []  # type: List[str]
        if len(self.coords) > 1:
            msg.append('$COORDS\n')
        for (unused_id, coord) in sorted(iteritems(self.coords)):
            if unused_id != 0:
                msg.append(coord.write_card(size, is_double))
        bdf_file.write(''.join(msg))

    def _write_dmigs(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the DMIG cards

        Parameters
        ----------
        size : int
            large field (16) or small field (8)

        Returns
        -------
        msg : str
            string representation of the DMIGs
        """
        msg = []  # type: List[str]
        for (unused_name, dmig) in sorted(iteritems(self.dmigs)):
            msg.append(dmig.write_card(size, is_double))
        for (unused_name, dmi) in sorted(iteritems(self.dmis)):
            msg.append(dmi.write_card(size, is_double))
        for (unused_name, dmij) in sorted(iteritems(self.dmijs)):
            msg.append(dmij.write_card(size, is_double))
        for (unused_name, dmiji) in sorted(iteritems(self.dmijis)):
            msg.append(dmiji.write_card(size, is_double))
        for (unused_name, dmik) in sorted(iteritems(self.dmiks)):
            msg.append(dmik.write_card(size, is_double))
        bdf_file.write(''.join(msg))

    def _write_dynamic(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the dynamic cards sorted by ID"""
        is_dynamic = (self.dareas or self.dphases or self.nlparms or self.frequencies or
                      self.methods or self.cMethods or self.tsteps or self.tstepnls or
                      self.transfer_functions or self.delays or self.rotors or self.tics)
        if is_dynamic:
            msg = ['$DYNAMIC\n']  # type: List[str]
            for (unused_id, method) in sorted(iteritems(self.methods)):
                msg.append(method.write_card(size, is_double))
            for (unused_id, cmethod) in sorted(iteritems(self.cMethods)):
                msg.append(cmethod.write_card(size, is_double))
            for (unused_id, darea) in sorted(iteritems(self.dareas)):
                msg.append(darea.write_card(size, is_double))
            for (unused_id, dphase) in sorted(iteritems(self.dphases)):
                msg.append(dphase.write_card(size, is_double))
            for (unused_id, nlparm) in sorted(iteritems(self.nlparms)):
                msg.append(nlparm.write_card(size, is_double))
            for (unused_id, nlpci) in sorted(iteritems(self.nlpcis)):
                msg.append(nlpci.write_card(size, is_double))
            for (unused_id, tstep) in sorted(iteritems(self.tsteps)):
                msg.append(tstep.write_card(size, is_double))
            for (unused_id, tstepnl) in sorted(iteritems(self.tstepnls)):
                msg.append(tstepnl.write_card(size, is_double))
            for (unused_id, freqs) in sorted(iteritems(self.frequencies)):
                for freq in freqs:
                    msg.append(freq.write_card(size, is_double))
            for (unused_id, delay) in sorted(iteritems(self.delays)):
                msg.append(delay.write_card(size, is_double))
            for (unused_id, rotor) in sorted(iteritems(self.rotors)):
                msg.append(rotor.write_card(size, is_double))
            for (unused_id, tic) in sorted(iteritems(self.tics)):
                msg.append(tic.write_card(size, is_double))

            for (unused_id, tfs) in sorted(iteritems(self.transfer_functions)):
                for tf in tfs:
                    msg.append(tf.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_loads(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the load cards sorted by ID"""
        if self.load_combinations or self.loads or self.tempds:
            msg = ['$LOADS\n']
            for (key, load_combinations) in sorted(iteritems(self.load_combinations)):
                for load_combination in load_combinations:
                    try:
                        msg.append(load_combination.write_card(size, is_double))
                    except:
                        print('failed printing load...type=%s key=%r'
                              % (load_combination.type, key))
                        raise
            for (key, loadcase) in sorted(iteritems(self.loads)):
                for load in loadcase:
                    try:
                        msg.append(load.write_card(size, is_double))
                    except:
                        print('failed printing load...type=%s key=%r'
                              % (load.type, key))
                        raise
            for key, tempd in sorted(iteritems(self.tempds)):
                msg.append(tempd.write_card(size, is_double))
            bdf_file.write(''.join(msg))
        self._write_dloads(bdf_file, size=size, is_double=is_double)

    def _write_dloads(self, bdf_file, size=8, is_double=False):
    # type: (Any, int, bool) -> None
        """Writes the dload cards sorted by ID"""
        if self.dloads or self.dload_entries:
            msg = ['$DLOADS\n']
            for (key, loadcase) in sorted(iteritems(self.dloads)):
                for load in loadcase:
                    try:
                        msg.append(load.write_card(size, is_double))
                    except:
                        print('failed printing load...type=%s key=%r'
                              % (load.type, key))
                        raise

            for (key, loadcase) in sorted(iteritems(self.dload_entries)):
                for load in loadcase:
                    try:
                        msg.append(load.write_card(size, is_double))
                    except:
                        print('failed printing load...type=%s key=%r'
                              % (load.type, key))
                        raise
            bdf_file.write(''.join(msg))


    def _write_masses(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the mass cards sorted by ID"""
        if self.properties_mass:
            bdf_file.write('$PROPERTIES_MASS\n')
            for (pid, mass) in sorted(iteritems(self.properties_mass)):
                try:
                    bdf_file.write(mass.write_card(size, is_double))
                except:
                    print('failed printing mass property...'
                          'type=%s eid=%s' % (mass.type, pid))
                    raise

        if self.masses:
            bdf_file.write('$MASSES\n')
            for (eid, mass) in sorted(iteritems(self.masses)):
                try:
                    bdf_file.write(mass.write_card(size, is_double))
                except:
                    print('failed printing masses...'
                          'type=%s eid=%s' % (mass.type, eid))
                    raise

    def _write_materials(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the materials in a sorted order"""
        is_materials = (self.materials or self.hyperelastic_materials or self.creep_materials or
                        self.MATS1 or self.MATS3 or self.MATS8 or self.MATT1 or
                        self.MATT2 or self.MATT3 or self.MATT4 or self.MATT5 or
                        self.MATT8 or self.MATT9)
        if is_materials:
            msg = ['$MATERIALS\n']  # type: List[str]
            for (unused_mid, material) in sorted(iteritems(self.materials)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.hyperelastic_materials)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.creep_materials)):
                msg.append(material.write_card(size, is_double))

            for (unused_mid, material) in sorted(iteritems(self.MATS1)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATS3)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATS8)):
                msg.append(material.write_card(size, is_double))

            for (unused_mid, material) in sorted(iteritems(self.MATT1)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT2)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT3)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT4)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT5)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT8)):
                msg.append(material.write_card(size, is_double))
            for (unused_mid, material) in sorted(iteritems(self.MATT9)):
                msg.append(material.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_nodes(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the NODE-type cards"""
        if self.spoints:
            msg = []  # type: List[str]
            msg.append('$SPOINTS\n')
            msg.append(write_xpoints('SPOINT', self.spoints.keys()))
            bdf_file.write(''.join(msg))
        if self.epoints:
            msg = []
            msg.append('$EPOINTS\n')
            msg.append(write_xpoints('EPOINT', self.epoints.keys()))
            bdf_file.write(''.join(msg))
        if self.points:
            msg = []
            msg.append('$POINTS\n')
            for point_id, point in sorted(iteritems(self.points)):
                msg.append(point.write_card(size, is_double))
            bdf_file.write(''.join(msg))
        if self.axic:
            bdf_file.write(self.axic.write_card(size, is_double))
            for nid, ringax_pointax in iteritems(self.ringaxs):
                bdf_file.write(ringax_pointax.write_card(size, is_double))

        self._write_grids(bdf_file, size=size, is_double=is_double)
        if self.seqgp:
            bdf_file.write(self.seqgp.write_card(size, is_double))

        #if 0:  # not finished
            #self._write_nodes_associated(bdf_file, size, is_double)

    def _write_grids(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the GRID-type cards"""
        if self.nodes:
            msg = []
            msg.append('$NODES\n')
            if self.grdset:
                msg.append(self.grdset.print_card(size))

            if self.is_long_ids:
                for (unused_nid, node) in sorted(iteritems(self.nodes)):
                    msg.append(node.write_card_16(is_double))
            else:
                for (unused_nid, node) in sorted(iteritems(self.nodes)):
                    msg.append(node.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    #def _write_nodes_associated(self, bdf_file, size=8, is_double=False):
        #"""
        #Writes the NODE-type in associated and unassociated groups.

        #.. warning:: Sometimes crashes, probably on invalid BDFs.
        #"""
        #msg = []
        #associated_nodes = set([])
        #for (eid, element) in iteritems(self.elements):
            #associated_nodes = associated_nodes.union(set(element.node_ids))

        #all_nodes = set(self.nodes.keys())
        #unassociated_nodes = list(all_nodes.difference(associated_nodes))
        ##missing_nodes = all_nodes.difference(

        ## TODO: this really shouldn't be a list...???
        #associated_nodes = list(associated_nodes)

        #if associated_nodes:
            #msg += ['$ASSOCIATED NODES\n']
            #if self.grdset:
                #msg.append(self.grdset.write_card(size, is_double))
            ## TODO: this really shouldn't be a dictionary...???
            #for key, node in sorted(iteritems(associated_nodes)):
                #msg.append(node.write_card(size, is_double))

        #if unassociated_nodes:
            #msg.append('$UNASSOCIATED NODES\n')
            #if self.grdset and not associated_nodes:
                #msg.append(self.grdset.write_card(size, is_double))
            #for key, node in sorted(iteritems(unassociated_nodes)):
                #if key in self.nodes:
                    #msg.append(node.write_card(size, is_double))
                #else:
                    #msg.append('$ Missing NodeID=%s' % key)
        #bdf_file.write(''.join(msg))

    def _write_optimization(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the optimization cards sorted by ID"""
        is_optimization = (self.dconadds or self.dconstrs or self.desvars or self.ddvals or
                           self.dresps or
                           self.dvprels or self.dvmrels or self.dvcrels or self.doptprm or
                           self.dlinks or self.dequations or self.dtable is not None or
                           self.dvgrids or self.dscreen)
        if is_optimization:
            msg = ['$OPTIMIZATION\n']  # type: List[str]
            for (unused_id, dconadd) in sorted(iteritems(self.dconadds)):
                msg.append(dconadd.write_card(size, is_double))
            for (unused_id, dconstrs) in sorted(iteritems(self.dconstrs)):
                for dconstr in dconstrs:
                    msg.append(dconstr.write_card(size, is_double))
            for (unused_id, desvar) in sorted(iteritems(self.desvars)):
                msg.append(desvar.write_card(size, is_double))
            for (unused_id, ddval) in sorted(iteritems(self.ddvals)):
                msg.append(ddval.write_card(size, is_double))
            for (unused_id, dlink) in sorted(iteritems(self.dlinks)):
                msg.append(dlink.write_card(size, is_double))
            for (unused_id, dresp) in sorted(iteritems(self.dresps)):
                msg.append(dresp.write_card(size, is_double))

            for (unused_id, dvcrel) in sorted(iteritems(self.dvcrels)):
                msg.append(dvcrel.write_card(size, is_double))
            for (unused_id, dvmrel) in sorted(iteritems(self.dvmrels)):
                msg.append(dvmrel.write_card(size, is_double))
            for (unused_id, dvprel) in sorted(iteritems(self.dvprels)):
                msg.append(dvprel.write_card(size, is_double))
            for (unused_id, dvgrids) in sorted(iteritems(self.dvgrids)):
                for dvgrid in dvgrids:
                    msg.append(dvgrid.write_card(size, is_double))
            for (unused_id, dscreen) in sorted(iteritems(self.dscreen)):
                msg.append(str(dscreen))

            for (unused_id, equation) in sorted(iteritems(self.dequations)):
                msg.append(str(equation))

            if self.dtable is not None:
                msg.append(self.dtable.write_card(size, is_double))
            if self.doptprm is not None:
                msg.append(self.doptprm.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_params(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the PARAM cards
        """
        if self.params or self.dti:
            msg = ['$PARAMS\n']  # type: List[str]
            for name, dti in sorted(iteritems(self.dti)):
                msg.append(dti.write_card(size=size, is_double=is_double))

            if self.is_long_ids:
                for (unused_key, param) in sorted(iteritems(self.params)):
                    msg.append(param.write_card(16, is_double))
            else:
                for (unused_key, param) in sorted(iteritems(self.params)):
                    msg.append(param.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_properties(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the properties in a sorted order"""
        if self.properties:
            msg = ['$PROPERTIES\n']  # type: List[str]
            prop_groups = (self.properties, self.pelast, self.pdampt, self.pbusht)
            if self.is_long_ids:
                for prop_group in prop_groups:
                    for unused_pid, prop in sorted(iteritems(prop_group)):
                        msg.append(prop.write_card_16(is_double))
                #except:
                    #print('failed printing property type=%s' % prop.type)
                    #raise
            else:
                for prop_group in prop_groups:
                    for unused_pid, prop in sorted(iteritems(prop_group)):
                        msg.append(prop.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_rejects(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """
        Writes the rejected (processed) cards and the rejected unprocessed
        cardlines
        """
        if size == 8:
            print_func = print_card_8
        else:
            print_func = print_card_16
        msg = []  # type: List[str]
        if self.reject_cards:
            msg.append('$REJECTS\n')
            for reject_card in self.reject_cards:
                try:
                    msg.append(print_func(reject_card))
                except RuntimeError:
                    for field in reject_card:
                        if field is not None and '=' in field:
                            raise SyntaxError('cannot reject equal signed '
                                              'cards\ncard=%s\n' % reject_card)
                    raise

        if self.rejects:
            msg.append('$REJECT_LINES\n')
        for reject_lines in self.reject_lines:
            if isinstance(reject_lines, (list, tuple)):
                for reject in reject_lines:
                    reject2 = reject.rstrip()
                    if reject2:
                        msg.append('%s\n' % reject2)
            elif isinstance(reject_lines, string_types):
                reject2 = reject_lines.rstrip()
                if reject2:
                    msg.append('%s\n' % reject2)
            else:
                raise TypeError(reject_lines)
        bdf_file.write(''.join(msg))

    def _write_rigid_elements(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the rigid elements in a sorted order"""
        if self.rigid_elements:
            bdf_file.write('$RIGID ELEMENTS\n')
            if self.is_long_ids:
                for (eid, element) in sorted(iteritems(self.rigid_elements)):
                    try:
                        bdf_file.write(element.write_card_16(is_double))
                    except:
                        print('failed printing element...'
                              'type=%s eid=%s' % (element.type, eid))
                        raise
            else:
                for (eid, element) in sorted(iteritems(self.rigid_elements)):
                    try:
                        bdf_file.write(element.write_card(size, is_double))
                    except:
                        print('failed printing element...'
                              'type=%s eid=%s' % (element.type, eid))
                        raise
        if self.plotels:
            bdf_file.write('$PLOT ELEMENTS\n')
            for (eid, element) in sorted(iteritems(self.plotels)):
                bdf_file.write(element.write_card(size, is_double))

    def _write_sets(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the SETx cards sorted by ID"""
        is_sets = (self.sets or self.asets or self.bsets or self.csets or self.qsets
                   or self.usets)
        if is_sets:
            msg = ['$SETS\n']  # type: List[str]
            for (unused_id, set_obj) in sorted(iteritems(self.sets)):  # dict
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.asets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.bsets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.csets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.qsets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for name, usets in sorted(iteritems(self.usets)):  # dict
                for set_obj in usets:  # list
                    msg.append(set_obj.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_superelements(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the SETx cards sorted by ID"""
        is_sets = (self.se_sets or self.se_bsets or self.se_csets or self.se_qsets
                   or self.se_usets)
        if is_sets:
            msg = ['$SUPERELEMENTS\n']  # type: List[str]
            for set_obj in self.se_bsets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.se_csets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for set_obj in self.se_qsets:  # list
                msg.append(set_obj.write_card(size, is_double))
            for (set_id, set_obj) in sorted(iteritems(self.se_sets)):  # dict
                msg.append(set_obj.write_card(size, is_double))
            for name, usets in sorted(iteritems(self.se_usets)):  # dict
                for set_obj in usets:  # list
                    msg.append(set_obj.write_card(size, is_double))
            for suport in self.se_suport:  # list
                msg.append(suport.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_tables(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the TABLEx cards sorted by ID"""
        if self.tables or self.tables_d or self.tables_m or self.tables_sdamping:
            msg = ['$TABLES\n']  # type: List[str]
            for (unused_id, table) in sorted(iteritems(self.tables)):
                msg.append(table.write_card(size, is_double))
            for (unused_id, table) in sorted(iteritems(self.tables_d)):
                msg.append(table.write_card(size, is_double))
            for (unused_id, table) in sorted(iteritems(self.tables_m)):
                msg.append(table.write_card(size, is_double))
            for (unused_id, table) in sorted(iteritems(self.tables_sdamping)):
                msg.append(table.write_card(size, is_double))
            bdf_file.write(''.join(msg))

        if self.random_tables:
            msg = ['$RANDOM TABLES\n']
            for (unused_id, table) in sorted(iteritems(self.random_tables)):
                msg.append(table.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_thermal(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the thermal cards"""
        # PHBDY
        if self.phbdys or self.convection_properties or self.bcs:
            # self.thermalProperties or
            msg = ['$THERMAL\n']

            for (unused_key, phbdy) in sorted(iteritems(self.phbdys)):
                msg.append(phbdy.write_card(size, is_double))

            #for unused_key, prop in sorted(iteritems(self.thermalProperties)):
            #    msg.append(str(prop))
            for (unused_key, prop) in sorted(iteritems(self.convection_properties)):
                msg.append(prop.write_card(size, is_double))

            # BCs
            for (unused_key, bcs) in sorted(iteritems(self.bcs)):
                for boundary_condition in bcs:  # list
                    msg.append(boundary_condition.write_card(size, is_double))
            bdf_file.write(''.join(msg))

    def _write_thermal_materials(self, bdf_file, size=8, is_double=False):
        # type: (Any, int, bool) -> None
        """Writes the thermal materials in a sorted order"""
        if self.thermal_materials:
            msg = ['$THERMAL MATERIALS\n']
            for (unused_mid, material) in sorted(iteritems(self.thermal_materials)):
                msg.append(material.write_card(size, is_double))
            bdf_file.write(''.join(msg))

