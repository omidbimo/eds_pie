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
from abc         import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple
from calendar    import monthrange
from string      import digits

import inspect
import cip_types


EXCLUDE_CHARS = [' ', '_', '\\']
STANDARD_EDS_LIB = "Standard".lower()
COMMON_OBJECT_CLASS = "CommonObjectClass".lower()

def trimstring(srcstring, exclude_list):
    string = srcstring
    for ch in exclude_list:
        if ch in string:
            string = string.replace(ch, '')
    return string


class EDS_dict(object):

    def __init__(self):
        self.libs = []
        self.dict = {}
        for lib in eds_libs:
            lib_key = lib.name.lower()
            self.libs.append(lib_key)

            for section in lib.sections:
                section_key = trimstring(section.keyword, EXCLUDE_CHARS).lower()
                self.dict[(lib_key, section_key, '', '')] = section

                for entry in section.entries:
                    entry_key = trimstring(entry.keyword, EXCLUDE_CHARS).lower()
                    self.dict[(lib_key, section_key, entry_key, '')] = entry

                    for field in entry.fields:
                        if field.name == '': field_key = trimstring(entry.name, EXCLUDE_CHARS).lower()
                        else: field_key = trimstring(field.name, EXCLUDE_CHARS).lower()
                        self.dict[(lib_key, section_key, entry_key, field_key)] = field

        self.cipdatatypes = { 0xC1: cip_types.BOOL
                            , 0xC2: cip_types.SINT
                            , 0xC3: cip_types.INT
                            , 0xC4: cip_types.DINT
                            , 0xC5: cip_types.LINT
                            , 0xC6: cip_types.USINT
                            , 0xC7: cip_types.UINT
                            , 0xC8: cip_types.UDINT
                            , 0xC9: cip_types.ULINT
                            , 0xCA: cip_types.REAL
                            , 0xCB: cip_types.LREAL
                            , 0xCC: cip_types.STIME
                            , 0xCD: cip_types.DATE
                            #, 0xCE: cip_types.TIME_OF_DAY
                            #, 0xCF: cip_types.DATE_AND_TIME
                            , 0xD0: cip_types.STRING
                            , 0xD1: cip_types.BYTE
                            , 0xD2: cip_types.WORD
                            , 0xD3: cip_types.DWORD
                            , 0xD4: cip_types.LWORD
                            #, 0xD5: cip_types.STRING2
                            #, 0xD6: cip_types.FTIME
                            #, 0xD7: cip_types.LTIME
                            #, 0xD8: cip_types.ITIME
                            #, 0xD9: cip_types.STRINGN
                            #, 0xDA: cip_types.SHORT_STRING
                            , 0xDB: cip_types.TIME
                            , 0xDC: cip_types.EPATH
                            #, 0xDD: cip_types.ENGUNIT
                            , 0xDE: cip_types.STRINGI
                            }

    def getfieldinfo(self, sectionname, entryname, fieldindex):
        entry = None
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname,   EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                entry = self.dict[(lib_key, section_key, entry_key, '')]
                break

            # Trying the incremental entries
            if entryname[-1].isdigit():
                entry_key = (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    entry = self.dict[(lib_key, section_key, entry_key, '')]
                    break

            # Trying the common object
            if libname != STANDARD_EDS_LIB:
                section_key = COMMON_OBJECT_CLASS
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    entry = self.dict[(lib_key, section_key, entry_key, '')]
                    break

        if entry:
            try:
                """ The requested index is greater than listed fields in the lib,
                     Consider the field as Nth field filed and re-calculate the index. """
                if fieldindex >= len(entry.fields) and entry.Nthfields:
                    fieldindex = (fieldindex % len(entry.Nthfields)) + entry.Nthfields[0] - 1 # To get the array index

                if entry.fields[fieldindex].name == '':
                    """ Single fields have the same name as their entry.
                        In worst case we return the entry name as field name """
                    return (entry.keyword, entry.fields[fieldindex].save_decorator_new_line)
                return (entry.fields[fieldindex].name, entry.fields[fieldindex].save_decorator_new_line)
            except:
                pass
        # No field is found. return a N name
        return ("field{}".format(fieldindex), True)

    def gettypes(self, sectionname, entryname, fieldname):
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname,   EXCLUDE_CHARS).lower()
            field_key   = trimstring(fieldname,   EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, field_key)].datatypes
                if fieldname[-1].isdigit():
                    field_key   = (trimstring(fieldname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                    if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                        return self.dict[(lib_key, section_key, entry_key, field_key)].datatypes

            if entry_key[-1].isdigit():
                entry_key   = (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                        return self.dict[(lib_key, section_key, entry_key, field_key)].datatypes
                    if fieldname[-1].isdigit():
                        field_key   = (trimstring(fieldname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                        if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                            return self.dict[(lib_key, section_key, entry_key, field_key)].datatypes

            if libname != STANDARD_EDS_LIB: # trying the common object
                section_key = COMMON_OBJECT_CLASS
                if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, field_key)].datatypes
        return []

    def getsectioninfo(self, sectionname):
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, '', '') in self.dict.keys():
                return (self.dict[(lib_key, section_key, '', '')].keyword,
                        self.dict[(lib_key, section_key, '', '')].id)
        return ("", 0)

    def getsectionname(self, classid):
        pass
    def getrequired_sections(self):
        for libname in self.libs:
            lib_key = libname.lower()

            if (lib_key, '', '') in self.dict.keys():
                lib = self.dict[(lib_key, '', '')]
                return tuple(section for section in lib.sections if section.mandatory == True)
        return []

    def getrequired_entries(self, sectionname):
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = sectionname.replace(' ', '').lower()

            if (lib_key, section_key, '') in self.dict.keys():
                section = self.dict[(lib_key, section_key, '')]
                return tuple(entry for entry in section.entries if entry.mandatory == True)
        return []

    def getrequired_fields(self, sectionname , entryname):
        for libname in self.libs:
            lib_key     = libname.replace(' ', '').lower()
            section_key = sectionname.replace(' ', '').lower()
            entry_key   = entryname.rstrip(digits).replace(' ', '').lower()

            if (lib_key, section_key, entry_key) in self.dict.keys():
                entry = self.dict[(lib_key, section_key, entry_key)]
                return tuple(field for field in entry.fields if field.mandatory == True)
        return []

    def getsection(self, sectionname):
        for libname in self.libs:
            lib_key = trimstring(libname, EXCLUDE_CHARS).lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, '', '') in self.dict.keys():
                return self.dict[(lib_key, section_key, '', '')]
        return None

    def getentry(self, sectionname , entryname):
        #todo: cleanup, optimimize
        for libname in self.libs:
            lib_key     = lib.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                return self.dict[(lib_key, section_key, entry_key, '')]

            if entryname[-1].isdigit():
                entry_key = (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, '')]

            if libname is not STANDARD_EDS_LIB:
                section_key = COMMON_OBJECT_CLASS
                entry_key = trimstring(entryname, EXCLUDE_CHARS).lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, '')]
        return []

    def hassection(self, sectionname):
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, '', '') in self.dict.keys():
                return True
        return False

    def hasentry(self, sectionname , entryname):
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                return True

            if entryname[-1].isdigit(): # Incremental entry
                entry_key =  (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    return True

            if libname is not STANDARD_EDS_LIB:
                section_key = COMMON_OBJECT_CLASS
                entry_key = trimstring(entryname, EXCLUDE_CHARS).lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    return True
        return False

    def getentryinfo(self, sectionname , entryname):
        entry = None
        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname, EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                entry = self.dict[(lib_key, section_key, entry_key, '')]
                break

            if entryname[-1].isdigit(): # Incremental entry
                entry_key =  (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    entry = self.dict[(lib_key, section_key, entry_key, '')]
                    break

            if libname is not STANDARD_EDS_LIB:
                section_key = COMMON_OBJECT_CLASS
                entry_key = trimstring(entryname, EXCLUDE_CHARS).lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    entry = self.dict[(lib_key, section_key, entry_key, '')]
                    break
        if entry:
            return (entry.keyword, entry.placement)
        return ("", 0)


    def ismandatory(self, sectionname, entryname, fieldname):
        if sectionname == '' or entryname == '' or fieldname == '':
            error = info(ERROR, "Invalid parameter.", extended_info = "sectionname:\"%\", entryname:\"%\" fieldname:\"%s\"" %(sectionname, entryname, fieldname))
            raise Exception(__name__ + ":> Error calling \"%s\" %s" %(str(inspect.stack()[0][3]), error))

        for libname in self.libs:
            lib_key     = libname.lower()
            section_key = trimstring(sectionname, EXCLUDE_CHARS).lower()
            entry_key   = trimstring(entryname,   EXCLUDE_CHARS).lower()
            field_key   = trimstring(fieldname,   EXCLUDE_CHARS).lower()

            if (lib_key, section_key, entry_key, '') in self.dict.keys():
                if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, field_key)].mandatory
                if fieldname[-1].isdigit():
                    field_key   = (trimstring(fieldname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                    if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                        return self.dict[(lib_key, section_key, entry_key, field_key)].mandatory

            if entry_key[-1].isdigit():
                entry_key   = (trimstring(entryname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                if (lib_key, section_key, entry_key, '') in self.dict.keys():
                    if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                        return self.dict[(lib_key, section_key, entry_key, field_key)].mandatory
                    if fieldname[-1].isdigit():
                        field_key   = (trimstring(fieldname.rstrip(digits), EXCLUDE_CHARS) + 'N').lower()
                        if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                            return self.dict[(lib_key, section_key, entry_key, field_key)].mandatory

            if libname != STANDARD_EDS_LIB: # trying the common object
                section_key = COMMON_OBJECT_CLASS
                if (lib_key, section_key, entry_key, field_key) in self.dict.keys():
                    return self.dict[(lib_key, section_key, entry_key, field_key)].mandatory
        return False


    def gettype(self, cip_typeid):
        return self.cipdatatypes[cip_typeid]

CIP_BOOL    = cip_types.BOOL
CIP_USINT   = cip_types.USINT
CIP_UINT    = cip_types.UINT
CIP_UDINT   = cip_types.UDINT
CIP_ULINT   = cip_types.ULINT
CIP_SINT    = cip_types.SINT
CIP_INT     = cip_types.INT
CIP_DINT    = cip_types.DINT
CIP_LINT    = cip_types.LINT
CIP_WORD    = cip_types.WORD
CIP_DWORD   = cip_types.DWORD
CIP_REAL    = cip_types.REAL
CIP_LREAL   = cip_types.LREAL
CIP_BYTE    = cip_types.BYTE
CIP_STRING  = cip_types.STRING
CIP_STRINGI = cip_types.STRINGI
CIP_DATE    = cip_types.DATE
CIP_TIME    = cip_types.TIME
CIP_EPATH   = cip_types.EPATH

EDS_REVISION   = cip_types.REVISION
EDS_KEYWORD    = cip_types.KEYWORD
EDS_DATAREF    = cip_types.REF
EDS_VENDORSPEC = cip_types.VENDOR_SPECIFIC
EDS_TYPEREF    = cip_types.DATATYPE_REF # Reference to another field which contains a cip_dtypeid
EDS_MAC_ADDR   = cip_types.ETH_MAC_ADDR
EDS_EMPTY      = cip_types.EMPTY
EDS_UNDEFINED  = cip_types.UNDEFINED
EDS_SERVICE    = cip_types.EDS_SERVICE

    # Note: the key "public" determines if a class is a public class and may contain entries from common object class.
EDS_LIB     = namedtuple('EDS_LIB'     , 'name sections')
EDS_SECTION = namedtuple('EDS_SECTION' , 'name keyword id mandatory entries')
    # Note: if an entry has recurring fields(Nth fields) first field number of these fields should be listed in the Nthfields of the entry.
    #   example: Section:Assembly entry:Assem the 7th, 9th, 11th... fields can present the members size field. then 7 sould be listed as Nth field
EDS_ENTRY   = namedtuple('EDS_ENTRY'   , 'name keyword mandatory placement Nthfields fields')
DT          = namedtuple('DT'          , 'type typeinfo')
EDS_FIELD   = namedtuple('EDS_FIELD'   , 'name mandatory placement datatypes save_decorator_new_line')

eds_libs = [
    EDS_LIB("Standard", [
        EDS_SECTION( "File Description", "File", 0x10001, True,
            [
              EDS_ENTRY( "File Description Text" , "DescText"  , True , 0, [], [EDS_FIELD("File Description Text" , True, 0, [DT(CIP_STRING, None)], True) ] )
            , EDS_ENTRY( "File Creation Date"    , "CreateDate", True , 0, [], [EDS_FIELD("File Creation Date"    , True, 0, [DT(CIP_DATE,     [])], True) ] )
            , EDS_ENTRY( "File Creation Time"    , "CreateTime", True , 0, [], [EDS_FIELD("File Creation Time"    , True, 0, [DT(CIP_TIME,     [])], True) ] )
            , EDS_ENTRY( "Last Modification Date", "ModDate"   , False, 0, [], [EDS_FIELD("Last Modification Date", True, 0, [DT(CIP_DATE,     [])], True) ] )
            , EDS_ENTRY( "Last Modification Time", "ModTime"   , False, 0, [], [EDS_FIELD("Last Modification Time", True, 0, [DT(CIP_TIME,     [])], True) ] )
            , EDS_ENTRY( "EDS Revision"          , "Revision"  , True , 0, [], [EDS_FIELD("EDS Revision"          , True, 0, [DT(EDS_REVISION, [])], True) ] )
            , EDS_ENTRY( "Home URL"              , "HomeURL"   , False, 0, [], [EDS_FIELD("Home URL"              , True, 0, [DT(CIP_STRING,   [])], True) ] )
            , EDS_ENTRY( "Exclude"               , "Exclude"   , False, 0, [], [EDS_FIELD("Exclude"               , True, 0, [DT(EDS_KEYWORD, ["NONE", "WRITE", "READ_WRITE"])], True) ] )
            , EDS_ENTRY( "EDS File CRC"          , "EDSFileCRC", False, 0, [], [EDS_FIELD("EDS File CRC"          , True, 0, [DT(CIP_UDINT,    [])], True) ] )
            ])

        , EDS_SECTION( "Device Description", "Device", 0x10002, True,
            [
              EDS_ENTRY( "Vendor ID"         , "VendCode"    , True,  0, [], [EDS_FIELD("Vendor ID"         , True, 0, [DT(CIP_UINT,   [])], True) ] )
            , EDS_ENTRY( "Vendor Name"       , "VendName"    , True,  0, [], [EDS_FIELD("Vendor Name"       , True, 0, [DT(CIP_STRING, [])], True) ] )
            , EDS_ENTRY( "Device Type"       , "ProdType"    , True,  0, [], [EDS_FIELD("Device Type"       , True, 0, [DT(CIP_UINT,   [])], True) ] )
            , EDS_ENTRY( "Device Type String", "ProdTypeStr" , True,  0, [], [EDS_FIELD("Device Type String", True, 0, [DT(CIP_STRING, [])], True) ] )
            , EDS_ENTRY( "Product Code"      , "ProdCode"    , True,  0, [], [EDS_FIELD("Product Code"      , True, 0, [DT(CIP_UDINT,  [])], True) ] )
            , EDS_ENTRY( "Major Revision"    , "MajRev"      , True,  0, [], [EDS_FIELD("Major Revision"    , True, 0, [DT(CIP_USINT,  [])], True) ] )
            , EDS_ENTRY( "Minor Revision"    , "MinRev"      , True,  0, [], [EDS_FIELD("Minor Revision"    , True, 0, [DT(CIP_USINT,  [])], True) ] )
            , EDS_ENTRY( "Product Name"      , "ProdName"    , True,  0, [], [EDS_FIELD("Product Name"      , True, 0, [DT(CIP_STRING, [])], True) ] )
            , EDS_ENTRY( "Catalog Number"    , "Catalog"     , False, 0, [], [EDS_FIELD("Catalog Number"    , True, 0, [DT(CIP_STRING, [])], True) ] )
            , EDS_ENTRY( "Icon File Name"    , "Icon"        , True,  0, [], [EDS_FIELD("Icon File Name"    , True, 0, [DT(CIP_STRING, [])], True) ] )
            , EDS_ENTRY( "Icon Contents"     , "IconContents", False, 0, [], [EDS_FIELD("Icon Contents"     , True, 0, [DT(CIP_STRING, [])], True) ] )
            ])

        , EDS_SECTION( "Device Classification", "Device Classification", 0x10003, True,
            [
              EDS_ENTRY( "Classification 1"  , "Class1"   , True    , 0, [1],
                    [EDS_FIELD("Class1", True, 0, [DT(EDS_KEYWORD, ["CompoNet", "ControlNet", "DeviceNet", "EtherNetIP", "ModbusSL", "ModbusTCP", "Safety"])], True) ] ),
              EDS_ENTRY( "Classification N"  , "ClassN"   , False    , 1, [1],
                    [EDS_FIELD("ClassN", True, 0, [DT(EDS_KEYWORD, ["CompoNet", "ControlNet", "DeviceNet", "EtherNetIP", "ModbusSL", "ModbusTCP", "Safety"])], True) ] )
            ])

        , EDS_SECTION( "Parameters", "Params", 0x10004, False,
            [
              EDS_ENTRY( "Parameter", "ParamN", False, 0, [],
                [ EDS_FIELD("Reserved"                       , True,  0, [DT(CIP_USINT,    [])], True )
                , EDS_FIELD("Link Path Size"                 , False, 0, [DT(CIP_USINT,   []), DT(EDS_EMPTY, [])], False )
                , EDS_FIELD("Link Path"                      , False, 0, [DT(CIP_EPATH,   []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"]), DT(EDS_EMPTY, []) ], True )
                , EDS_FIELD("Descriptor"                     , True,  0, [DT(CIP_WORD,     [])], True )
                , EDS_FIELD("Data Type"                      , True,  0, [DT(CIP_USINT,    [])], True )
                , EDS_FIELD("Data Size"                      , True,  0, [DT(CIP_USINT,    []), DT(EDS_EMPTY, [])], True )
                , EDS_FIELD("Parameter Name"                 , True,  0, [DT(CIP_STRING,   [])], True)
                , EDS_FIELD("Units String"                   , True,  0, [DT(CIP_STRING,   [])], True)
                , EDS_FIELD("Help String"                    , True,  0, [DT(CIP_STRING,   [])], True)
                , EDS_FIELD("Minimum Value"                  , False, 0, [DT(EDS_TYPEREF, ["Data Type"]), DT(EDS_EMPTY, [])], False )
                , EDS_FIELD("Maximum Value"                  , False, 0, [DT(EDS_TYPEREF, ["Data Type"]), DT(EDS_EMPTY, [])], False )
                , EDS_FIELD("Default Value"                  , True,  0, [DT(EDS_TYPEREF,  ["Data Type"]), DT(EDS_EMPTY, [])], True )
                , EDS_FIELD("Scaling Multiplier"             , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Scaling Divider"                , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Scaling Base"                   , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Scaling Offset"                 , False, 0, [DT(CIP_DINT,    [])], True )
                , EDS_FIELD("Multiplier Link"                , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Divisor Link"                   , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Base Link"                      , False, 0, [DT(CIP_UINT,    [])], False )
                , EDS_FIELD("Offset Link"                    , False, 0, [DT(CIP_UINT,    [])], True )
                , EDS_FIELD("Decimal Precision"              , False, 0, [DT(CIP_USINT,   [])], True )
                , EDS_FIELD("International Parameter Name"   , False, 0, [DT(CIP_STRINGI, [])], True )
                , EDS_FIELD("International Engineering Units", False, 0, [DT(CIP_STRINGI, [])], True )
                , EDS_FIELD("International Help String"      , False, 0, [DT(CIP_STRINGI, [])], True )
                ])
            , EDS_ENTRY( "Enumeration", "EnumN", False, 0, [3, 4],
                [ EDS_FIELD("First Enum"       , False, 0, [DT(CIP_USINT,  []), DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("First Enum String", False, 0, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Nth Enum"         , False, 0, [DT(CIP_USINT,  []), DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Nth Enum String"  , False, 0, [DT(CIP_STRING, [])], True )
                ])
            ])
        ])
    ]

eds_libs += [
    EDS_LIB("EtherNetIP", [
        EDS_SECTION( "Identity Class", "Identity Class", 0x01, False,
            [
            ])

        , EDS_SECTION( "Message Router Class", "Message Router Class", 0x02, False,
            [
            ])

        , EDS_SECTION( "DeviceNet Class", "DeviceNet Class", 0x03, False,
            [
            ])

        , EDS_SECTION( "Assembly", "Assembly", 0x04, False,
            [
              EDS_ENTRY( "Assem", "AssemN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True,  1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path"            , False, 2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Size"            , False, 3, [DT(CIP_UINT,   [])], True )
                , EDS_FIELD("Descriptor"      , False, 4, [DT(CIP_WORD,   [])], True )
                , EDS_FIELD("Reserved"        , False, 5, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        , False, 6, [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("Member Size"     , False, 7, [DT(CIP_UINT,   [])], False )
                , EDS_FIELD("Member Reference", False, 8, [DT(CIP_UDINT,  []),
                                                           DT(CIP_EPATH,  []),
                                                           DT(EDS_DATAREF, ["AssemN", "ParamN", "ProxyAssemN", "ProxyParamN"]),
                                                           DT(EDS_EMPTY, [])], True)
                ])
            , EDS_ENTRY( "Assem", "ProxyAssemN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True,  1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path"            , False, 2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"]) ], True )
                , EDS_FIELD("Size"            , False, 3, [DT(CIP_UINT,   [])], True )
                , EDS_FIELD("Descriptor"      , False, 4, [DT(CIP_WORD,   [])], True )
                , EDS_FIELD("Reserved"        , False, 5, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        , False, 6, [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("Member Size"     , False, 7, [DT(CIP_UINT,   [])], False )
                , EDS_FIELD("Member Reference", False, 8, [DT(CIP_UDINT,  []),
                                                          DT(CIP_EPATH,  []),
                                                          DT(EDS_DATAREF, ["AssemN", "ParamN"]),
                                                          DT(EDS_EMPTY,      [])], True )
                ])
            , EDS_ENTRY( "Assem", "ProxiedAssemN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True, 1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path"            , False,2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Size"            , False,3, [DT(CIP_UINT,   [])], True)
                , EDS_FIELD("Descriptor"      , False,4, [DT(CIP_WORD,   [])], True)
                , EDS_FIELD("Reserved"        , False,5, [DT(EDS_EMPTY,  [])], False)
                , EDS_FIELD("Reserved"        , False,6, [DT(EDS_EMPTY,  [])], True)
                , EDS_FIELD("Member Size"     , False,7, [DT(CIP_UINT,   [])], False)
                , EDS_FIELD("Member Reference", False,8, [DT(CIP_UDINT,  []),
                                                          DT(CIP_EPATH,  []),
                                                          DT(EDS_DATAREF, ["AssemN", "ParamN"]),
                                                          DT(EDS_EMPTY,      [])], True)
                ])
            , EDS_ENTRY( "Assem", "AssemExaN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True, 1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path"            , False,2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Size"            , False,3, [DT(CIP_UINT,   []), DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Descriptor"      , False,4, [DT(CIP_WORD,   [])], True)
                , EDS_FIELD("Reserved"        , False,5, [DT(EDS_EMPTY,  [])], False)
                , EDS_FIELD("Reserved"        , False,6, [DT(EDS_EMPTY,  [])], True)
                , EDS_FIELD("Member Size"     , False,7, [DT(CIP_UINT,   [])], False)
                , EDS_FIELD("Member Reference", False,8, [DT(CIP_UDINT,  []),
                                                          DT(CIP_EPATH,  []),
                                                          DT(EDS_DATAREF, ["AssemN", "ParamN", "AssemExaN", "VariantN", "BitStringVariantN", "VariantExaN", "ArrayN", "ConstructedParamN"]),
                                                          DT(EDS_EMPTY, [])], True)
                ])
            , EDS_ENTRY( "Assem", "ProxyAssemExaN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True, 1, [DT(CIP_STRING, [])], True)
                , EDS_FIELD("Path"            , False,2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Size"            , False,3, [DT(CIP_UINT,   []), DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Descriptor"      , False,4, [DT(CIP_WORD,   [])], True )
                , EDS_FIELD("Reserved"        , False,5, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        , False,6, [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("Member Size"     , False,7, [DT(CIP_UINT,   [])], False )
                , EDS_FIELD("Member Reference", False,8, [DT(CIP_UDINT,  []),
                                                          DT(CIP_EPATH,  []),
                                                          DT(EDS_DATAREF, ["AssemN", "ParamN", "AssemExaN", "VariantN", "BitStringVariantN", "VariantExaN", "ArrayN", "ConstructedParamN"]),
                                                          DT(EDS_EMPTY, [])], True)
                ])
            , EDS_ENTRY( "Assem", "ProxiedAssemExaN", False, 0, [7, 8],
                [ EDS_FIELD("Name"            , True,  1, [DT(CIP_STRING, [])], True)
                , EDS_FIELD("Path"            , False, 2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True)
                , EDS_FIELD("Size"            , False, 3, [DT(CIP_UINT,   []), DT(EDS_DATAREF, ["ParamN"])], True)
                , EDS_FIELD("Descriptor"      , False, 4, [DT(CIP_WORD,   [])], True)
                , EDS_FIELD("Reserved"        , False, 5, [DT(EDS_EMPTY,  [])], False)
                , EDS_FIELD("Reserved"        , False, 6, [DT(EDS_EMPTY,  [])], True)
                , EDS_FIELD("Member Size"     , False, 7, [DT(CIP_UINT,   [])], False)
                , EDS_FIELD("Member Reference", False, 8, [DT(CIP_UDINT,  []),
                                                           DT(CIP_EPATH,  []),
                                                           DT(EDS_DATAREF, ["AssemN", "ParamN", "AssemExaN", "VariantN", "BitStringVariantN", "VariantExaN", "ArrayN", "ConstructedParamN"]),
                                                           DT(EDS_EMPTY, [])], True)
                ])
            , EDS_ENTRY( "Variant", "VariantN", False, 0, [11, 12],
                [ EDS_FIELD("Name"            ,             False, 1 , [DT(CIP_STRING, [])], True)
                , EDS_FIELD("Help String"     ,             False, 2 , [DT(CIP_STRING, [])], True)
                , EDS_FIELD("Reserved"        ,             False, 3 , [DT(EDS_EMPTY,  [])], False)
                , EDS_FIELD("Reserved"        ,             False, 4 , [DT(EDS_EMPTY,  [])], False)
                , EDS_FIELD("Reserved"        ,             False, 5 , [DT(EDS_EMPTY,  [])], True)
                , EDS_FIELD("switch selector",              True,  6 , [DT(EDS_DATAREF, ["ParamN", "AssemN"])], True)
                , EDS_FIELD("First selection value",        True,  7,  [DT(CIP_UINT, [])], True )
                , EDS_FIELD("First selection entry",        True,  8,  [DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Second Selection value",       True,  9,  [DT(CIP_UINT, [])], True )
                , EDS_FIELD("Second Selection entry",       True,  10, [DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Subsequent Selection values",  False, 11, [DT(CIP_UINT, [])], True )
                , EDS_FIELD("Subsequent Selection entries", False, 12, [DT(EDS_DATAREF, ["ParamN"])], True )
                ])
            , EDS_ENTRY( "Variant", "VariantExaN", False, 0, [11, 12],
                [ EDS_FIELD("Name"            ,             False, 1 , [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Help String"     ,             False, 2 , [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Reserved"        ,             False, 3 , [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        ,             False, 4 , [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        ,             False, 5 , [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("switch selector",              True,  6 , [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN"])], True )
                , EDS_FIELD("First selection value",        True,  7,  [DT(CIP_UINT, [])], True )
                , EDS_FIELD("First selection entry",        True,  8,  [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True )
                , EDS_FIELD("Second Selection value",       True,  9,  [DT(CIP_UINT, [])], True )
                , EDS_FIELD("Second Selection entry",       True,  10, [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True )
                , EDS_FIELD("Subsequent Selection values",  False, 11, [DT(CIP_UINT, [])], True )
                , EDS_FIELD("Subsequent Selection entries", False, 12, [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True )
                ])
            , EDS_ENTRY( "Variant", "BitStringVariantN", False, 0, [10, 11, 12],
                [ EDS_FIELD("Name"            ,                     False, 1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Help String"     ,                     False, 2, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Reserved"        ,                     False, 3, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        ,                     False, 4, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved"        ,                     False, 5, [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("Bit switch selector",                  True,  6, [DT(EDS_DATAREF, ["AssemN", "ParamN","AssemExaN"])], True )
                , EDS_FIELD("First bit selection value",            True,  7, [DT(CIP_UINT, [])], True )
                , EDS_FIELD("First bit set selection entry",        True,  8, [DT(EDS_DATAREF, ["AssemN", "ParamN","AssemExaN","ArrayN", "ConstructedParamN"]),
                                                                               DT(EDS_EMPTY,      [])], True )
                , EDS_FIELD("First bit reset selection entry",      True,  9, [DT(EDS_DATAREF, ["AssemN", "ParamN","AssemExaN","ArrayN", "ConstructedParamN"]),
                                                                               DT(EDS_EMPTY,      [])], True )
                , EDS_FIELD("Subsequent bit selection value",       False, 10, [DT(CIP_UINT, [])], True )
                , EDS_FIELD("Subsequent bit set selection entry",   False, 11, [DT(EDS_DATAREF, ["AssemN", "ParamN","AssemExaN","ArrayN", "ConstructedParamN"]),
                                                                                DT(EDS_EMPTY,      [])], True )
                , EDS_FIELD("Subsequent bit reset selection entry", False, 12, [DT(EDS_DATAREF, ["AssemN", "ParamN","AssemExaN","ArrayN", "ConstructedParamN"]),
                                                                                DT(EDS_EMPTY,      [])], True )
                ])
            , EDS_ENTRY( "Array", "ArrayN", False, 0, [11],
                [ EDS_FIELD("Name",                         True,  1, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path",                         False, 2, [DT(CIP_EPATH,  []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Descriptor",                   False, 3, [DT(CIP_WORD,   [])], True )
                , EDS_FIELD("Help String",                  False, 4, [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Reserved",                     False, 5, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved",                     False, 6, [DT(EDS_EMPTY,  [])], False )
                , EDS_FIELD("Reserved",                     False, 7, [DT(EDS_EMPTY,  [])], True )
                , EDS_FIELD("Array Element Size",           False, 8, [DT(CIP_UINT,   [])], True )
                , EDS_FIELD("Array Element Type",           True,  9, [DT(EDS_DATAREF, ["AssemN", "AssemExaN", "ParamN", "VariantN", "BitStringVariantN", "VariantExaN", "ConstructedParamN"]),
                                                                       DT(EDS_EMPTY, [])], True  )
                , EDS_FIELD("Number of Dimensions",         True, 10, [DT(CIP_USINT, [])], True )
                , EDS_FIELD("Number of Dimension Elements", True, 11, [DT(CIP_UDINT, [])], True )
                ])
            ])

        , EDS_SECTION( "Connection Class", "Connection Class", 0x05, False,

            [
            ])

        , EDS_SECTION( "Connection Manager", "Connection Manager", 0x06, True,

            [
              EDS_ENTRY( "Connection", "ConnectionN", False, 0, [],
                [ EDS_FIELD("Trigger and transport"     , False, 1 ,  [DT(CIP_DWORD, [])], True )
                , EDS_FIELD("Connection parameters"     , False, 2 ,  [DT(CIP_DWORD, [])], True )
                , EDS_FIELD("O2T RPI"                   , False, 3 ,  [DT(CIP_UDINT, []), DT(EDS_DATAREF, ["ParamN"])], False )
                , EDS_FIELD("O2T size"                  , False, 4 ,  [DT(CIP_UINT,  []), DT(EDS_DATAREF, ["ParamN"])], False )
                , EDS_FIELD("O2T format"                , False, 5 ,  [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True )
                , EDS_FIELD("T2O RPI"                   , False, 6 ,  [DT(EDS_DATAREF, ["ParamN"])], False )
                , EDS_FIELD("T2O size"                  , False, 7 ,  [DT(CIP_UINT,  []), DT(EDS_DATAREF, ["ParamN"])], False )
                , EDS_FIELD("T2O format"                , False, 8 ,  [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True)
                , EDS_FIELD("Proxy Config size"         , False, 9 ,  [DT(CIP_UINT,  []), DT(EDS_DATAREF, ["ParamN"])], False )
                , EDS_FIELD("Proxy Config format"       , False, 10,  [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "AssemExaN", "ArrayN", "ConstructedParamN"])], False )
                , EDS_FIELD("Target Config size"        , False, 11,  [DT(CIP_UINT,  []), DT(EDS_DATAREF, ["ParamN"])], True )
                , EDS_FIELD("Target Config format"      , False, 12,  [DT(EDS_DATAREF, ["ParamN", "AssemN", "AssemExaN", "AssemExaN", "ArrayN", "ConstructedParamN"])], True )
                , EDS_FIELD("Connection name string"    , False, 13 , [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Help string"               , False, 14 , [DT(CIP_STRING, [])], True )
                , EDS_FIELD("Path"                      , False, 15 , [DT(CIP_EPATH, []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True )
                , EDS_FIELD("Safety ASYNC"              , False, 16 , [DT(EDS_EMPTY, [])], True ) #TODO
                , EDS_FIELD("Safety Max Consumer Number", False, 17 , [DT(EDS_EMPTY, [])], True ) #TODO
                ])
            , EDS_ENTRY( "Production Inhibit Time in Milliseconds Network Segment" , "PITNS",      False, 0, [], [EDS_FIELD("PITNS", True, 1, [DT(EDS_KEYWORD, ["Yes", "No"])], True)])
            , EDS_ENTRY( "Production Inhibit Time in Microseconds Network Segment" , "PITNS_usec", False, 0, [], [EDS_FIELD("PITNS_usec", True, 1, [DT(EDS_KEYWORD, ["Yes", "No"])], True)])
            ])

        , EDS_SECTION( "Register Class", "Register Class", 0x07, False,
            [
            ])

        , EDS_SECTION( "Discrete Input Class", "Discrete Input Class", 0x08, False,
            [
            ])

        , EDS_SECTION( "Discrete Output Class", "Discrete Output Class", 0x09, False,
            [
            ])

        , EDS_SECTION( "Analog Input Class", "Analog Input Class", 0x0A, False,
            [
            ])

        , EDS_SECTION( "Analog Output Class", "Analog Output Class", 0x0B, False,
            [
            ])

        , EDS_SECTION( "Analog Output Class", "Analog Output Class", 0x0B, False,
            [
            ])

        , EDS_SECTION( "Presence Sensing Class", "Presence Sensing Class", 0x0E, False,
            [
            ])

        , EDS_SECTION( "Parameter Class", "ParamClass", 0x0F, False,
            [
            ])
#---------------------------------------------------------------------------
        , EDS_SECTION( "Parameter Group", "Groups", 0x10, False,
            [
              EDS_ENTRY( "Group", "GroupN", False, 0, [3],
            #--------
            # Fields
            #--------
            [ EDS_FIELD("Group Name String"                    , True, 1, [DT(CIP_STRING, [])], True)
            , EDS_FIELD("Number of Members"                    , True, 2, [DT(CIP_UINT,   [])], True)
            , EDS_FIELD("Parameter, Proxy Parameter or Variant", True, 3, [DT(CIP_UINT,   [])], True)
            ])
            ])

        , EDS_SECTION( "File Class", "File Class", 0x37, False,
            [
            ])

        , EDS_SECTION( "Port", "Port", 0x01, False,
            [
            ])

        , EDS_SECTION( "Capacity", "Capacity", 0x01, True,
            [
              EDS_ENTRY( "Traffic Spec", "TSpecN", False, 0, [],
                [ EDS_FIELD("TxRx"            , True, 0, [DT(EDS_KEYWORD, ["Tx", "Rx", "TxRx"])], True )
                , EDS_FIELD("ConnSize"        , True, 1, [DT(CIP_UINT,  [])], True)
                , EDS_FIELD("PacketsPerSecond", True, 2, [DT(CIP_UDINT, [])], True)
                ])
            , EDS_ENTRY( "Connection overhead"                       , "ConnOverhead"        , False, 0, [], [EDS_FIELD("Connection overhead"        , True, 0, [DT(CIP_REAL, [])], True) ] )
            , EDS_ENTRY( "Maximum CIP connections"                   , "MaxCIPConnections"   , False, 0, [], [EDS_FIELD("Maximum CIP connections"   , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O connections"                   , "MaxIOConnections"    , False, 0, [], [EDS_FIELD("Maximum I/O connections"    , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum explicit connections"              , "MaxMsgConnections"   , False, 0, [], [EDS_FIELD("Maximum explicit connections"   , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O producers"                     , "MaxIOProducers"      , False, 0, [], [EDS_FIELD("Maximum I/O producers"      , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O consumers"                     , "MaxIOConsumers"      , False, 0, [], [EDS_FIELD("Maximum I/O consumers"      , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O producers plus consumers"      , "MaxIOProduceConsume" , False, 0, [], [EDS_FIELD("Maximum I/O producers plus consumers" , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O multicast producers"           , "MaxIOMcastProducers" , False, 0, [], [EDS_FIELD("Maximum I/O multicast producers" , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum I/O multicast consumers"           , "MaxIOMcastConsumers" , False, 0, [], [EDS_FIELD("Maximum I/O multicast consumers" , True, 0, [DT(CIP_UINT, [])], True) ] )
            , EDS_ENTRY( "Maximum consumers per multicast connection", "MaxConsumersPerMcast", False, 0, [], [EDS_FIELD("Maximum consumers per multicast connection", True, 0, [DT(CIP_UINT, [])], True) ] )
            ])

        , EDS_SECTION( "Device Level Ring Class", "DLR Class", 0x47, False,

            [

            ])

        , EDS_SECTION( "TCP/IP Interface Class", "TCP/IP Interface Class", 0xF5, False,

            [
              EDS_ENTRY( "EtherNet/IP QuickConnect Target" , "ENetQCTN", False, 0, [0], [EDS_FIELD("Ready for Connection Time", True, 0, [DT(CIP_UINT,  [])], True) ] )
            , EDS_ENTRY( "EtherNet/IP QuickConnect Originator" , "ENetQCON", False, 0, [0], [EDS_FIELD("Connection Origination Time", True, 0, [DT(CIP_UINT, [])], True) ] )
            ])

        , EDS_SECTION( "Ethernet Link Class", "Ethernet Link Class", 0xF6, False,
            [
              EDS_ENTRY( "Interface Speed" , "InterfaceSpeedN", False, 0, [], [EDS_FIELD("Interface Speed", True, 0, [DT(CIP_UDINT,  [])], True) ] )
            , EDS_ENTRY( "Interface Label" , "InterfaceLabelN", False, 9, [], [EDS_FIELD("Interface Label", True, 0, [DT(CIP_STRING, [])], True) ] )
            ])

        , EDS_SECTION( "Quality of Service Class", "QoS Class", 0x48, False,
            [
            ])

        , EDS_SECTION( "Connection Configuration Class", "Connection Configuration", 0xF3, False,
            [
            ])

        , EDS_SECTION( "CIP Security Class", "CIP Security Class", 0x5D, False,
            [
            ])

        , EDS_SECTION( "EtherNet/IP Security Class", "EtherNet/IP Security Class", 0x5E, False,
            [
            ])

        , EDS_SECTION( "Certificate Management Class", "Certificate Management Class", 0x5F, False,
            [
            ])

        , EDS_SECTION( "Common Object Class", "CommonObjectClass", 0, False,
            [
              EDS_ENTRY( "Revision",                            "Revision",                        False, 0, [], [EDS_FIELD("Revision",                            True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Maximum Instance Number",             "MaxInst",                         False, 0, [], [EDS_FIELD("MaxInst",                             True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Number of Static Instances",          "Number_Of_Static_Instances",      False, 0, [], [EDS_FIELD("Maximum Instance Number",             True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Maximum Number of Dynamic Instances", "Max_Number_Of_Dynamic_Instances", False, 0, [], [EDS_FIELD("Maximum Number of Dynamic Instances", True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Class attribute identification",      "Class_Attributes",                False, 0, [1], [EDS_FIELD("Attribute ID",                       True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Instance attribute identification",   "Instance_Attributes",             False, 0, [1], [EDS_FIELD("Attribute ID",                       True, 0, [DT(CIP_UINT,   [])], True) ])
            , EDS_ENTRY( "Class service support",               "Class_Services",                  False, 0, [1], [EDS_FIELD("Service",                            True, 0, [DT(EDS_SERVICE, [])], True) ])
            , EDS_ENTRY( "Instance service support",            "Instance_Services",               False, 0, [1], [EDS_FIELD("Service",                            True, 0, [DT(EDS_SERVICE, [])], True) ])
            , EDS_ENTRY( "Object Name",                         "Object_Name",                     False, 0, [], [EDS_FIELD("Name",                                True, 0, [DT(CIP_STRING, [])], True) ])
            , EDS_ENTRY( "Object Class Code",                   "Object_Class_Code",               False, 0, [], [EDS_FIELD("Object Class Code",                   True, 0, [DT(CIP_UDINT,  [])], True) ])
            , EDS_ENTRY( "Service Description",                 "Service_DescriptionN",            False, 0, [1],
                [ EDS_FIELD("Service Code",             True, 0, [DT(CIP_USINT, [])], True)
                , EDS_FIELD("Name",                     True, 1, [DT(CIP_STRING, [])], True)
                , EDS_FIELD("Service Application Path", True, 2, [DT(CIP_EPATH, []), DT(EDS_KEYWORD, ["SYMBOL_ANSI"])], True)
                , EDS_FIELD("Service Request Data",     True, 3, [DT(EDS_DATAREF, ["AssemExaN", "ParamN", "ConstructedParamN"]), DT(EDS_EMPTY, [])], True)
                , EDS_FIELD("Service Response Data",    True, 4, [DT(EDS_DATAREF, ["AssemExaN", "ParamN", "ConstructedParamN"]), DT(EDS_EMPTY, [])], True)
                ])
            ])
        ])
    ]

