import os
import sys
import json

from cip_eds_types import *

class EDS_RefLib:
    def __init__(self):
        self.libs = {}

        for file in os.listdir():
            if file.endswith(".json"):
                with open(file, "r") as src:
                    data = json.loads(src.read())
                    if data.get("project", None) ==  "eds_pie" and file != "edslib_schema.json":
                        self.libs[data["protocol"].lower()] = data

    def get_lib_name(self, section_keyword):
        for _, lib in self.libs.items():
            if section_keyword in lib["sections"]:
                return lib["protocol"]
        return None

    def get_section_name(self, class_id):
        """
        To get a protocol specific EDS section_keyword by its CIP class ID
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

    def has_entry(self, section_keyword, entry_keyword):
        """
        To get an entry dictionary by its section name and entry name
        """
        return self.get_entry(section_keyword, entry_keyword) is not None

    def get_entry(self, section_keyword, entry_keyword):
        """
        To get an entry dictionary by its section name and entry name
        """
        entry = None

        if entry_keyword[-1].isdigit(): # Enumerated Entry
            entry_keyword = entry_keyword.rstrip(digits) + "N"

        section = self.get_section(section_keyword)
        if section:
            # First check if the entry is in common class object
            if section["class_id"] and section["class_id"] != 0:
                common_section = self.get_section("Common Object Class")
                entry = common_section["entries"].get(entry_keyword, None)

            if entry is None:
                entry = section["entries"].get(entry_keyword, None)
        return entry

    def has_field(self, section_keyword, entry_keyword, field_index):
        field = None
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            """
            If the requested index is greater than listed fields in the lib,
            the field is possibly an enumerated field. re-calculate the index.
            """
            fields = entry.get("fields")
            if field_index < len(entry["fields"]) or entry.get("enumerated_fields", None):
                return True
        return False

    def get_field_byindex(self, section_keyword, entry_keyword, field_index):
        """
        To get a field dictionary by its section name and entry name and field index
        """
        field = None
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            """
            If the requested index is greater than listed fields in the lib,
            the field is possibly an enumerated field. re-calculate the index.
            """
            fields = entry.get("fields")

            if field_index < len(entry["fields"]) or entry.get("enumerated_fields", None):
                if field_index >= len(entry["fields"]):
                    # Calculating reference field index
                    field_index = (field_index % entry["enumerated_fields"]["enum_member_count"]) + entry["enumerated_fields"]["first_enum_field"] - 1
                field = entry["fields"][field_index]
        return field

    def get_field_byname(self, section_keyword, entry_keyword, field_name):
        """
        To get a field dictionary by its section name and entry name and field name
        """
        field = None
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            if field_name[-1].isdigit(): # Incremental field_name
                field_name = field_name.rstrip(digits) + "N"

            for fld in entry["fields"]:
                if fld["name"] == field_name:
                    field = fld
        return field
    """
    def get_type(self, cip_typeid):
        return self.supported_data_types[cip_typeid]
    """
    def get_required_sections(self):
        required_sections = {}

        for _, lib in self.libs.items():
            for section_keyword, section in lib["sections"].items():
                if section["required"] == True:
                    required_sections.update({section_keyword: section})

        return required_sections

    def get_type(self, type_name):
        return getattr(__import__("cip_eds_types"), type_name, None)

    def get_field_data_types(self, section_keyword, entry_keyword, field_index):
        field = self.get_field_byindex(section_keyword, entry_keyword, field_index)
        if field is not None:
            return field.get("data_types", None)
        return None

    def get_field_name(self, section_keyword, entry_keyword, field_index):
        field = self.get_field_byindex(section_keyword, entry_keyword, field_index)
        if field is not None:
            return field.get("name", None)
        return None

    def find_proper_data_type_for_field_value(self, section_keyword, entry_keyword, field_index, field_value):
        ref_field = self.get_field_byindex(section_keyword, entry_keyword, field_index)
        if ref_field is not None:
            cip_data_instance = None
            ref_data_types = ref_field.get("data_types", {})

            for type_name, type_info in ref_data_types.items():
                if self.validate(type_name, type_info, field_value):
                    return type_name, type_info

        return None

    def validate(self, type_name, type_info, value):
        dt = self.get_type(type_name)
        if dt:
            return dt.validate(value, type_info)
        return False

    def is_required_field(self, section_keyword, entry_keyword, field_index):
        field = self.get_field_byindex(section_keyword, entry_keyword, field_index)
        if field:
            return field.get("required", False)
        return False
    """
    def is_required_field(self, section_keyword, entry_keyword, field_name):
        field = self.get_field_byname(section_keyword, entry_keyword, field_name)
        if field:
            return field["required"]
        return False
    """
class EDS:

    def __init__(self):
        self.protocol = None
        self.sections = {}
        self.ref_libs = EDS_RefLib()
        self.hcomment = "" # Heading comment
        self.fcomment = "" # End comment

    def list(self, indent=0):
        for key, section in self.sections.items():
            section.list(indent)

    def get_section(self, section_keyword=None, class_id=0):
        """
        To get a section object by its EDS keyword or by its CIP classID.
        """
        if section_keyword:
            return self.sections.get(section_keyword)

        return self.sections.get(self.ref_libs.get_section_name(class_id))

    def get_entry(self, section_keyword, entry_keyword):
        """
        To get an entry by its section name and its entry name.
        """
        section = self.get_section(section_keyword)
        if section:
            return section.get_entry(entry_keyword)
        return None

    def get_field(self, section_keyword, entry_keyword, field_index):
        """
        To get an field by its section name/section id, its entry name and its field anme/field index
        """
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            return entry.get_field(field_index)
        return None

    def get_value(self, section_keyword, entry_keyword, field_index=0):
        field = self.get_field(section_keyword, entry_keyword, field_index)
        if field:
            return field.value
        return None

    def set_value(self, section_keyword, entry_keyword, field_index, value):
        field = self.get_field(section_keyword, entry_keyword, field_index)
        if field is None:
            raise Exception("Not a valid field! Unable to set the field value.")
        field.value = value

    def has_section(self, section_keyword):
        """
        To check if the EDS contains a section by its EDS keyword or by its CIP classID.
        """
        if isinstance(section_keyword, str):
            return section_keyword in self.sections.keys()
        if isinstance(section_keyword, numbers.Number):
            return self.ref_libs.get_section_name(section_keyword, self.protocol) in self.sections.keys()
        raise TypeError("Inappropriate data type: {}".format(type(section_keyword)))

    def has_entry(self, section_keyword, entry_keyword):
        section_keyword = self.get_section(section_keyword)
        if section_keyword:
            return entry_keyword in section_keyword.entries.keys()
        return False

    def has_field(self, section_keyword, entry_keyword, field_index):
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            return field_index < len(entry.fields)
        return False

    def add_section(self, section_keyword):
        if section_keyword == "":
            raise Exception("Invalid section keyword! [{}]".format(section_keyword))

        if section_keyword in self.sections.keys():
            raise Exception("Duplicate section! [{}}".format(section_keyword))

        section_name = section_keyword
        try:
            section_name = self.ref_libs.get_section(section_keyword)["name"]
        except Exception as ex:
            #print(ex)
            logger.warning("Unknown Section [{}]".format(section_keyword))

        section = Section(self, section_keyword, section_name, self.ref_libs.get_section_id(section_keyword))
        self.sections.update({section_keyword: section})

        return section

    def add_entry(self, section_keyword, entry_keyword):
        section = self.get_section(section_keyword)
        if section is None:
            raise Exception("Section not found! [{}]".format(section_keyword))
        return section.add_entry(entry_keyword)


    def add_field(self, section_keyword, entry_keyword, field_value, field_data_type=None):
        """
        Fields must be added in order and no random access is allowed.
        """
        section = self.get_section(section_keyword)

        if section is None:
            raise Exception("Section not found! [{}]".format(section_keyword))

        entry = section.get_entry(entry_keyword)
        if entry is None:
            raise Exception("Entry not found! [{}]".format(entry_keyword))
        return entry.add_field(field_value, field_data_type)

    def remove_section(self, section_keyword, removetree = False):
        section = self.get_section(section_keyword)

        if section is None: return
        if not section.entries:
            del self.sections[section_keyword]
        elif removetree:
            for entry in section.entries:
                self.remove_entry(section_keyword, entry.keyword, removetree)
            del self.sections[section_keyword]
        else:
            logger.error("Unable to remove section! [{}] contains one or more entries."
                "Remove the entries first or use removetree = True".format(section.keyword))

    def remove_entry(self, section_keyword, entry_keyword, removetree = False):
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry is None: return
        if not entry.fields:
            section = self.get_section(section_keyword)
            del section.entries[entry_keyword]
        elif removetree:
            entry.fields = []
        else:
            logger.error("Unable to remove entry! [{}].{} contains one or more fields."
                "Remove the fields first or use removetree = True".format(section.keyword, entry.keyword))

    def remove_field(self, section_keyword, sentryname, fieldindex):
        # TODO
        pass

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
                    entry_keyword = item
                    field = self.get_field("Params", entry_keyword, "Default Value")
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
        sorted_sections += [section for key, section in self.sections.items() if section not in sorted_sections]

        for section in sorted_sections:
            if section.hcomment != "":
                eds_str += "".join("$ {}\n".format(line.strip()) for line in section.hcomment.splitlines())
            eds_str += "\n[{}]".format(section.keyword)

            if section.fcomment != "":
                eds_str += "\n"
                eds_str += "\n".join("".ljust(indent, " ") + "$ {}".format(line.strip()) for line in section.fcomment.splitlines())

            eds_str += "\n"

            # Entries
            for key, entry in section.entries.items():

                if entry.hcomment != "":
                    eds_str += "".join("".ljust(indent, " ") + "$ {}\n".format(line.strip()) for line in entry.hcomment.splitlines())
                eds_str += "".ljust(indent, " ") + "{} =".format(entry.keyword)

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
    def __init__(self, eds, keyword, name, class_id=0):
        self.parent  = eds
        self.keyword = keyword
        self.name = name
        self.class_id = class_id
        self.entries = {}
        self.hcomment = ""
        self.fcomment = ""

    def add_entry(self, entry_keyword):
        if entry_keyword == "":
            raise Exception("Invalid Entry keyword! [{}]\"{}\"".format(self.keyword, entry_keyword))

        if entry_keyword in self.entries.keys():
            raise Exception("Duplicate Entry! [{}]\"{}\"".format(self.keyword, entry_keyword))

        entry_name = entry_keyword
        # Search for the same section:entry inside the reference lib
        ref_libs = self.get_ref_libs()
        try:
            entry_name = ref_libs.get_entry(self.keyword, entry_keyword)["name"]
        except Exception as ex:
            #print(ex)
            logger.warning("Unknown Entry [{}].{}".format(self.keyword, entry_keyword))

        entry = Entry(self, entry_keyword, entry_name)
        self.entries[entry_keyword] = entry

        return entry

    def has_entry(self, entry_keyword = None, entryindex = None):
        if entry_keyword.replace(" ", "").lower() in self.entries.keys():
            return True
        return False

    def get_entry(self, entry_keyword):
        return self.entries.get(entry_keyword)

    def get_field(self, entry_keyword, field_index):
        """
        To get a section.entry.field using the entry name + (ield name or field index.
        """
        entry = self.entries.get(entry_keyword)
        if entry:
            return entry.get_field(field_index)
        return None

    def get_value(self, entry_keyword, field_index=0):
        field = self.get_field(entry_keyword, field_index)
        if field:
            return field.value
        return None

    def get_ref_libs(self):
        parent_eds = self.parent
        return parent_eds.ref_libs

    def list(self, indent=0):
        print ("".ljust(indent, " ") + self.__repr__())
        for key, entry in self.entries.items():
            entry.list(indent+4)

    def __str__(self):
        return self.keyword

    def __repr__(self):
        return "SECTION({})".format(self.keyword)

class Entry:

    def __init__(self, section, keyword, name):
        self.parent = section
        self.keyword = keyword
        self.name = name
        self.fields = [] # Unlike the sections and entries, fields are implemented as a list.
        self.hcomment = ""
        self.fcomment = ""

    def get_ref_libs(self):
        parent_section = self.parent
        parent_eds = parent_section.parent
        return parent_eds.ref_libs

    def add_field(self, field_value, field_data_type=None):

        entry_keyword = self.keyword
        section_keyword = self.parent.keyword
        ref_libs = self.get_ref_libs()

        field_data_object = None # This going to be an instance of CIP_TYPE
        field_name = "field{}".format(len(self.fields))

        # Try to find a proper CIP_TYPE for this field using the reference libraries.
        if ref_libs.has_field(section_keyword, entry_keyword, len(self.fields)):
            field_name = field_name.rstrip("N") + str(len(self.fields) + 1)
            dt = ref_libs.find_proper_data_type_for_field_value(section_keyword, entry_keyword, len(self.fields), field_value)
            if dt is None:
                # Wasn't able to assign a data type to field using available references
                # Introduce the list of acceptable data types for this specific field
                ref_data_types = ref_libs.get_field_data_types(section_keyword, entry_keyword, len(self.fields))
                types_str = ", ".join("<{}({})>".format(ref_libs.get_type(type_name).__name__, type_info) for type_name, type_info in ref_data_types.items())

                if ref_libs.is_required_field(section_keyword, entry_keyword, len(self.fields)):
                    raise Exception("Data type mismatch! [{}].{}.{} = ({}), Field should be of type: {}".format(section_keyword, entry_keyword, field_name, field_value, types_str))
                elif field_value != "":
                    logger.error("Data_type mismatch! [{}].{}.{} = ({}), Field should be of type: {}".format(section_keyword, entry_keyword, field_name, field_value, types_str))
            else:
                # CIP_TYPE is found: instantiate it
                type_name, type_info = dt
                field_data_object = ref_libs.get_type(type_name)(field_value, type_info)

                assert field_data_object is not None

        if field_data_object is None:
            # Wasn't able to assign a CIP_TYPE to the field
            if field_data_type is not None:
                field_data_object = field_data_type(field_value)
            elif field_value == "":
                logger.info("Field [{}].{}.{} has no value. Switched to EMPTY field.".format(section_keyword, entry_keyword, field_name))
                field_data_object = EMPTY(field_value)
            else:
                if VENDOR_SPECIFIC.validate(field_value):
                    logger.warning("Unknown Field [{}].{}.{} = {}. Switched to VENDOR_SPECIFIC field.".format(section_keyword, entry_keyword, field_name, field_value))
                    field_data_object = VENDOR_SPECIFIC(field_value)
                else:
                    logger.warning("Unknown Field [{}].{}.{} = {}. Switched to UNDEFINED field.".format(section_keyword, entry_keyword, field_name, field_value))
                    field_data_object = UNDEFINED(field_value)

        assert field_data_object is not None

        field = Field(self, field_name, field_data_object, len(self.fields))
        field.data_types = ref_libs.get_field_data_types(section_keyword, entry_keyword, len(self.fields))
        self.fields.append(field)

        return field

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

    def get_field(self, field_index=0):
        """
        Also works with Negative indexing
        """
        field = None
        try:
            field = self.fields[field_index]
        except:
            pass
        return field

    def get_value(self, field_index=0):
        """
        Also works with Negative indexing
        """
        value = None
        try:
            value = self.fields[field_index].value
        except:
            pass
        return value

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
        if type(self.data) != EMPTY or type(self.data) != UNDEFINED:
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
                                for datatype, valid_data in self.data_types)
        raise Exception("Unable to set Field value! Data_type mismatch!"
            " [{}].{}.{} = ({}), should be a type of: {}"
            .format(self.parent.parent.keyword, self.parent.keyword, self.name, value, types_str))

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
