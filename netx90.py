"""

MIT License

Copyright (c) 2021 Omid Kompani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import logging
logging.basicConfig(level=logging.ERROR,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

from eds_pie import eds_pie, EDS_PIE_ENUMS
import struct

class EDS_TRIGGER_AND_TRANSPORT(EDS_PIE_ENUMS):
    CLASS_0          = 1 << 0
    CLASS_1          = 1 << 1
    CLASS_2          = 1 << 2
    CLASS_3          = 1 << 3
    CLASS_4          = 1 << 4
    CLASS_5          = 1 << 5
    CLASS_6          = 1 << 6
    CYCLIC          = 1 << 16
    CHANGE_OF_STATE = 1 << 17
    APPLICATION     = 1 << 18
    LISTEN_ONLY     = 1 << 24
    INPUT_ONLY      = 1 << 25
    EXCLUSIVE_OWNER = 1 << 26
    REDUNDANT_OWNER = 1 << 27

class EDS_CONNECTION_PARAMETERS(EDS_PIE_ENUMS):
    O2T_FIXED_SIZE_SUPPORTED        = 1 << 0
    O2T_VARIABLE_SIZE_SUPPORTED     = 1 << 1
    T2O_FIXED_SIZE_SUPPORTED        = 1 << 2
    T2O_VARIABLE_SIZE_SUPPORTED     = 1 << 3
    O2T_REAL_TIME_TRANSFER_FORMAT   = (1 << 8) | (1 << 9) | (1 << 10)
    T2O_REAL_TIME_TRANSFER_FORMAT   = (1 << 12) | (1 << 13) | (1 << 14)
    O2T_CONNECTION_TYPE_NULL        = 1 << 16
    O2T_CONNECTION_TYPE_MULTICAST   = 1 << 17
    O2T_CONNECTION_TYPE_POINT2POINT = 1 << 18
    T2O_CONNECTION_TYPE_NULL        = 1 << 20
    T2O_CONNECTION_TYPE_MULTICAST   = 1 << 21
    T2O_CONNECTION_TYPE_POINT2POINT = 1 << 22
    O2T_PRIORITY_LOW                = 1 << 24
    O2T_PRIORITY_HIGH               = 1 << 25
    O2T_PRIORITY_SCHEDULED          = 1 << 26
    O2T_PRIORITY_URGENT             = 1 << 27
    T2O_PRIORITY_LOW                = 1 << 28
    T2O_PRIORITY_HIGH               = 1 << 29
    T2O_PRIORITY_SCHEDULED          = 1 << 30
    T2O_PRIORITY_URGENT             = 1 << 31

class EDS_REALTIME_TRANSFER_FORMAT(EDS_PIE_ENUMS):
    MODELESS        = 1 << 0
    ZERO_SIZE_DATA  = 1 << 1
    RESERVED        = 1 << 2
    HEARTBIT        = 1 << 3
    RUN_IDLE_HEADER = 1 << 4
    SAFETY          = 1 << 5

def demo():

    with open('netx90.eds', 'r') as edssourcefile:
        eds_content = edssourcefile.read()
    eds = eds_pie.parse(eds_content, showprogress = False)
    if eds.protocol == 'EtherNetIP':

        #eds.list('params')
        #index = 0
        #while(True):
        #    index += 1
        #    entry_name = "connection%d" %index
        #    field = eds.getfield("connection manager", entry_name, fieldname = "Trigger and transport")
        #    if field:
        #        if field.value & (1<<26):
        #            data_size = eds.getfield("connection manager", entry_name, fieldindex = 10).value
        #            path = eds.pack_path(eds.getfield("connection manager", entry_name, fieldindex = 14).value)
        #            break
        #    else: break

        index = 0
        trigger_transport_bits = sorted([val for key, val in EDS_TRIGGER_AND_TRANSPORT.__dict__.items() if '__' not in key])
        connection_parameters = sorted([val for key, val in EDS_CONNECTION_PARAMETERS.__dict__.items() if '__' not in key])
        RT_format = sorted([val for key, val in EDS_REALTIME_TRANSFER_FORMAT.__dict__.items() if '__' not in key])
        while(True):
            index += 1
            entry = eds.getentry('connection manager', 'connection{}'.format(index))
            if entry:
                print '   ', entry
                field = entry.getfield(0) # Trigger and Transport
                print '        Trigger and Transport type'
                print '        --------------------------'
                for mask in trigger_transport_bits:
                    if mask & field.value:
                        print '        {}'.format(EDS_TRIGGER_AND_TRANSPORT.Str(mask))
                print '        Connetion parameters'
                print '        --------------------'
                field = entry.getfield(1) # Connection parameters
                for mask in connection_parameters:
                    if EDS_CONNECTION_PARAMETERS.O2T_REAL_TIME_TRANSFER_FORMAT == mask:
                        print '        {}'.format(EDS_CONNECTION_PARAMETERS.Str(mask))
                        for f in RT_format:
                            if f & ((EDS_CONNECTION_PARAMETERS.O2T_REAL_TIME_TRANSFER_FORMAT & field.value) >> 8):
                                print '            {}'.format(EDS_REALTIME_TRANSFER_FORMAT.Str(f))
                    elif EDS_CONNECTION_PARAMETERS.T2O_REAL_TIME_TRANSFER_FORMAT == mask:
                        print '        {}'.format(EDS_CONNECTION_PARAMETERS.Str(mask))
                        for f in RT_format:
                            if f & ((EDS_CONNECTION_PARAMETERS.T2O_REAL_TIME_TRANSFER_FORMAT & field.value) >> 12):
                                print '            {}'.format(EDS_REALTIME_TRANSFER_FORMAT.Str(f))
                    elif mask & field.value:
                        print '        {}'.format(EDS_CONNECTION_PARAMETERS.Str(mask))


                print '        O->T RPI: {}'.format(entry.getfield(2).value)
                print '        O->T Size: {}'.format(entry.getfield(3).value)
                print '        O->T format: {}'.format(entry.getfield(4).value)
                print '        T->O RPI: {}'.format(entry.getfield(5).value)
                print '        T->O Size: {}'.format(entry.getfield(6).value)
                print '        T->O format: {}'.format(entry.getfield(7).value)
                if EDS_TRIGGER_AND_TRANSPORT.EXCLUSIVE_OWNER & field.value:
                    path = entry.getfield(14).value
                    #print(path)
                    path = eds.resolve_epath(path)
                    #print(path)
                    path = ''.join(struct.pack('B', int(item, 16)) for item in path.split())
            else:
                break

#def resolvepath(self, path):
#    items = path.split()
#    for index, item in enumerate(items):
#        if len(item) < 2:
#            logger.error('Invalid EPATH format! item[{}]:\"{}\" in [{}]'.format(index, item, path))
#
#        if not isnumber(item):
#            if item[0] == '[' and item[-1] == ']':
#                entryname = item.strip('[]').lower()
#                field = self.getfield('Params', entryname, fieldname = 'Default Value') #TODO: requires improvement
#                if field:
#                    items[index] = int(field.value)
#                    continue
#                logger.error('Entry not found! item[{}]:\"{}\" in [{}]'.format(index, item, path))
#            # ? Error(ERRORS.ERR_INVALID_EPATH_FORMAT, 'item[{}]:\"{}\" in [{}]: '
#            # ?      .format(index, item, path))
#        elif not ishex(item):
#            logger.error('Invalid EPATH format! item[{}]:\"{}\" in [{}]'.format(index, item, path))
#
#        items[index] = int(item, 16)
#    return ' '.join('{:02X}'.format(item) for item in items)
#
#def packpath(self, path):
#    path = self.resolve_path(path)
#    items = path.split()
#    return ''.join((struct.pack('B', int(item, 16)) for item in items))


if __name__ == "__main__":
    demo()
