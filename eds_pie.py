'''

MIT License

Copyright (c) 2021 Omid Kompani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

'''
    EDS grammatics:
    ---------------

    OPERATOR
        {=}

    SEPARATOR
        {,;-:}

    EOL
        \n

    STRING
        {ASCII symbols}

    NUMBER
        {.0-9}

    HEXNUMBER
        0x{0-9a-fA-F}

    CIP_DATE
        mm'-'dd'-'yyyy
        [m,d,y] = NUMBER/HEXNUMBER

    CIP_TIME
        hh':'mm':'ss
        [h,m,s] = NUMBER/HEXNUMBER

    COMMENT
        $ {ASCII symbols} EOL

    HEADER_COMMENT
        COMMENT

    FOOTER_COMMENT
        {ASCII symbols} COMMENT

    IDENTIFIER
        {a-zA-Z0-9_}

    DATASET
        '{'...,...,...'}'

    KEYWORD
        IDENTIFIER

    SECTION_IDENTIFIER
        '[' {a-zA-Z0-9_/- } ']'
        ***Note: the SYMBOLS '/' , '-' and ' ' should be used non-consecutive
        ***Note: A public section identifier shall never begin with a number
        ***Note: A vendor specific section identifier shall always begin with
                the vendor Id of the company making the addition followed by an
                underscore. VendorID_VendorSpecificKeyword

    KEYWORDVALUE (or keyword data field)
        NUMBER | STRING | IDENTIFIER | VSIDENTIFIER| CIP_DATE | CIP_TIME
      | DATASET

    ENTRY
        KEYWORD '=' KEYWORDVALUE {',' KEYWORDVALUE} ';'

    SECTION
        HEADRCOMMENT
        SECTION_IDENTIFIER FOOTERCOMENT
        { HEADRCOMMENT
            ENTRY = { HEADRCOMMENT
                        KEYWORDVALUE }  FOOTERCOMENT }
'''

import os
import sys
import inspect
import struct
import logging
import numbers

from collections import namedtuple
from datetime    import datetime, date, time
from string      import digits

from eds_libs import *
from cip_types import isnumber, ishex

logging.basicConfig(level=logging.WARNING,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)
#-------------------------------------------------------------------------------
EDS_PIE_VERSION     = '0.1'
EDS_PIE_RELASE_DATE = '3 Nov. 2020'
SECTION_NAME_VALID_SYMBOLES = '-.\\_/'
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
class EDS_PIE_ENUMS(object):

    def Str(self, enum):
        for attr in vars(self.__class__):
            if isinstance(self.__class__.__dict__[attr], int) and self.__class__.__dict__[attr] == enum: return '{}'.format(attr)
        for base in self.__class__.__bases__:
            for attr in vars(base):
                if isinstance(base.__dict__[attr], int) and base.__dict__[attr] == enum: return '{}'.format(attr)
        return ''

    @classmethod
    def Str(cls, enum):
        for attr in vars(cls):
            if isinstance(cls.__dict__[attr], int) and cls.__dict__[attr] == enum: return '{}'.format(attr)
        for base in cls.__bases__:
            for attr in vars(base):
                if isinstance(base.__dict__[attr], int) and base.__dict__[attr] == enum: return '{}'.format(attr)
        return ''

class TOKEN_TYPES(EDS_PIE_ENUMS):
    DATE       =  1
    TIME       =  2
    NUMBER     =  3
    STRING     =  4
    COMMENT    =  5
    SECTION    =  6
    OPERATOR   =  7
    SEPARATOR  =  8
    IDENTIFIER =  9
    DATASET    =  10

class SYMBOLS(EDS_PIE_ENUMS):
    ASSIGNMENT     = '='
    COMMA          = ','
    SEMICOLON      = ';'
    COLON          = ':'
    MINUS          = '-'
    UNDERLINE      = '_'
    PLUS           = '+'
    POINT          = '.'
    BACKSLASH      = '\\'
    QUOTATION      = '\"'
    TAB            = '\t'
    DOLLAR         = '$'
    OPENINGBRACKET = '['
    CLOSINGBRACKET = ']'
    OPENINGBRACE   = '{'
    CLOSINGBRACE   = '}'
    AMPERSAND      = '&'
    SPACE          = ' '
    EOL            = '\n'
    EOF            = None

OPERATORS  = [ SYMBOLS.ASSIGNMENT ]
SEPARATORS = [ SYMBOLS.COMMA, SYMBOLS.SEMICOLON ]


class EDS_Section(object):
    _instancecount = -1
    def __init__(self, eds, name, id = 0):
        type(self)._instancecount += 1
        self._eds        = eds
        self._index      = type(self)._instancecount
        self._id         = id
        self._name       = name
        self._entries    = {}
        self.hcomment    = ''
        self.fcomment    = ''

    @property
    def name(self):
        return self._name

    @property
    def entrycount(self):
        return len(self._entries)

    @property
    def entries(self):
        return tuple(self._entries.values())

    def addentry(self, entryname, serialize = False):
        return self._eds.addentry(self._name, entryname)

    def has_entry(self, entryname = None, entryindex = None):
        if entryname.replace(' ', '').lower() in self._entries.keys():
            return True
        return False

    def getentry(self, entryname = None, entryindex = None):
        return self._entries.get(entryname.replace(' ', '').lower())

    def getfield(self, entryname, fieldindex = 0, fieldname = ''):
        entry = self._entries.get(entryname.replace(' ', '').lower())
        if entry:
            if fieldname is not None and fieldname != '':
                for field in entry.fields:
                    if field.name.replace(' ', '').lower() == fieldname.replace(' ', '').lower():
                        return field
            if fieldindex < entry.fieldcount: return entry.fields[fieldindex] # TODO: test
        return None

    def __str__(self):
        return 'SECTION({})'.format(self._name)

# --------------------------------------------------------------------------
class EDS_Entry(object):

    def __init__(self, section, name, index):
        self._index   = index
        self._section = section
        self._name    = name
        self._fields  = [] # Fields are implemented as a list. Not the same as sections and entries
        self.hcomment = ''
        self.fcomment = ''

    def addfield(self, fieldvalue, datatype = None):
        return self._section._eds.addfield(self._section.name, self._name, fieldvalue, datatype)

    def hasfield(self, fieldindex = 0, fieldname = ''):
        if fieldname != '':
            for field in self._fields:
                if fieldname.replace(' ', '').lower() == field.name.replace(' ', '').lower():
                    return True
            return False
        if fieldindex < self.fieldcount:
            return True
        return False

    def getfield(self, fieldindex = 0, fieldname = ''):
        if fieldname != '':
            for field in self._fields:
                if fieldname.replace(' ', '').lower() == field.name.replace(' ', '').lower():
                    return field
            return None
        if fieldindex < self.fieldcount:
            return self.fields[fieldindex]
        return None
    @property
    def name(self):
        return self._name

    @property
    def fieldcount(self):
        return len(self._fields)

    @property
    def fields(self):
        return tuple(self._fields)

    def __str__(self):
        return 'ENTRY({})'.format(self._name)
# --------------------------------------------------------------------------
class EDS_Field(object):
    def __init__(self, entry, name, data, index):
        self._index     = index
        self._entry     = entry
        self._name      = name
        self._data      = data
        self._datatypes = []
        self.hcomment  = ''
        self.fcomment  = ''

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._data.value

    @value.setter
    def value(self, value):
        #TODO: requires improvements
        if type(self._data) != EMPTY or type(self._data) != EDS_UNDEFINED:
            if type(self._data).validate(value, self._data.range):
                self._data._value = value
                return
        if self._datatypes:
            for datatype, valid_data in self._datatypes:
                if datatype.validate(value, valid_data):
                    del self._data
                    self._data = datatype(value, valid_data)
                    return
        types_str = ', '.join('<{}>{}'.format(datatype.__name__, valid_data) for datatype, valid_data in self._datatypes)
        error_msg = ('Data_type mismatch! [{}].{}.{} = ({}), should be a type of: {}'
            .format(self._entry._section.name, self._entry.name, self.name, value, types_str))

        raise Exception(__name__ + ':> calling: \"{}()\" {}'.format(str(inspect.stack()[0][3]), error_msg))

    @property
    def datatype(self):
        return (type(self._data), self._data.range)

    def __str__(self):
        if self._data is None:
            return '\"\"'
        return 'FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})'.format(self._index, self._name, str(self._data), type(self._data).__name__, self._data.range)

# ------------------------------------------------------------------------------
class EDS(object):

    def __init__(self):
        self.heading_comment = ''
        self.end_comment = ''
        self._protocol  = None
        self._sections  = {}
        self.ref = CIP_EDS_lib()

    def list(self, sectionname = None, entryname = None):
        if sectionname is None and entryname is None:
            sections = sorted(self.sections, key = lambda section: section._index)
            for section in sections:
                print section
                entries = sorted(section.entries, key = lambda entry: entry._index)
                for entry in entries:
                    print '    ', entry
                    for field in entry.fields:
                        print '        ', field
            return

        if sectionname is not None and entryname is not None:
            entry = self.getentry(sectionname, entryname)
            if entry:
                print entry
                for field in entry.fields:
                    print '    ', field
            return

        if sectionname is not None and entryname is None:
            section = self.getsection(sectionname)
            if section:
                print section
                entries = sorted(section.entries, key = lambda entry: entry._index)
                for entry in entries:
                    print '    ', entry
                    for field in entry.fields:
                        print '        ', field
            return

    @property
    def protocol(self):
        return self._protocol

    @property
    def sections(self):
        return list(self._sections.values())

    def getsection(self, section):
        '''
        To get a section object by its EDS keyword or by its CIP classID.
        '''
        if isinstance(section, str):
            return self._sections.get(section.replace(' ', '').lower())
        if isinstance(section, numbers.Number):
            return self._sections.get(self.ref.get_section_name(section, self.protocol).replace(' ', '').lower())
        raise TypeError('Inappropriate data type: {}'.format(type(section)))

    def getentry(self, sectionname, entryname):
        if sectionname.replace(' ', '').lower() in self._sections.keys():
            return self._sections[sectionname.replace(' ', '').lower()].getentry(entryname)
        return None

    def getfield(self, sectionname, entryname, fieldindex = 0, fieldname = ''):
        entry = self.getentry(sectionname, entryname)
        if entry is not None:
            if fieldname is not None and fieldname != '':
                for field in entry.fields:
                    if field.name.replace(' ', '').lower() == fieldname.replace(' ', '').lower():
                        return field
            if fieldindex < entry.fieldcount:
                return entry.fields[fieldindex]
        return None

    def getvalue(self, sectionname, entryname, fieldindex = 0, fieldname = ''):
        entry = self.getentry(sectionname, entryname)
        if entry:
            if fieldname is not None and fieldname != '':
                for field in entry.fields:
                    if field.name.replace(' ', '').lower() == fieldname.replace(' ', '').lower():
                        return field.value
            return entry.fields[fieldindex].value
        return None

    def setvalue(self, sectionname, entryname, fieldindex, value):
        entry_ = self.getentry(sectionname, entryname)
        if entry_:
            entry_.fields[fieldindex].value = value

    def has_section(self, sectionname):
        if sectionname.replace(' ', '').lower() in self._sections.keys():
            return True
        return False

    def has_entry(self, sectionname, entryname):
        section = self.getsection(sectionname)
        if section:
            if entryname.replace(' ', '').lower() in section._entries.keys():
                return True
        return False

    def hasfield(self, sectionname, entryname, fieldindex):
        entry = self.getentry(sectionname, entryname)
        if entry:
            if fieldindex < entry.fieldcount:
                return True
        return False

    def addsection(self, sectionname):
        sectionkey = sectionname.replace(' ', '').lower()
        ref_id = 0

        if sectionkey == '':
            logger.error('Invalid section name! {} contains invalid characters'.format(sectionname))

        if sectionkey in self._sections.keys():
            logger.error('DUplicated section! [{}}'.format(sectionname))

        if not self.ref.has_section(sectionname):
            logger.warning('Unknown Section [{}]'.format(sectionname))
        else:
            ref_section = self.ref.get_section(sectionname)
            if ref_section:
                ref_section_key = ref_section.key
                ref_id = ref_section.id or 0
            if ref_section_key != sectionname:
                logger.warning('section name: [{}] should be: [{}]'.format(sectionname, ref_keyword))

            ## TODO: is it helpful?
            if ((ref_section_key == 'File' and len(self._sections) != 0) or
                (ref_section_key == 'Device' and len(self._sections) != 1)):
                logger.warning('Unexpected order of sections. Section [{}] found at '.format(sectionname))

            sectionname = ref_section.key

        section = EDS_Section(self, sectionname, ref_id)

        self._sections[sectionkey] = section

        return section

    def addentry(self, sectionname, entryname):

        section = self._sections[sectionname.replace(' ', '').lower()]

        if entryname == '':
            logger.error('Invalid Entry name! [{}]\"{}\" contains invalid characters.'
                .format(sectionname, entryname))
            return None

        if entryname.replace(' ', '').lower() in section._entries.keys():
            logger.error('Duplicated Entry! to serialize \"{}\", set the serialize switch to True'.format(entry))

        if not self.ref.has_entry(sectionname, entryname):
            logger.warning('Unknown Entry [{}].{}'.format(sectionname, entryname))

        # Correcting entry name
        ref_keyword = ''
        ref_entry = self.ref.get_entry(sectionname, entryname)
        if ref_entry:
            ref_keyword = ref_entry.key.rstrip('N').rstrip(digits)

        if ref_keyword != entryname.rstrip(digits):
            logger.warning('Not exact match! in section [{}], entry name: \"{}\" should be:'
                ' \"{}[N]\"'.format(sectionname, entryname, ref_keyword))

            entry_nid = entryname[len(ref_keyword):]
            entryname = ref_keyword + entry_nid

        entry = EDS_Entry(section, entryname, section.entrycount)

        section._entries[entryname.replace(' ', '').lower()] = entry

        return entry

    def addfield(self, sectionname, entryname, fieldvalue, fielddatatype = None):
        section = self.getsection(sectionname)
        if section is None:
            logger.error('Section not found! [{}]'.format(section._name))

        entry   = section.getentry(entryname)
        if entry is None:
            logger.error('Entry not found! [{}].{}'.format(sectionname, entryname))
        fielddata = None

        # getting the type info from eds dictionary
        ref_field = self.ref.get_field(section._name, entry.name, (entry.fieldcount))
        if ref_field:
            field_name = ref_field.name or entry.name
        else:
            field_name = 'field{}'.format(entry.fieldcount)

        datatypes = self.ref.get_field_datatypes(section._name, entry.name, field_name)
        if not datatypes:
            logger.warning('Unknown Field [{}].{}.{} = {}'.format(section._name, entry.name, field_name, fieldvalue))

        # Validating field value
        if fieldvalue != '' or self.ref.ismandatory(section._name, entry.name, field_name):
            for dtype, typeinfo in datatypes: # Getting the listed data types and their acceptable ranges
                if dtype.validate(fieldvalue, typeinfo):

                    if dtype == EDS_TYPEREF:
                        ''' A referenced-type has to be validated. Type this
                            filed comes from another field which is here named
                            The linked field contains a CIP type id '''

                        typeid = self.getfield(sectionname, entryname, fieldname = typeinfo[0]).value
                        try:
                            dtype = self.ref.gettype(typeid)
                            if dtype.validate(fieldvalue, []):
                                fielddata = dtype(fieldvalue, [])
                                break
                        except:

                            fielddata = EDS_UNDEFINED(fieldvalue)

                    else: # No TYPEREF
                        # creating type instance with field value

                        fielddata = dtype(fieldvalue, typeinfo)

            if fielddata is None: # No proper type was found
                if EDS_VENDORSPEC.validate(fieldvalue):
                    typelist = [(type, '') for type, typeinfo in datatypes if not typeinfo]
                    typelist += [(type, typeinfo) for type, typeinfo in datatypes if typeinfo]
                    types_str = ', '.join('<{}{}>'.format(type[0].__name__, type[1]) for type in typelist)
                    logger.warning('Type mismatch! [{}].{}.{} = ({}), should be a type of: {}. '
                    'Switched to VENDOR_SPECIFIC type.'.format(section._name, entry.name, field_name, fieldvalue, types_str))

                    fielddata = EDS_VENDORSPEC(fieldvalue)
                elif self.ref.ismandatory(section._name, entry.name, field_name):
                    typelist = [(type, '') for type, typeinfo in datatypes if not typeinfo]
                    typelist += [(type, typeinfo) for type, typeinfo in datatypes if typeinfo]
                    types_str = ', '.join('<{}{}>'.format(type[0].__name__, type[1]) for type in typelist)
                    logger.error('Data_type mismatch! [{}].{}.{} = ({}), should be a type of: {}'
                         .format(section._name, entry.name, field_name, fieldvalue, types_str))

                elif fieldvalue == '':
                    fielddata = EDS_EMPTY(fieldvalue)
                else:
                    fielddata = EDS_UNDEFINED(fieldvalue)
        else: # fieldvalue == ''
            fielddata = EDS_EMPTY(fieldvalue)


        field = EDS_Field(entry, field_name, fielddata, entry.fieldcount)

        field._datatypes = datatypes
        entry._fields.append(field)

        return field

    def removesection(self, sectionname, removetree = False):
        section = self.getsection(sectionname)

        if section is None: return
        if not section.entries:
            del self._sections[sectionname.replace(' ', '').lower()]
        elif removetree:
            for entry in section.entries:
                self.removeentry(sectionname, entry.name, removetree)
            del self._sections[sectionname.replace(' ', '').lower()]
        else:
            logger.error('Unable to remove section! [{}] contains one or more entries.'
                'Remove the entries first or use removetree = True'.format(section._name))

    def removeentry(self, sectionname, entryname, removetree = False):
        entry = self.getentry(sectionname, entryname)
        if entry is None: return
        if not entry.fields:
            section = self.getsection(sectionname)
            del section._entries[entryname.replace(' ', '').lower()]
        elif removetree:
            entry._fields = []
        else:
            logger.error('Unable to remove entry! [{}].{} contains one or more fields.'
                'Remove the fields first or use removetree = True'.format(section._name, entry.name))

    def removefield(self, sectionname, sentryname, fieldindex):
        pass

    def resolvepath(self, path):
        items = path.split()
        for index, item in enumerate(items):
            if len(item) < 2:
                logger.error('Invalid EPATH format! item[{}]:\"{}\" in [{}]'.format(index, item, path))

            if not isnumber(item):
                if item[0] == '[' and item[-1] == ']':
                    entryname = item.strip('[]').lower()
                    field = self.getfield('Params', entryname, fieldname = 'Default Value') #TODO: requires improvement
                    if field:
                        items[index] = int(field.value)
                        continue
                    logger.error('Entry not found! item[{}]:\"{}\" in [{}]'.format(index, item, path))
                # ? Error(ERRORS.ERR_INVALID_EPATH_FORMAT, 'item[{}]:\"{}\" in [{}]: '
                # ?      .format(index, item, path))
            elif not ishex(item):
                logger.error('Invalid EPATH format! item[{}]:\"{}\" in [{}]'.format(index, item, path))

            items[index] = int(item, 16)
        return ' '.join('{:02X}'.format(item) for item in items)

    def packpath(self, path):
        path = self.resolve_path(path)
        items = path.split()
        return ''.join((struct.pack('B', int(item, 16)) for item in items))

    def final_rollcall(self):
        requiredsections = self.ref.get_required_sections()
        for section in requiredsections:
            if self.has_section(section.keyword) == False:
                logger.error('Missing required section! [{}] \"{}\"'.format(section.keyword, section.name))

        for section in self.sections:
            requiredentries = self.ref.get_required_entries(section.name)
            for entry in requiredentries:
                if self.has_entry(section.name, entry.keyword) == False:
                    logger.error('Missing required entry! [{}].\"{}\"{}'
                        .format(section.name, entry.keyword, entry.name))

            for entry in section.entries:
                requiredfields = self.ref.get_required_fields(section.name, entry.name)
                for field in requiredfields:
                    if self.hasfield(section.name, entry.name, field.placement) == False:
                        logger.error('Missing required field! [{}].{}.{} #{}'
                            .format(section.name, entry.name, field.name, field.placement))

    def save(self, filename, overwrite = False):
        if os.path.isfile(filename) and overwrite == False:
            raise Exception('Failed to write to file! \"{}\" already exists and overrwite is not enabled.'.format(filename))

        eds_content = self.heading_comment
        if eds_content == '':
            for line in HEADING_COMMENT_TEMPLATE.splitlines():
                eds_content +='$ {}\n'.format(line.strip())

        # sections
        std_sections = [section for section in self.sections if section._id > 0x10000]
        std_sections = sorted(std_sections, key = lambda section: section._id)
        cip_sections = [section for section in self.sections if section._id < 0x10000]
        cip_sections = sorted(cip_sections, key = lambda section: section._id)
        sections = std_sections + cip_sections

        for section in sections:

            if section.hcomment != '':
                for linecomment in section.hcomment.splitlines():
                    eds_content += '$ {}\n'.format(linecomment.strip())

            eds_content += '\n[{}]'.format(section.name)

            if section.fcomment != '':
                for linecomment in section.fcomment.splitlines():
                    eds_content += '$ {}\n'.format(linecomment.strip())
            eds_content += '\n'

            # entries
            entries = sorted(section.entries, key = lambda entry: entry._index)
            for entry in entries:

                tabsize = 4
                if entry.hcomment != '':
                    for linecomment in entry.hcomment.splitlines():
                        eds_content += ''.ljust(tabsize, ' ') + '$ {}\n'.format(linecomment.strip())
                if entry.fcomment != '':
                    eds_content += ''.ljust(tabsize, ' ') + '    $ {}\n'.format(entry.fcomment)

                # fields
                tab = 4

                singleline_str = ''
                singleline_str += ''.ljust(tab, ' ') + '{} ='.format(entry.name)
                if entry.fieldcount == 1:
                    singleline_str += ' '
                else: # multiple fields
                    singleline_str += '\n'
                    singleline_str += ''.ljust(2 * tab, ' ')

                for fieldindex, field in enumerate(entry.fields):

                    # header comment
                    if field.hcomment != '':
                        for linecomment in field.hcomment.splitlines():
                            singleline_str +='$ {}\n'.format(linecomment.strip()) + ''.ljust(tab, ' ')

                    singleline_str += '{}'.format(field._data)

                    # separator
                    if (fieldindex + 1) == entry.fieldcount:
                        singleline_str += ';'
                    else:
                        singleline_str += ','

                    # footer comment
                    if field.fcomment != '':
                        singleline_str = singleline_str.ljust(20, ' ')
                        singleline_str += ' $ {}\n'.format(field.fcomment.strip())
                        eds_content += singleline_str
                        singleline_str = ''
                        if (fieldindex + 1) != entry.fieldcount:
                            singleline_str += ''.ljust(2 * tab, ' ')
                    #elif field.cr:
                    #    singleline_str += '\n'
                    #    eds_content += singleline_str
                    #    singleline_str = ''
                    #    if (fieldindex + 1) != entry.fieldcount:
                    #        singleline_str += ''.ljust(2 * tab, ' ')
                    #elif (fieldindex + 1) == entry.fieldcount:
                    #    eds_content += singleline_str
                    #    singleline_str = ''
                    #    singleline_str += '\n'
                    else:
                        singleline_str += '\n'
                        eds_content += singleline_str
                        singleline_str = ''
                        if (fieldindex + 1) != entry.fieldcount:
                            singleline_str += ''.ljust(2 * tab, ' ')
        # end comment
        if self.end_comment == '':
            self.end_comment = END_COMMENT_TEMPLATE
        for linecomment in self.end_comment.splitlines():
            eds_content +='$ {}\n'.format(linecomment.strip())
        hfile = open(filename, 'w')
        hfile.write(eds_content)
        hfile.close()

    def __str__(self):
        Msg = ''
        for section in self.__sections:
            Msg += '[%s]\n'%(section._name)
            for entry in section.entries:
                Msg += '     %s = '%(entry.name)
                for entryvalue in entry.fields:
                    Msg += '%s,'%(entryvalue.data)
                Msg += '\n'
        return Msg

    def get_cip_section_name(self, classid, protocol=None):
        if protocol is None:
            protocol = self.protocol
        return self.ref.get_section_name(classid, protocol)
# ---------------------------------------------------------------------------
class Token(object):

    def __init__(self, type = None, value = None, offset = None, line = None, col = None):
        self.type   = type
        self.value  = value
        self.offset = offset
        self.line   = line
        self.col    = col

    def __str__(self):
        return '[Ln: {}, Col: {}, Pos: {}] {} \"{}\"'.format(
            str(self.line).rjust(4),
            str(self.col).rjust(3),
            str(self.offset).rjust(5),
            TOKEN_TYPES.Str(self.type).ljust(11),
            self.value)
#---------------------------------------------------------------------------
class parser(object):
    def __init__(self, sourcetext, showprogress = False):

        self.edsstream  = sourcetext
        self.lastoffset = len(sourcetext) - 1
        self.offset     = -1
        self.line       = 1
        self.col        = 0

        self.eds       = EDS()
        self.token     = None
        self.prevtoken = None

        self.hcomment = ''
        self.fcomment = ''

        self.sectioninuse  = None
        self.entryinuse    = None
        self.actualelement = None

        self.showprogress = showprogress
        self.progress = 0.0

    def getchar(self):
        if self.showprogress:
            progress_step = float(float(self.lastoffset) / 100.0)
            self.progress += 1.0
            if self.progress % progress_step < 1.0:
                sys.stdout.write('Parsing... [%0.0f%%]                          \r' %(self.progress / progress_step) )
                sys.stdout.flush()
                sys.stdout.write('')
        if self.offset == self.lastoffset:
            return None

        self.offset += 1
        self.col += 1
        if self.edsstream[self.offset] == '\n':
            self.line += 1
            self.col = 0
        return self.edsstream[self.offset]

    def lookahead(self, offset = 1):
        if self.offset + offset > self.lastoffset:
            return None
        return self.edsstream[self.offset + offset]

    def lookbehind(self, offset = 1):
        if self.offset - offset < 0:
            return None
        return self.edsstream[self.offset - offset]

    def gettoken(self):
        ch = self.getchar()
        if ch is SYMBOLS.EOF:
            return None

        token = Token()
        while ch.isspace(): # including: space, tab, carriage return, new line
            ch = self.getchar()
            if ch is SYMBOLS.EOF:
                return None

        if ch == '$':
            token = Token(type = TOKEN_TYPES.COMMENT, value = '', offset = self.offset, line = self.line, col = self.col)
            while True:
                ch = self.getchar()
                if ch == SYMBOLS.EOL or ch == SYMBOLS.EOF:
                    return token
                token.value += ch

        if ch == '[':
            token = Token(type = TOKEN_TYPES.SECTION, value = '', offset = self.offset, line = self.line, col = self.col)
            while True:
                ch = self.getchar()
                if ch == ']':
                    return token

                # filtering invalid symbols in section name
                if (not ch.isspace() and not ch.isalpha() and not ch.isdigit()
                    and (ch not in SECTION_NAME_VALID_SYMBOLES)):

                    raise Exception( __name__ + '.lexer:> Invalid section '
                                   + 'identifier. Unexpected char sequence '
                                   + '@[idx: {}] [ln: {}] [col: {}]'
                                   .format(self.offset, self.line, self.col))

                # unexpected symbols at the beginning or at the end of the section id
                if ((token.value == '' or self.lookahead() == ']') and
                    (not ch.isalpha() and not ch.isdigit())):
                    if ch.isspace():
                        logger.warning('Unexpected character: \" \".section id @[idx: {}] [ln: {}] [col: {}]'.format(self.offset, self.line, self.col))
                    else:
                        raise Exception( __name__ + '.lexer:> Invalid section identifier. Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]'.format(self.offset, self.line, self.col))

                if ch == ' ' and self.lookahead().isspace(): # consecutive spaces
                    logger.warning('Unexpected character: \" \".section id @[idx: {}] [ln: {}] [col: {}]'.format(self.offset, self.line, self.col))

                if ch == SYMBOLS.EOF or ch == SYMBOLS.EOL:
                    raise Exception( __name__ + '.lexer:> Invalid section identifier @[idx: {}] [ln: {}] [col: {}]'.format(self.offset, self.line, self.col))
                token.value += ch

        if ch == SYMBOLS.QUOTATION:
            token = Token(type = TOKEN_TYPES.STRING, value = '', offset = self.offset, line = self.line, col = self.col)
            while True:
                ch = self.getchar()
                if ch == SYMBOLS.QUOTATION and self.lookbehind() != SYMBOLS.BACKSLASH:
                    return token
                if ch == SYMBOLS.EOF or ch == SYMBOLS.EOL:
                    raise Exception( __name__ + '.lexer:> Invalid string value @[idx: {}] [ln: {}] [col: {}]'.format(self.offset, self.line, self.col))
                token.value += ch

        if ch in OPERATORS:
            return Token(type = TOKEN_TYPES.OPERATOR, value = ch, offset = self.offset, line = self.line, col = self.col)

        if ch in SEPARATORS:
            return Token(type = TOKEN_TYPES.SEPARATOR, value = ch, offset = self.offset, line = self.line, col = self.col)

        if ch == SYMBOLS.POINT or ch == SYMBOLS.MINUS or ch == SYMBOLS.PLUS  or ch.isdigit():
            token = Token(TOKEN_TYPES.NUMBER, value = ch, offset = self.offset, line = self.line, col = self.col)
            while True:
                if ((self.lookahead() in OPERATORS) or
                    (self.lookahead() in SEPARATORS)):
                    return token
                ch = self.getchar()
                if ch.isspace():
                    return token
                if ch == ':': token.type   = TOKEN_TYPES.TIME
                elif ch == '-': token.type = TOKEN_TYPES.DATE
                elif ch == '_': token.type = TOKEN_TYPES.IDENTIFIER
                token.value += ch

        if ch == SYMBOLS.OPENINGBRACE:
            token = Token(TOKEN_TYPES.DATASET, value = ch, offset = self.offset, line = self.line, col = self.col)
            while True:
                if self.lookahead() == SYMBOLS.SEMICOLON:
                    return token
                ch = self.getchar()
                token.value += ch

                if ch == SYMBOLS.CLOSINGBRACE:
                    return token

        if ch.isalpha():
            token = Token(TOKEN_TYPES.IDENTIFIER, value = ch, offset = self.offset, line = self.line, col = self.col)
            while True:
                ch = self.getchar()
                if ch.isspace():
                    return token
                token.value += ch
                if ((self.lookahead() in OPERATORS) or
                    (self.lookahead() in SEPARATORS)):
                    return token

    def nexttoken(self):
        self.prevtoken = self.token
        self.token = self.gettoken()

        logger.debug('token: {}'.format(self.token))

    def parse(self):
        while True:
            self.nexttoken()

            if self.token is None:
                self.on_EOF()
                return self.eds

            if self.match(TOKEN_TYPES.COMMENT):
                self.addcomment()
                continue

            if self.match(TOKEN_TYPES.SECTION):
                self.addsection()
                continue

            if self.match(TOKEN_TYPES.IDENTIFIER):
                self.addentry()
                continue

            raise Exception(__name__ + ':> ERROR! Invalid token! {}'.format(self.token))

    def addsection(self):
        self.sectioninuse = self.eds.addsection(self.token.value)

        if self.sectioninuse is None:
            raise Exception(__name__ + ':> ERROR! unable to create section: {}'.format(self.token.value))
        self.actualelement = self.sectioninuse
        self.actualelement.hcomment = self.hcomment
        self.hcomment = ''

    def addentry(self):
        self.entryinuse = self.eds.addentry(self.sectioninuse.name, self.token.value)

        if self.entryinuse is None:
            raise Exception(__name__ + ':> ERROR! unable to create entry: {}'.format(self.token.value))
        self.actualelement = self.entryinuse
        self.actualelement.hcomment = self.hcomment
        self.hcomment = ''

        self.nexttoken()
        self.expect(TOKEN_TYPES.OPERATOR, SYMBOLS.ASSIGNMENT)

        while True:
            self.addfield()
            if self.match(TOKEN_TYPES.SEPARATOR, SYMBOLS.COMMA):
                continue
            if self.match(TOKEN_TYPES.SEPARATOR, SYMBOLS.SEMICOLON):
                break

    def addfield(self):
        expectingfieldvalue = True
        fieldvalue = ''
        fieldtype  = None

        # Fetch tokens in a loop, concatenate the values if possible(to support multi-line strings) and finally create a field if a separator is found
        while(True):
            self.nexttoken()

            if self.token is None:
                raise Exception(__name__ + ':> ERROR! Unexpected EOF.')

            if self.match(TOKEN_TYPES.COMMENT):
                self.addcomment()
                continue

            if (self.match(TOKEN_TYPES.IDENTIFIER)  or
                self.match(TOKEN_TYPES.STRING)      or
                self.match(TOKEN_TYPES.NUMBER)      or
                self.match(TOKEN_TYPES.DATE)        or
                self.match(TOKEN_TYPES.TIME)        or
                self.match(TOKEN_TYPES.DATASET)):

                if fieldvalue == '' and fieldtype is None:
                    fieldvalue += self.token.value
                    fieldtype = self.token.type
                elif fieldtype == TOKEN_TYPES.STRING and self.match(TOKEN_TYPES.STRING): # There are two strings literals in one field which should be Concatenated
                    fieldvalue += self.token.value
                else:
                    raise Exception(__name__ + '.lexer:> ERROR! Concatenating these literals is not allowed. ({})<{}> + ({})<{}> @({})'.format(fieldvalue, TOKEN_TYPES.Str(fieldtype), self.token.value, TOKEN_TYPES.Str(self.token.type), self.token))
                continue

            if self.match(TOKEN_TYPES.SEPARATOR, SYMBOLS.COMMA) or self.match(TOKEN_TYPES.SEPARATOR, SYMBOLS.SEMICOLON):
                field = self.eds.addfield(self.sectioninuse.name, self.entryinuse.name, fieldvalue, fieldtype)

                if field is None:
                    raise Exception(__name__ + '.lexer:> ERROR! unable to create field: {} of type: {}'.format(self.token.value, self.token.type))

                self.actualelement = field
                self.actualelement.hcomment = self.hcomment
                self.hcomment = ''

                fieldvalue = ''
                fieldtype  = None
                break

            raise Exception(__name__ + '.lexer:> ERROR! Unexpected token type. {}'.format(self.token))

    def addcomment(self):
        # the footer comment only appears on the same line after the eds data
        # otherwise the comment is a header comment
        if self.prevtoken:
            if self.prevtoken.line == self.token.line:
                self.actualelement.fcomment = self.token.value.strip()
                return
            self.hcomment += self.token.value.strip() + '\n'

    def on_EOF(self):
        self.eds.end_comment = self.hcomment
        self.hcomment = ''

    def expect(self, exptokentype, exptokenval = None):
        if self.token.type == exptokentype and exptokenval is not None:
            if self.token.value == exptokenval:
                return True
        elif self.token.type == exptokentype :
            return True

        raise Exception(__name__ + '.lexer:> ERROR! Unexpected token! Expected: (\"{}\": {}) but received: {}'.format(TOKEN_TYPES.Str(exptokentype), exptokenval, self.token))

    def match(self, exptokentype, exptokenval = None):
        if self.token.type == exptokentype and exptokenval is not None:
            if self.token.value == exptokenval:
                return True
        elif self.token.type == exptokentype :
            return True
        return False

# ------------------------------------------------------------------------------
class eds_pie(object):
    @staticmethod
    def parse(eds_content = '', showprogress = True):

        eds = parser(eds_content, showprogress).parse()

        # setting the protocol
        sect = eds.getsection('Device Classification')
        if sect:
            for entry in sect.entries:
                if entry.getfield().value in entry.getfield().datatype[1]:
                    eds._protocol = entry.getfield().value
                    break
        if eds._protocol == '': eds._protocol = 'Generic'

        #self.final_rollcall()
        if showprogress: print ''
        return eds


