import os
import sys
import json

from cip_eds_types import *

CIP_BOOL    = BOOL
CIP_USINT   = USINT
CIP_UINT    = UINT
CIP_UDINT   = UDINT
CIP_ULINT   = ULINT
CIP_SINT    = SINT
CIP_INT     = INT
CIP_DINT    = DINT
CIP_LINT    = LINT
CIP_WORD    = WORD
CIP_DWORD   = DWORD
CIP_REAL    = REAL
CIP_LREAL   = LREAL
CIP_BYTE    = BYTE
CIP_STRING  = STRING
CIP_STRINGI = STRINGI
EDS_DATE    = DATE
CIP_TIME    = TIME
CIP_EPATH   = EPATH

EDS_REVISION   = REVISION
EDS_KEYWORD    = KEYWORD
EDS_DATAREF    = REF
EDS_VENDORSPEC = VENDOR_SPECIFIC
EDS_TYPEREF    = DATATYPE_REF # Reference to another field which contains a cip_dtypeid
EDS_MAC_ADDR   = ETH_MAC_ADDR
EDS_EMPTY      = EMPTY
EDS_UNDEFINED  = UNDEFINED
EDS_SERVICE    = EDS_SERVICE

class EDS_RefLib():
    type_mapping = {
        "BOOL"    : BOOL,
        "USINT"   : USINT,
        "UINT"    : UINT,
        "UDINT"   : UDINT,
        "ULINT"   : ULINT,
        "SINT"    : SINT,
        "INT"     : INT,
        "DINT"    : DINT,
        "LINT"    : LINT,
        "WORD"    : WORD,
        "DWORD"   : DWORD,
        "REAL"    : REAL,
        "LREAL"   : LREAL,
        "BYTE"    : BYTE,
        "STRING"  : STRING,
        "STRINGI" : STRINGI,
        "DATE"    : DATE,
        "TIME"    : TIME,
        "EPATH"   : EPATH,

        "REVISION"          : REVISION,
        "KEYWORD"           : KEYWORD,
        "REF"               : REF,
        "VENDOR_SPECIFIC"   : VENDOR_SPECIFIC,
        "DATATYPE_REF"      : DATATYPE_REF, # Reference to another field which contains a cip_dtypeid
        "MAC_ADDR"          : ETH_MAC_ADDR,
        "EMPTY"             : EMPTY,
        "UNDEFINED"         : UNDEFINED,
        "SERVICE"           : EDS_SERVICE,
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
        0xCC: STIME,
        0xCD: EDS_DATE,
        #, 0xCE: TIME_OF_DAY
        #, 0xCF: DATE_AND_TIME
        0xD0: CIP_STRING,
        0xD1: CIP_BYTE,
        0xD2: CIP_WORD,
        0xD3: CIP_DWORD,
        0xD4: LWORD,
        #, 0xD5: STRING2
        #, 0xD6: FTIME
        #, 0xD7: LTIME
        #, 0xD8: ITIME
        #, 0xD9: STRINGN
        #, 0xDA: SHORT_STRING
        0xDB: CIP_TIME,
        0xDC: CIP_EPATH,
        #, 0xDD: ENGUNIT
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
        """
        To get a protocol specific EDS section_name by its CIP class ID
        """
        for _, lib in self.libs.items():
            for section in lib["sections"]:
                if section["class_id"] == class_id:
                    return section
        return ""

    def get_section_id(self, section_keyword):
        section = self.get_section(section_keyword)
        if section:
            return section["class_id"]
        return None

    def has_section(self, section_keyword):
        """
        Checks the existence of a section by its name
        """
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
        """
        To get an entry dictionary by its section name and entry name
        """
        return self.get_entry(section_keyword, entry_name) is not None

    def get_entry(self, section_keyword, entry_name):
        """
        To get an entry dictionary by its section name and entry name
        """
        entry = None

        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + "N"

        section = self.get_section(section_keyword)
        if section:
            # First check if the entry is in common class object
            if section["class_id"] and section["class_id"] != 0:
                common_section = self.get_section("Common Object Class")
                entry = common_section["entries"].get(entry_name, None)

            if entry is None:
                entry = section["entries"].get(entry_name, None)
        return entry

    def get_field_byindex(self, section_keyword, entry_name, field_index):
        """
        To get a field dictionary by its section name and entry name and field index
        """
        field = None
        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + "N"

        entry = self.get_entry(section_keyword, entry_name)
        if entry:
            """
            The requested index is greater than listed fields in the lib,
            Consider the field as Nth field filed and re-calculate the index.
            """
            if field_index >= len(entry["fields"]) and entry.get("enumerated_fields", None):
                # Calculating reference field index
                field_index = (field_index % entry["enumerated_fields"]["enum_member_count"]) + entry["enumerated_fields"]["first_enum_field"] - 1
            try:
                field = entry["fields"][field_index]
            except:
                field = None
        return field

    def get_field_byname(self, section_keyword, entry_name, field_name):
        """
        To get a field dictionary by its section name and entry name and field name
        """
        field = None

        if entry_name[-1].isdigit(): # Incremental entry_name
            entry_name = entry_name.rstrip(digits) + "N"

        entry = self.get_entry(section_keyword, entry_name)
        if entry:
            if field_name[-1].isdigit(): # Incremental field_name
                field_name = field_name.rstrip(digits) + "N"

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

class EDS:

    def __init__(self):
        self.protocol  = None
        self.sections  = {}
        self.ref_libs = EDS_RefLib()
        self.hcomment = "" # Heading comment
        self.fcomment = "" # End comment

    def list(self, indent=0):
        for key, section in self.sections.items():
            section.list(indent)

    def get_section(self, section_name=None, class_id=0):
        """
        To get a section object by its EDS keyword or by its CIP classID.
        """
        if section_name:
            return self.sections.get(section_name)

        return self.sections.get(self.ref_libs.get_section_name(class_id))


    def get_entry(self, section_name, entry_name):
        """
        To get an entry by its section name and its entry name.
        """
        section = self.get_section(section_name)
        if section:
            return section.get_entry(entry_name)
        return None

    def get_field(self, section_name, entry_name, field_index):
        """
        To get an field by its section name/section id, its entry name and its field anme/field index
        """
        entry = self.get_entry(section, entry_name)
        if entry:
            return entry.get_field(field_index)
        return None

    def get_value(self, section, entry_name, field):
        field = self.get_field(section, entry_name, field)
        if field:
            return field.value
        return None

    def set_value(self, section, entry_name, field, value):
        field = self.get_field(section, entry_name, field)
        if field is None:
            raise Exception("Not a valid field! Unable to set the field value.")
        field.value = value


    def has_section(self, section):
        """
        To check if the EDS contains a section by its EDS keyword or by its CIP classID.
        """
        if isinstance(section, str):
            return section in self.sections.keys()
        if isinstance(section, numbers.Number):
            return self.ref_libs.get_section_name(section, self.protocol) in self.sections.keys()
        raise TypeError("Inappropriate data type: {}".format(type(section)))

    def has_entry(self, section, entry_name):
        section = self.get_section(section)
        if section:
            return entry_name in section.entries.keys()
        return False

    def has_field(self, section, entry_name, field):
        entry = self.get_entry(section, entry_name)
        if entry:
            return fieldindex < len(entry.fields)
        return False

    def add_section(self, section_name):
        if section_name == "":
            raise Exception("Invalid section name! [{}]".format(section_name))

        if section_name in self.sections.keys():
            raise Exception("Duplicate section! [{}}".format(section_name))

        if self.ref_libs.has_section(section_name) == False:
            logger.warning("Unknown Section [{}]".format(section_name))

        section = Section(self, section_name, self.ref_libs.get_section_id(section_name))
        self.sections.update({section_name: section})

        return section

    def add_entry(self, section_name, entry_name):
        section = self.sections[section_name]

        if entry_name == "":
            raise Exception("Invalid Entry name! [{}]\"{}\"".format(section_name, entry_name))

        if entry_name in section.entries.keys():
            raise Exception("Duplicate Entry! [{}]\"{}\"".format(section_name, entry_name))

        # Search for the same section:entry inside the reference lib
        if self.ref_libs.has_entry(section_name, entry_name) == False:
            logger.warning("Unknown Entry [{}].{}".format(section_name, entry_name))

        entry = Entry(section, entry_name, len(section.entries))
        section.entries[entry_name] = entry

        return entry

    def add_field(self, section_name, entry_name, field_value, field_datatype=None):
        """
        Fields must be added in order and no random access is allowed.
        """
        section = self.get_section(section_name)

        if section is None:
            raise Exception("Section not found! [{}]".format(section_name))

        entry = section.get_entry(entry_name)
        if entry is None:
            raise Exception("Entry not found! [{}]".format(entry_name))

        # Getting field"s info from eds reference libraries
        field_data = None
        ref_data_types = []
        ref_field = self.ref_libs.get_field_byindex(section.name, entry.name, len(entry.fields))

        if ref_field:
            # Reference field is now known. Use the ref information to create the field
            ref_data_types = ref_field.get("data_types", None)
            field_name = ref_field["name"] or entry.name
            # Serialize the field name if the entry can have enumerated fields like AssemN and ParamN.
            if self.ref_libs.get_entry(section_name, entry_name).get("enumerated_fields", None):
                field_name = field_name.rstrip("N") + str(len(entry.fields) + 1)
        else:
            # No reference field was found. Use a general naming scheme
            field_name = "field{}".format(len(entry.fields))

        # Validate field"s value and assign a data type to the field
        if field_value == "":
            logger.info("Field [{}].{}.{} has no value. Switched to EDS_EMPTY field.".format(section.name, entry.name, field_name))
            field_data = EDS_EMPTY(field_value)

        elif not ref_data_types:
            # The filed is unknown and no ref_types are in hand. Try some default data types.
            if EDS_VENDORSPEC.validate(field_value):
                logger.warning("Unknown Field [{}].{}.{} = {}. Switched to VENDOR_SPECIFIC field.".format(section.name, entry.name, field_name, field_value))
                field_data = EDS_VENDORSPEC(field_value)
            elif EDS_UNDEFINED.validate(field_value):
                logger.warning("Unknown Field [{}].{}.{} = {}. Switched to EDS_UNDEFINED field.".format(section.name, entry.name, field_name, field_value))
                field_data = EDS_UNDEFINED(field_value)
            else:
                raise Exception("Unknown Field [{}].{}.{} = {} with no matching data types.".format(section.name, entry.name, field_name, field_value))

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
                types_str = ", ".join("<{}({})>".format(self.ref_libs.get_type(type_name).__name__, type_info) for type_name, type_info in type_list)

                if self.ref_libs.get_field_byname(section.name, entry.name, field_name)["required"]:
                    raise Exception("Data type mismatch! [{}].{}.{} = ({}), should be a type of: {}"
                         .format(section.name, entry.name, field_name, field_value, types_str))
                elif field_value != "":
                    logger.error("Data_type mismatch! [{}].{}.{} = ({}), should be a type of: {}"
                         .format(section.name, entry.name, field_name, field_value, types_str))
                    if EDS_VENDORSPEC.validate(field_value):
                        field_data = EDS_VENDORSPEC(field_value)
                    else:
                        field_data = EDS_UNDEFINED(field_value)

        field = Field(entry, field_name, field_data, len(entry.fields))

        field._data_types = ref_data_types
        entry.fields.append(field)

        return field

    def remove_section(self, section_name, removetree = False):
        section = self.get_section(section_name)

        if section is None: return
        if not section.entries:
            del self.sections[section_name]
        elif removetree:
            for entry in section.entries:
                self.remove_entry(section_name, entry.name, removetree)
            del self.sections[section_name]
        else:
            logger.error("Unable to remove section! [{}] contains one or more entries."
                "Remove the entries first or use removetree = True".format(section.name))

    def remove_entry(self, section_name, entry_name, removetree = False):
        entry = self.get_entry(section_name, entry_name)
        if entry is None: return
        if not entry.fields:
            section = self.get_section(section_name)
            del section.entries[entry_name]
        elif removetree:
            entry.fields = []
        else:
            logger.error("Unable to remove entry! [{}].{} contains one or more fields."
                "Remove the fields first or use removetree = True".format(section.name, entry.name))

    def remove_field(self, section_name, sentryname, fieldindex):
        # TODO
        pass

    def semantic_check(self):
        required_sections = self.ref_libs.get_required_sections()

        for section_name, section in required_sections.items():
            if self.has_section(section_name):
                continue
            raise Exception("Missing required section! [{}]".format(section_name))
        """
        #TODO: re-enable this part
        for section in self.sections:
            requiredentries = self.ref.get_required_entries(section.name)
            for entry in requiredentries:
                if self.has_entry(section.name, entry.keyword) == False:
                    logger.error("Missing required entry! [{}].\"{}\"{}"
                        .format(section.name, entry.keyword, entry.name))

            for entry in section.entries:
                requiredfields = self.ref.get_required_fields(section.name, entry.name)
                for field in requiredfields:
                    if self.has_field(section.name, entry.name, field.placement) == False:
                        logger.error("Missing required field! [{}].{}.{} #{}"
                            .format(section.name, entry.name, field.name, field.placement))
        """
        """
        if type_name == "EDS_TYPEREF":

            Type of a field is determined by value of another field. A referenced-type has to be validated.
            The name of the ref field that contains the a data_type, is listed in the primary field"s
            datatype.valid_ranges(typeinfo) which itself is a list of names
            Example: The datatype of Params.Param1.MinimumValue is determined by Params.Param1.DataType

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
            raise Exception("Failed to write to file! \"{}\" already exists and overrwite is not enabled.".format(filename))

        eds_content = self.__str__()

        hfile = open(filename, "w")
        hfile.write(eds_content)
        hfile.close()

    def get_cip_section_name(self, class_id, protocol=None):
        if protocol is None:
            protocol = self.protocol
        return self.ref_libs.get_section_name(class_id, protocol)

    def resolve_epath(self, epath):
        """
        EPATH data types can contain references to param entries in params section.
        This method validates the path and resolves the referenced items inside the epath.
        input EPATH in string format. example \"20 04 24 [Param1] 30 03\"
        return: EPATH in string format
        """
        items = epath.split()
        for i in range(len(items)):
            item = items[i]
            if len(item) < 2:
                raise Exception("Invalid EPATH format! item[{}]:\"{}\" in [{}]".format(index, item, path))

            if not isnumber(item):
                item = item.strip("[]")
                if "Param" == item.rstrip(digits) or "ProxyParam" == item.rstrip(digits):
                    entry_name = item
                    field = self.get_field("Params", entry_name, "Default Value")
                    if field:
                        items[i] = "{:02X}".format(field.value)
                        continue
                    raise Exception("Entry not found! tem[\"{}\"] in [{}]".format(item, path))
                raise Exception("Invalid path format! tem[\"{}\"] in [{}]".format(item, path))
            elif not ishex(item):
                raise Exception("Invalid EPATH format! item[\"{}\"] in [{}]".format(item, path))

        return " ".join(item for item in items)


    def __str__(self):
        indent = 4
        if self.hcomment != "":
            eds_str = "".join("$ {}\n".format(line.strip()) for line in self.hcomment.splitlines())

        # sections
        sorted_sections = [self.get_section("File")]
        sorted_sections.append(self.get_section("Device"))
        sorted_sections.append(self.get_section("Device Classification"))
        # listing sections without a class Id
        sorted_sections += [section for key, section in self.sections.items() if section not in sorted_sections and section.class_id is None]
        # listing sections with a class Ids
        sorted_sections += sorted([section for key, section in self.sections.items() if section not in sorted_sections], key = lambda section: section.class_id)

        for section in sorted_sections:
            if section.hcomment != "":
                eds_str += "".join("$ {}\n".format(line.strip()) for line in section.hcomment.splitlines())
            eds_str += "\n[{}]".format(section.name)

            if section.fcomment != "":
                eds_str += "\n"
                eds_str += "\n".join("".ljust(indent, " ") + "$ {}".format(line.strip()) for line in section.fcomment.splitlines())

            eds_str += "\n"

            # Entries
            for key, entry in section.entries.items():

                if entry.hcomment != "":
                    eds_str += "".join("".ljust(indent, " ") + "$ {}\n".format(line.strip()) for line in entry.hcomment.splitlines())
                eds_str += "".ljust(indent, " ") + "{} =".format(entry.name)

                # fields
                if len(entry.fields) == 1:
                    if "\n" in str(entry.fields[0].data):
                        eds_str += "\n"
                        eds_str += "\n".join("".ljust(2 * indent, " ") + line
                            for line in str(entry.fields[0].data).splitlines())
                        eds_str += ";"
                    else:
                        eds_str += "{};".format(entry.fields[0].data)
                    if entry.fields[0].fcomment != "":
                        eds_str += "".join("".ljust(indent, " ") +
                            "$ {}\n".format(line.strip()) for line in entry.fields[0].fcomment.splitlines())
                    eds_str += "\n"
                else: # entry has multiple fields
                    eds_str += "\n"

                    for fieldindex, field in enumerate(entry.fields):
                        singleline_field_str = "".ljust(2 * indent, " ") + "{}".format(field.data)

                        # separator
                        if (fieldindex + 1) == len(entry.fields):
                            singleline_field_str += ";"
                        else:
                            singleline_field_str += ","

                        # footer comment
                        if field.fcomment != "":
                            singleline_field_str = singleline_field_str.ljust(30, " ")
                            singleline_field_str += "".join("$ {}".format(line.strip()) for line in field.fcomment.splitlines())
                        eds_str += singleline_field_str + "\n"

        # end comment
        eds_str += "\n"
        if self.fcomment != "":
            eds_str += "".join("$ {}\n".format(line.strip()) for line in self.fcomment.splitlines())
        return eds_str

class Section:
    def __init__(self, eds, name, class_id=0):
        self.parent  = eds
        self.class_id = class_id
        self.name = name
        self.entries = {}
        self.hcomment = ""
        self.fcomment = ""

    def add_entry(self, entry_name, serialize = False):
        return self._eds.add_entry(self.name, entry_name)

    def has_entry(self, entry_name = None, entryindex = None):
        if entry_name.replace(" ", "").lower() in self.entries.keys():
            return True
        return False

    def get_entry(self, entry_name):
        return self.entries.get(entry_name)

    def get_field(self, entry_name, field_index):
        """
        To get a section.entry.field using the entry name + (ield name or field index.
        """
        entry = self.entries.get(entry_name)
        if entry:
            return entry.get_field(field_index)
        return None

    def list(self, indent=0):
        print ("".ljust(indent, " ") + self.__repr__())
        for key, entry in self.entries.items():
            entry.list(indent+4)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "SECTION({})".format(self.name)

class Entry:

    def __init__(self, section, name, index):
        self.index = index
        self.parent = section
        self.name = name
        self.fields = [] # Unlike the sections and entries, fields are implemented as a list.
        self.hcomment = ""
        self.fcomment = ""

    def add_field(self, field_value, datatype = None):
        return self.parent.parent.add_field(self.parent.name, self.name, field_value, datatype)

    def has_field(self, field):
        if isinstance(field, str): # field name
            fieldname = field.replace(" ", "").lower()
            for field in self.fields:
                if fieldname == field.name.replace(" ", "").lower():
                    return True
        elif isinstance(field, numbers.Number): # field index
            return field < len(entry.fields)
        else:
            raise TypeError("Inappropriate data type: {}".format(type(field)))

    def get_field(self, field_index):
        """
        if isinstance(field, str): # field name
            fieldname = field.replace(" ", "").lower()
            for field in self.fields:
                if fieldname == field:
                    return field
        """
        if field_index < len(self.fields):
            return self.fields[field_index]
        return None

    def list(self, indent=0):
        print("".ljust(indent, " ") + self.__repr__())
        for field in self.fields:
            print("".ljust(indent + 4, " ") + field.__repr__())

    @property
    def value(self):
        if len(self.fields) > 1:
            logger.warning("Entry has multiple fields. Only the first field is returned.")
        return self.fields[0].value

    def __str__(self):
        return self.name

    def __repr__(self):
        return "ENTRY({})".format(self.name)

class Field:
    def __init__(self, entry, name, data, index):
        self.index = index
        self.parent = entry
        self.name = name
        self.data = data # datatype object. Actually is the Field value containing also its type information
        self.data_types = [] # Valid datatypes a field supports

        self.hcomment = ""
        self.fcomment = ""

    @property
    def value(self):
        return self.data.value

    @value.setter
    def value(self, value):
        if type(self.data) != EMPTY or type(self.data) != EDS_UNDEFINED:
            if type(self.data).validate(value, self.data.range):
                self.data.value = value
                return
        # Setting with the actual datatype is failed. Try other supported types.
        if self.data_types:
            for datatype, valid_data in self.data_types:
                if datatype.validate(value, valid_data):
                    del self.data
                    self.data = datatype(value, valid_data)
                    return
        types_str = ", ".join("<{}>{}".format(datatype.__name__, valid_data)
                                for datatype, valid_data in self._data_types)
        raise Exception("Unable to set Field value! Data_type mismatch!"
            " [{}].{}.{} = ({}), should be a type of: {}"
            .format(self.parent.parent.name, self.parent.name, self.name, value, types_str))

    @property
    def datatype(self):
        return (type(self.data), self.data.range)

    def __str__(self):
        if self.data is None:
            return "\"\""
        # TODO: If a field of STRING contains multi lines of string, print each line as a seperate string.
        return "FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})".format(
            self.index, self.name, str(self.data), type(self.data).__name__, self.data.range)

    def __repr__(self):
        if self.data is None:
            return "FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})".format(
                self.index, self.name, "", "", "")
        # TODO: If a field of STRING contains multi lines of string, print each line as a seperate string.
        return "FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})".format(
            self.index, self.name, str(self.data), type(self.data).__name__, self.data.range)
