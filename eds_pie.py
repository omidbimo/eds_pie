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
logging.basicConfig(level=logging.WARNING,
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

CIP_BOOL    = EDS_Types.BOOL
CIP_USINT   = EDS_Types.USINT
CIP_UINT    = EDS_Types.UINT
CIP_UDINT   = EDS_Types.UDINT
CIP_ULINT   = EDS_Types.ULINT
CIP_SINT    = EDS_Types.SINT
CIP_INT     = EDS_Types.INT
CIP_DINT    = EDS_Types.DINT
CIP_LINT    = EDS_Types.LINT
CIP_WORD    = EDS_Types.WORD
CIP_DWORD   = EDS_Types.DWORD
CIP_REAL    = EDS_Types.REAL
CIP_LREAL   = EDS_Types.LREAL
CIP_BYTE    = EDS_Types.BYTE
CIP_STRING  = EDS_Types.STRING
CIP_STRINGI = EDS_Types.STRINGI
EDS_DATE    = EDS_Types.DATE
CIP_TIME    = EDS_Types.TIME
CIP_EPATH   = EDS_Types.EPATH

EDS_REVISION   = EDS_Types.REVISION
EDS_KEYWORD    = EDS_Types.KEYWORD
EDS_DATAREF    = EDS_Types.REF
EDS_VENDORSPEC = EDS_Types.VENDOR_SPECIFIC
EDS_TYPEREF    = EDS_Types.DATATYPE_REF # Reference to another field which contains a cip_dtypeid
EDS_MAC_ADDR   = EDS_Types.ETH_MAC_ADDR
EDS_EMPTY      = EDS_Types.EMPTY
EDS_UNDEFINED  = EDS_Types.UNDEFINED
EDS_SERVICE    = EDS_Types.EDS_SERVICE

class PSTATE(EDS_Types.ENUMS):
    EXPECT_SECTION = 0
    EXPECT_ENTRY   = 1
    EXPECT_SECTION_OR_ENTRY = 2
    EXPECT_FIELD   = 3

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

    def add_entry(self, entry_name, serialize = False):
        return self._eds.add_entry(self._name, entry_name)

    def has_entry(self, entry_name = None, entryindex = None):
        if entry_name.replace(' ', '').lower() in self._entries.keys():
            return True
        return False

    def get_entry(self, entry_name):
        return self._entries.get(entry_name)

    def get_field(self, entry_name, field):
        '''
        To get a section.entry.field using the entry name + (ield name or field index.
        '''
        entry = self._entries.get(entry_name)
        if entry:
            return entry.get_field(field)
        return None

    def __str__(self):
        return 'SECTION({})'.format(self._name)

class EDS_Entry(object):

    def __init__(self, section, name, index):
        self._index   = index
        self._section = section
        self._name    = name
        self._fields  = [] # Unlike the _sections and _entries, _fields are implemented as a list.
                           # One reason is entry fields with the same name which doesn't easily fit to a dictionary.
        self.hcomment = ''
        # Entries don't have fcomment attribute. The fcomments belongs to fields

    def add_field(self, field_value, datatype = None):
        return self._section._eds.add_field(self._section.name, self._name, field_value, datatype)

    def has_field(self, field):
        if isinstance(field, str): # field name
            fieldname = field.replace(' ', '').lower()
            for field in self._fields:
                if fieldname == field.name.replace(' ', '').lower():
                    return True
        elif isinstance(field, numbers.Number): # field index
            return field < entry.fieldcount
        else:
            raise TypeError('Inappropriate data type: {}'.format(type(field)))

    def get_field(self, field):
        if isinstance(field, str): # field name
            fieldname = field.replace(' ', '').lower()
            for field in self._fields:
                if fieldname == field:
                    return field
        elif isinstance(field, numbers.Number): # field index
            if field < self.fieldcount:
                return self.fields[field]
        else:
            raise TypeError('Inappropriate data type: {}'.format(type(field)))
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

    @property
    def value(self):
        if len(self._fields) > 1:
            logger.warning('Entry has multiple fields. Only the first field is returned.')
        return self._fields[0].value

    def __str__(self):
        return 'ENTRY({})'.format(self._name)

class EDS_Field(object):
    def __init__(self, entry, name, data, index):
        self._index     = index
        self._entry     = entry
        self._name      = name
        self._data      = data # datatype object. Actually is the Field value containing also its type information
        self._data_types = [] # Valid datatypes a field supports
        # Fields don't have hcomment attribute. The hcomments belongs to entries
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
        if type(self._data) != EMPTY or type(self._data) != EDS_UNDEFINED:
            if type(self._data).validate(value, self._data.range):
                self._data._value = value
                return
        # Setting with the actual datatype is failed. Try other supported types.
        if self._data_types:
            for datatype, valid_data in self._data_types:
                if datatype.validate(value, valid_data):
                    del self._data
                    self._data = datatype(value, valid_data)
                    return
        types_str = ', '.join('<{}>{}'.format(datatype.__name__, valid_data)
                                for datatype, valid_data in self._data_types)
        raise Exception('Unable to set Field value! Data_type mismatch!'
            ' [{}].{}.{} = ({}), should be a type of: {}'
            .format(self._entry._section.name, self._entry.name, self.name, value, types_str))

    @property
    def datatype(self):
        return (type(self._data), self._data.range)

    def __str__(self):
        if self._data is None:
            return '\"\"'
        # TODO: If a field of STRING contains multi lines of string, print each line as a seperate string.
        return 'FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})'.format(
            self._index, self._name, str(self._data), type(self._data).__name__, self._data.range)

class EDS_RefLib(object):
    type_mapping = {
        "BOOL"    : EDS_Types.BOOL,
        "USINT"   : EDS_Types.USINT,
        "UINT"    : EDS_Types.UINT,
        "UDINT"   : EDS_Types.UDINT,
        "ULINT"   : EDS_Types.ULINT,
        "SINT"    : EDS_Types.SINT,
        "INT"     : EDS_Types.INT,
        "DINT"    : EDS_Types.DINT,
        "LINT"    : EDS_Types.LINT,
        "WORD"    : EDS_Types.WORD,
        "DWORD"   : EDS_Types.DWORD,
        "REAL"    : EDS_Types.REAL,
        "LREAL"   : EDS_Types.LREAL,
        "BYTE"    : EDS_Types.BYTE,
        "STRING"  : EDS_Types.STRING,
        "STRINGI" : EDS_Types.STRINGI,
        "DATE"    : EDS_Types.DATE,
        "TIME"    : EDS_Types.TIME,
        "EPATH"   : EDS_Types.EPATH,

        "REVISION"          : EDS_Types.REVISION,
        "KEYWORD"           : EDS_Types.KEYWORD,
        "REF"               : EDS_Types.REF,
        "VENDOR_SPECIFIC"   : EDS_Types.VENDOR_SPECIFIC,
        "DATATYPE_REF"      : EDS_Types.DATATYPE_REF, # Reference to another field which contains a cip_dtypeid
        "MAC_ADDR"          : EDS_Types.ETH_MAC_ADDR,
        "EMPTY"             : EDS_Types.EMPTY,
        "UNDEFINED"         : EDS_Types.UNDEFINED,
        "SERVICE"           : EDS_Types.EDS_SERVICE,
        }

    supported_data_types = {
        0xC1: CIP_BOOL,
        0xC2: CIP_SINT,
        0xC3: CIP_INT,
        0xC4: CIP_DINT,
        0xC5: CIP_LINT,
        0xC6: CIP_USINT,
        0xC7: CIP_UINT,
        0xC8: CIP_UDINT,
        0xC9: CIP_ULINT,
        0xCA: CIP_REAL,
        0xCB: CIP_LREAL,
        0xCC: EDS_Types.STIME,
        0xCD: EDS_DATE,
        #, 0xCE: EDS_Types.TIME_OF_DAY
        #, 0xCF: EDS_Types.DATE_AND_TIME
        0xD0: CIP_STRING,
        0xD1: CIP_BYTE,
        0xD2: CIP_WORD,
        0xD3: CIP_DWORD,
        0xD4: EDS_Types.LWORD,
        #, 0xD5: EDS_Types.STRING2
        #, 0xD6: EDS_Types.FTIME
        #, 0xD7: EDS_Types.LTIME
        #, 0xD8: EDS_Types.ITIME
        #, 0xD9: EDS_Types.STRINGN
        #, 0xDA: EDS_Types.SHORT_STRING
        0xDB: CIP_TIME,
        0xDC: CIP_EPATH,
        #, 0xDD: EDS_Types.ENGUNIT
        0xDE: CIP_STRINGI,
        }

    def __init__(self):
        self.libs = {}

        for file in os.listdir():
            if file.endswith(".json"):
                with open(file, "r") as src:
                    jlib = json.loads(src.read())
                    if jlib["project"] ==  "eds_pie" and file != "edslib_schema.json":
                        self.libs[jlib["protocol"].lower()] = jlib



    def get_lib_name(self, section_keyword):
        for _, lib in self.libs.items():
            if section_keyword in lib["sections"]:
                return lib["protocol"]
        return None

    def get_section_name(self, class_id):
        '''
        To get a protocol specific EDS section_name by its CIP class ID
        '''
        for _, lib in self.libs.items():
            for section in lib["sections"]:
                if section["class_id"] == class_id:
                    return section
        return ''

    def get_section_id(self, section_keyword):
        section = self.get_section(section_keyword)
        if section:
            return section["class_id"]
        return None

    def has_section(self, section_keyword):
        '''
        Checks the existence of a section by its name
        '''
        for _, lib in self.libs.items():
            if section_keyword in lib["sections"]:
                return True
        return False

    def get_section(self, section_keyword, protocol=None):
        section = None
        for _, lib in self.libs.items():
            section = lib["sections"].get(section_keyword, None)
            if section:
                break
            else:
                continue
        return section

    def has_entry(self, section_keyword, entry_name):
        '''
        To get an entry dictionary by its section name and entry name
        '''
        return self.get_entry(section_keyword, entry_name) is not None

    def get_entry(self, section_keyword, entry_name):
        '''
        To get an entry dictionary by its section name and entry name
        '''
        entry = None

        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + 'N'

        section = self.get_section(section_keyword)
        if section:
            # First check if the entry is in common class object
            if section["class_id"] and section["class_id"] != 0:
                common_section = self.get_section("Common Object Class")
                entry = common_section["entries"].get(entry_name, None)
                #print(entry_name, entry)
            if entry is None:
                entry = section["entries"].get(entry_name, None)
        return entry

    def get_field_byindex(self, section_keyword, entry_name, field_index):
        '''
        To get a field dictionary by its section name and entry name and field index
        '''
        field = None
        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + 'N'

        entry = self.get_entry(section_keyword, entry_name)
        if entry:
            '''
            The requested index is greater than listed fields in the lib,
            Consider the field as Nth field filed and re-calculate the index.
            '''
            if field_index >= len(entry["fields"]) and entry.get("enumerated_fields", None):
                # Calculating reference field index
                field_index = (field_index % entry["enumerated_fields"]["enum_member_count"]) + entry["enumerated_fields"]["first_enum_field"] - 1
            try:
                field = entry["fields"][field_index]
            except:
                field = None
        return field

    def get_field_byname(self, section_keyword, entry_name, field_name):
        '''
        To get a field dictionary by its section name and entry name and field name
        '''
        field = None

        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + 'N'

        entry = self.get_entry(section_keyword, entry_name)
        if entry:
            if field_name[-1].isdigit(): # Incremental field_name
                field_name = field_name.rstrip(digits) + 'N'

            for fld in entry["fields"]:
                if fld["name"] == field_name:
                    field = fld
        return field

    def get_type(self, cip_typeid):
        return self.supported_data_types[cip_typeid]

    def get_required_sections(self):

        required_sections = {}

        for _, lib in self.libs.items():
            for section_name, section in lib["sections"].items():
                if section["required"] == True:
                    required_sections.update({section_name: section})

        return required_sections

    def get_type(self, type_name):
        return self.type_mapping.get(type_name, None)

    def validate(self, type_name, type_info, value):
        dt = self.get_type(type_name)
        if dt:
            return dt.validate(value, type_info)
        return False

    def is_required_field(self, section_keyword, entry_name, field_name):
        field = self.get_field_byname(section_keyword, entry_name, field_name)
        if field:
            return field["required"]
        return False

class EDS(object):

    def __init__(self):
        self.heading_comment = ''
        self.end_comment = ''
        self._protocol  = None
        self._sections  = {}
        self.ref_libs = EDS_RefLib()

    def list(self, section_name='', entry_name=''):
        if section_name:
            self.list_section(self.get_section(section_name), entry_name)
        else:
            for section in sorted(self.sections, key = lambda section: section._index):
                self.list_section(section, entry_name)

    def list_section(self, section, entry_name=''):
        if entry_name:
            self.list_entry(section.get_entry(entry_name))
        else:
            for entry in sorted(section.entries, key = lambda entry: entry._index):
                self.list_entry(entry)

    def list_entry(self, entry):
        print ('    {}'.format(entry))
        for field in entry.fields:
            print ('        {}'.format(field))

    @property
    def protocol(self):
        return self._protocol

    @property
    def sections(self):
        return tuple(self._sections.values())

    def get_section(self, section):
        '''
        To get a section object by its EDS keyword or by its CIP classID.
        '''
        if isinstance(section, str):
            return self._sections.get(section)
        if isinstance(section, numbers.Number):
            return self._sections.get(self.ref_libs.get_section_name(section))
        raise TypeError('Inappropriate data type: {}'.format(type(section)))

    def get_entry(self, section, entry_name):
        '''
        To get an entry by its section name/section id and its entry name.
        '''
        sec = self.get_section(section)
        if sec:
            return sec.get_entry(entry_name)
        return None

    def get_field(self, section, entry_name, field):
        '''
        To get an field by its section name/section id, its entry name and its field anme/field index
        '''
        entry = self.get_entry(section, entry_name)
        if entry:
            return entry.get_field(field)
        return None

    def get_value(self, section, entry_name, field):
        field = self.get_field(section, entry_name, field)
        if field:
            return field.value
        return None

    def set_value(self, section, entry_name, field, value):
        field = self.get_field(section, entry_name, field)
        if field is None:
            raise Exception('Not a valid field! Unable to set the field value.')
        field.value = value


    def has_section(self, section):
        '''
        To check if the EDS contains a section by its EDS keyword or by its CIP classID.
        '''
        if isinstance(section, str):
            return section in self._sections.keys()
        if isinstance(section, numbers.Number):
            return self.ref_libs.get_section_name(section, self.protocol) in self._sections.keys()
        raise TypeError('Inappropriate data type: {}'.format(type(section)))

    def has_entry(self, section, entry_name):
        section = self.get_section(section)
        if section:
            return entry_name in section._entries.keys()
        return False

    def has_field(self, section, entry_name, field):
        entry = self.get_entry(section, entry_name)
        if entry:
            return fieldindex < entry.fieldcount
        return False

    def add_section(self, section_name):
        if section_name == '':
            raise Exception("Invalid section name! [{}]".format(section_name))

        if section_name in self._sections.keys():
            raise Exception('Duplicate section! [{}}'.format(section_name))

        if self.ref_libs.has_section(section_name) == False:
            logger.warning('Unknown Section [{}]'.format(section_name))

        section = EDS_Section(self, section_name, self.ref_libs.get_section_id(section_name))
        self._sections.update({section_name: section})

        return section

    def add_entry(self, section_name, entry_name):
        section = self._sections[section_name]

        if entry_name == '':
            raise Exception("Invalid Entry name! [{}]\"{}\"".format(section_name, entry_name))

        if entry_name in section._entries.keys():
            raise Exception("Duplicate Entry! [{}]\"{}\"".format(section_name, entry_name))

        # Search for the same section:entry inside the reference lib
        if self.ref_libs.has_entry(section_name, entry_name) == False:
            logger.warning('Unknown Entry [{}].{}'.format(section_name, entry_name))

        entry = EDS_Entry(section, entry_name, section.entrycount)
        section._entries[entry_name] = entry

        return entry

    def add_field(self, section_name, entry_name, field_value, field_datatype = None):
        '''
        Fields must be added in order and no random access is allowed.
        '''
        section = self.get_section(section_name)

        if section is None:
            raise Exception('Section not found! [{}]'.format(section_name))

        entry = section.get_entry(entry_name)
        if entry is None:
            raise Exception('Entry not found! [{}]'.format(entry_name))

        # Getting field's info from eds reference libraries
        field_data = None
        ref_data_types = []
        ref_field = self.ref_libs.get_field_byindex(section._name, entry.name, entry.fieldcount)

        if ref_field:
            # Reference field is now known. Use the ref information to create the field
            ref_data_types = ref_field.get("data_types", None)
            field_name = ref_field["name"] or entry.name
            # Serialize the field name if the entry can have enumerated fields like AssemN and ParamN.
            if self.ref_libs.get_entry(section_name, entry_name).get("enumerated_fields", None):
                field_name = field_name.rstrip('N') + str(entry.fieldcount + 1)
        else:
            # No reference field was found. Use a general naming scheme
            field_name = 'field{}'.format(entry.fieldcount)

        # Validate field's value and assign a data type to the field
        if field_value == '':
            logger.info("Field [{}].{}.{} has no value. Switched to EDS_EMPTY field.".format(section._name, entry.name, field_name))
            field_data = EDS_EMPTY(field_value)

        elif not ref_data_types:
            # The filed is unknown and no ref_types are in hand. Try some default data types.
            if EDS_VENDORSPEC.validate(field_value):
                logger.info('Unknown Field [{}].{}.{} = {}. Switched to VENDOR_SPECIFIC field.'.format(section._name, entry.name, field_name, field_value))
                field_data = EDS_VENDORSPEC(field_value)
            elif EDS_UNDEFINED.validate(field_value):
                logger.info('Unknown Field [{}].{}.{} = {}. Switched to EDS_UNDEFINED field.'.format(section._name, entry.name, field_name, field_value))
                field_data = EDS_UNDEFINED(field_value)
            else:
                raise Exception('Unknown Field [{}].{}.{} = {} with no matching data types.'.format(section._name, entry.name, field_name, field_value))

        else:
            for type_name, type_info in ref_data_types.items(): # Getting the listed data types and their acceptable ranges
                if self.ref_libs.validate(type_name, type_info, field_value):
                    # creating type instance with field value
                    field_data = self.ref_libs.get_type(type_name)(field_value, type_info)

            if field_data is None: # No proper type was found
                # Providing info on potential acceptable data types
                type_list = []
                for type_name, type_info in ref_data_types.items():
                    if type_info:
                        type_list.append((type_name, type_info))
                    else:
                        try:
                            type_list.append((type_name, self.ref_libs.get_type(type_name)._range))
                        except:
                            continue
                types_str = ', '.join('<{}({})>'.format(self.ref_libs.get_type(type_name).__name__, type_info) for type_name, type_info in type_list)

                if self.ref_libs.get_field_byname(section._name, entry.name, field_name)["required"]:
                    raise Exception('Data_type mismatch! [{}].{}.{} = ({}), should be a type of: {}'
                         .format(section._name, entry.name, field_name, field_value, types_str))
                else:
                    logger.error('Data_type mismatch! [{}].{}.{} = ({}), should be a type of: {}'
                         .format(section._name, entry.name, field_name, field_value, types_str))
                    if EDS_VENDORSPEC.validate(field_value):
                        field_data = EDS_VENDORSPEC(field_value)
                    else:
                        field_data = EDS_UNDEFINED(field_value)

        field = EDS_Field(entry, field_name, field_data, entry.fieldcount)

        field._data_types = ref_data_types
        entry._fields.append(field)

        return field

    def remove_section(self, section_name, removetree = False):
        section = self.get_section(section_name)

        if section is None: return
        if not section.entries:
            del self._sections[section_name]
        elif removetree:
            for entry in section.entries:
                self.remove_entry(section_name, entry.name, removetree)
            del self._sections[section_name]
        else:
            logger.error('Unable to remove section! [{}] contains one or more entries.'
                'Remove the entries first or use removetree = True'.format(section._name))

    def remove_entry(self, section_name, entry_name, removetree = False):
        entry = self.get_entry(section_name, entry_name)
        if entry is None: return
        if not entry.fields:
            section = self.get_section(section_name)
            del section._entries[entry_name]
        elif removetree:
            entry._fields = []
        else:
            logger.error('Unable to remove entry! [{}].{} contains one or more fields.'
                'Remove the fields first or use removetree = True'.format(section._name, entry.name))

    def remove_field(self, section_name, sentryname, fieldindex):
        # TODO
        pass

    def semantic_check(self):
        required_sections = self.ref_libs.get_required_sections()

        for section_name, section in required_sections.items():
            if self.has_section(section_name):
                continue
            raise Exception('Missing required section! [{}]'.format(section_name))
        '''
        #TODO: re-enable this part
        for section in self.sections:
            requiredentries = self.ref.get_required_entries(section.name)
            for entry in requiredentries:
                if self.has_entry(section.name, entry.keyword) == False:
                    logger.error('Missing required entry! [{}].\"{}\"{}'
                        .format(section.name, entry.keyword, entry.name))

            for entry in section.entries:
                requiredfields = self.ref.get_required_fields(section.name, entry.name)
                for field in requiredfields:
                    if self.has_field(section.name, entry.name, field.placement) == False:
                        logger.error('Missing required field! [{}].{}.{} #{}'
                            .format(section.name, entry.name, field.name, field.placement))
        '''
        """
        if type_name == "EDS_TYPEREF":
            '''
            Type of a field is determined by value of another field. A referenced-type has to be validated.
            The name of the ref field that contains the a data_type, is listed in the primary field's
            datatype.valid_ranges(typeinfo) which itself is a list of names
            Example: The datatype of Params.Param1.MinimumValue is determined by Params.Param1.DataType
            '''
            # TODO: here we read only the first item of the reference field list. Iterating the list might be a better way
            typeid = self.get_field(section_name, entry_name, typeinfo[0]).value
            try:
                dtype = self.ref_libs.get_type(typeid)
                if dtype.validate(field_value, []):
                    field_data = dtype(field_value, [])
                    break
            except:
                field_data = EDS_UNDEFINED(field_value)
        """
    def save(self, filename, overwrite = False):
        if os.path.isfile(filename) and overwrite == False:
            raise Exception('Failed to write to file! \"{}\" already exists and overrwite is not enabled.'.format(filename))

        if self.heading_comment == '':
            self.heading_comment = HEADING_COMMENT_TEMPLATE
        eds_content = ''.join('$ {}\n'.format(line.strip()) for line in self.heading_comment.splitlines())

        tabsize = 4
        # sections
        # Creating a list of standard sections.
        std_sections = [self.get_section('File')]
        std_sections.append(self.get_section('Device'))
        std_sections.append(self.get_section('Device Classification'))
        for section in self.sections:
            if section._id is None and section not in std_sections:
                std_sections.append(section)
        # Creating a list of protocol specific sections oredred by their ids.
        protocol_sections = [section for section in self.sections if section._id is not None]
        protocol_sections = sorted(protocol_sections, key = lambda section: section._id)
        sections = std_sections + protocol_sections

        for section in sections:
            if section.hcomment != '':
                eds_content += ''.join('$ {}\n'.format(line.strip()) for line in section.hcomment.splitlines())
            eds_content += '\n[{}]'.format(section.name)

            if section.fcomment != '':
                eds_content += ''.join('$ {}\n'.format(line.strip()) for line in section.fcomment.splitlines())

            eds_content += '\n'

            # Entries
            entries = sorted(section.entries, key = lambda entry: entry._index)
            for entry in entries:

                if entry.hcomment != '':
                    eds_content += ''.join(''.ljust(tabsize, ' ') + '$ {}\n'.format(line.strip()) for line in entry.hcomment.splitlines())
                eds_content += ''.ljust(tabsize, ' ') + '{} ='.format(entry.name)

                # fields
                if entry.fieldcount == 1:
                    if '\n' in str(entry.fields[0]._data):
                        eds_content += '\n'
                        eds_content += '\n'.join(''.ljust(2 * tabsize, ' ') + line
                            for line in str(entry.fields[0]._data).splitlines())
                        eds_content += ';'
                    else:
                        eds_content += '{};'.format(entry.fields[0]._data)
                    if entry.fields[0].fcomment != '':
                        eds_content += ''.join(''.ljust(tabsize, ' ') +
                            '$ {}\n'.format(line.strip()) for line in entry.fields[0].fcomment.splitlines())
                    eds_content += '\n'
                else: # entry has multiple fields
                    eds_content += '\n'

                    for fieldindex, field in enumerate(entry.fields):
                        singleline_field_str = ''.ljust(2 * tabsize, ' ') + '{}'.format(field._data)

                        # separator
                        if (fieldindex + 1) == entry.fieldcount:
                            singleline_field_str += ';'
                        else:
                            singleline_field_str += ','

                        # footer comment
                        if field.fcomment != '':
                            singleline_field_str = singleline_field_str.ljust(30, ' ')
                            singleline_field_str += ''.join('$ {}'.format(line.strip()) for line in field.fcomment.splitlines())
                        eds_content += singleline_field_str + '\n'

        # end comment
        eds_content += '\n'
        if self.end_comment == '':
            self.end_comment = END_COMMENT_TEMPLATE
        eds_content += ''.join('$ {}\n'.format(line.strip()) for line in self.end_comment.splitlines())

        hfile = open(filename, 'w')
        hfile.write(eds_content)
        hfile.close()

    def get_cip_section_name(self, class_id, protocol=None):
        if protocol is None:
            protocol = self.protocol
        return self.ref_libs.get_section_name(class_id, protocol)

    def resolve_epath(self, epath):
        '''
        EPATH data types can contain references to param entries in params section.
        This method validates the path and resolves the referenced items inside the epath.
        input EPATH in string format. example \'20 04 24 [Param1] 30 03\'
        return: EPATH in string format
        '''
        items = epath.split()
        for i in range(len(items)):
            item = items[i]
            if len(item) < 2:
                raise Exception('Invalid EPATH format! item[{}]:\"{}\" in [{}]'.format(index, item, path))

            if not isnumber(item):
                item = item.strip('[]')
                if 'Param' == item.rstrip(digits) or 'ProxyParam' == item.rstrip(digits):
                    entry_name = item
                    field = self.get_field('Params', entry_name, 'Default Value')
                    if field:
                        items[i] = '{:02X}'.format(field.value)
                        continue
                    raise Exception('Entry not found! tem[\'{}\'] in [{}]'.format(item, path))
                raise Exception('Invalid path format! tem[\'{}\'] in [{}]'.format(item, path))
            elif not ishex(item):
                raise Exception('Invalid EPATH format! item[\'{}\'] in [{}]'.format(item, path))

        return ' '.join(item for item in items)

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
    def __init__(self, eds_data, protocol=None):
        self.parser = Parser(eds_data)
        self.parser.parse()

