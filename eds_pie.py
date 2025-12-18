
import os
import sys
import inspect
import struct
import numbers
import json

from datetime import datetime, date, time
from string   import digits
from eds_parser import Parser
import cip_eds_types as EDS_Types


import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)
#-------------------------------------------------------------------------------
EDS_PIE_VERSION     = '0.1'
EDS_PIE_RELASE_DATE = '3 Nov. 2020'

#-------------------------------------------------------------------------------
END_COMMENT_TEMPLATE = ( ' '.ljust(79, '-') + '\n' + ' EOF \n'
                      + ' '.ljust(79, '-') + '\n' )

HEADING_COMMENT_TEMPLATE = ( ' Electronic Data Sheet Generated with EDS-pie Version '
                         +   '{} - {}\n'.format(EDS_PIE_VERSION, EDS_PIE_RELASE_DATE)
                         +   ' '.ljust(79, '-') + '\n'
                         +   ' Created on: {} - {}:{}\n'.format(str(date.today()),
                                 str(datetime.now().hour), str(datetime.now().minute))
                         +   ' '.ljust(79, '-') + '\n\n ATTENTION: \n'
                         +   ' Changes in this file may cause configuration or '
                         +   'communication problems.\n\n' + ' '.ljust(79, '-')
                         +   '\n' )
# ------------------------------------------------------------------------------





class eds_pie(object):

    @staticmethod
    def parse(eds_content = '', showprogress = True):

        eds = parser(eds_content, showprogress).parse()
        eds.semantic_check()
        # setting the protocol
        eds._protocol = 'Generic'

        if eds.get_section('Device Classification').entries:
            field = eds.get_section('Device Classification').entries[0].get_field(0)
            if field:
                eds._protocol = field.value

        eds.semantic_check()
        if showprogress: print('')
        return eds


class CIP_EDS():
    def __new__(cls, eds_data):
        return Parser(eds_data).parse()


