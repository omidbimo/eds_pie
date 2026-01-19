import os
import json
from pathlib import Path

from .cip_eds_types import *

class EDS:
    def __init__(self):
        self.protocol = None
        self.classification = None
        self.ref_db = EDS_RefDatabase()
        self.sections = {}
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

        return self.sections.get(self.protocol_db.get_section_name(class_id))

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
            return self.protocol_db.get_section_name(section_keyword) in self.sections.keys()
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

    def add_section(self, section_keyword, line_number=0):
        if section_keyword == "":
            raise Exception("Invalid section keyword! [{}]".format(section_keyword))

        if section_keyword in self.sections.keys():
            raise Exception("Duplicate section! [{}}".format(section_keyword))

        section_name = section_keyword # using section keyword as the default section name
        section = Section(self, section_keyword, section_name, None, line_number)
        self.sections.update({section_keyword: section})

        return section

    def add_entry(self, section_keyword, entry_keyword, line_number=0):
        section = self.get_section(section_keyword)
        if section is None:
            raise Exception("Section not found! [{}]".format(section_keyword))
        return section.add_entry(entry_keyword, line_number)


    def add_field(self, section_keyword, entry_keyword, field_value, field_data_type=None, line_number=0):
        """
        Fields must be added in order and no random access is allowed.
        """
        section = self.get_section(section_keyword)

        if section is None:
            raise Exception("Section not found! [{}]".format(section_keyword))

        entry = section.get_entry(entry_keyword)
        if entry is None:
            raise Exception("Entry not found! [{}]".format(entry_keyword))
        return entry.add_field(field_value, field_data_type, line_number)

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
        raise NotImplementedError

    def save(self, filename, overwrite = False):
        if os.path.isfile(filename) and overwrite == False:
            raise Exception("Failed to write to file! \"{}\" already exists and overrwite is not enabled.".format(filename))

        eds_content = self.__str__()

        hfile = open(filename, "w")
        hfile.write(eds_content)
        hfile.close()

    def sort_sections(self):
        # sections
        sorted_sections = []
        section = self.get_section("File")
        if section: sorted_sections.append(section)

        section = self.get_section("Device")
        if section: sorted_sections.append(section)

        section = self.get_section("Device Classification")
        if section: sorted_sections.append(section)

        sorted_sections += [section for key, section in self.sections.items() if section not in sorted_sections]
        return sorted_sections

    def to_json(self):
        json_doc = json.loads("{}")
        sorted_sections = self.sort_sections()
        for section in sorted_sections:
            json_doc[section.keyword] = {}
            # Entries
            for _, entry in section.entries.items():
                json_doc[section.keyword][entry.keyword] = ""
                # fields
                # Entry has only one field and the field's value has only one line of Data
                if len(entry.fields) == 1:
                    if isinstance(entry.fields[0].data, BOOL):
                        json_doc[section.keyword][entry.keyword] = entry.fields[0].value >= 1
                    elif isinstance(entry.fields[0].data, CIP_EDS_BASE_INT):
                        json_doc[section.keyword][entry.keyword] = entry.fields[0].value
                    else:
                        json_doc[section.keyword][entry.keyword] = str(entry.fields[0].data)
                else: # Entry holds multiple Fields
                    json_doc[section.keyword][entry.keyword] = []
                    for field in entry.fields:
                        if isinstance(field.data, BOOL):
                            json_doc[section.keyword][entry.keyword].append(field.value >= 1)
                        elif isinstance(field.data, CIP_EDS_BASE_INT):
                            json_doc[section.keyword][entry.keyword].append(field.value)
                        else:
                            json_doc[section.keyword][entry.keyword].append(str(field.data))

        return json_doc

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

    def validate(self):
        """
        Semantic validation of EDS objects.
        Verify whether EDS content make sense according to the CIP/EDS specification.
        """
        # Check if required sections are at required positions
        sections_list = list(self.sections) # Create a list of dictionary keys
        if len(self.sections) > 0 and sections_list[0] != "File":
            logger.warning("First section expected to be [File]. Found: [{}]".format(sections_list[0]))

        if len(self.sections) > 1 and sections_list[1] != "Device":
            logger.warning("Second section expected to be [Device]. Found: [{}]".format(sections_list[1]))

        device_classification_section = self.sections.get("Device Classification", None)
        if len(self.sections) > 2 and device_classification_section is None:
            logger.warning("Missing required section [Device Classification]")

        # Device Classification
        if device_classification_section is not None:

            classifications = list(device_classification_section.entries.items())
            if len(classifications) == 0:
                logger.warning("Missing required entry [Device Classification].Class1")
            else:
                index = 0
                public_classifications = self.ref_db.get_field_data_types("Device Classification", "ClassN", 0)["KEYWORD"]
                for keyword, entry in classifications:
                    index += 1
                    if keyword != "Class{}".format(index):
                        logger.warning("Unexpected [Device Classification].{} at position {}".format(index, keyword))
                    if index == 1 and entry.value in public_classifications and len(classifications) > 1:
                            logger.warning("[Device Classification].Class1 is a public classification. No further classifications are allowed but found {} more classification(s).".format(len(classifications) - 1))
                    if entry.value in public_classifications and self.classification is None:
                        self.classification = entry.value
                        if "EtherNetIP" in entry.value:
                            self.protocol = "EtherNetIP"
                        else:
                            self.protocol = entry.value
                        self.ref_db.set_protocol(self.protocol)

        # Validate sections, entries and fields then assign a data type to each field if possible
        for _, section in self.sections.items():
            section_name = self.ref_db.get_section_name(section.keyword)
            if section_name is None:
                if not VENDOR_SPECIFIC.validate(section.keyword):
                    logger.warning("Unknown Section [{}]".format(section.keyword))
            else:
                # replace the default name with the correct one from reflib
                section.name = section_name
                section.class_id = self.ref_db.get_section_class_id(section.keyword)

            for _, entry in section.entries.items():
                entry_name = self.ref_db.get_entry_name(section.keyword, entry.keyword)
                if entry_name is None:
                    if not VENDOR_SPECIFIC.validate(section.keyword) and not VENDOR_SPECIFIC.validate(entry.keyword):
                        logger.warning("Unknown Entry [{}].{}".format(section.keyword, entry.keyword))
                else:
                    # replace the default name with the correct one from reflib
                    entry.name = entry_name

                for field_index, field in enumerate(entry.fields):
                    if self.ref_db.has_field(section.keyword, entry.keyword, field_index):
                        field.name = self.ref_db.get_field_name(section.keyword, entry.keyword, field_index)
                        field.data_types = self.ref_db.get_field_data_types(section.keyword, entry.keyword, field_index)
                        field_data_object = self.ref_db.assign_type_to_field(section.keyword, entry.keyword, field_index, field.value)

                        # Failed to find a proper data type for the field. Handle special case of EnumN keyword
                        if field_data_object is None and section.name == "Parameters" and "Enum" in entry.keyword:
                            associated_param_field = self.get_field("Params", entry.keyword.replace("Enum", "Param"), 4)
                            type_name = CIP_TYPES.stringify(getnumber(associated_param_field.value))
                            if type_name:
                                field_data_object = self.ref_db.get_type(type_name)(field.value)

                        if field_data_object is not None:
                            field.data = field_data_object

                        else:
                            # Wasn't able to assign a data type to this field.
                            # Introduce the list of acceptable data types for this specific field
                            data_types = self.ref_db.get_field_data_types(section.keyword, entry.keyword, field_index)
                            types_str = ", ".join("<{}({})>".format(type_name, type_meta)
                                                    for type_name, type_meta in data_types.items())
                            if field.value != "":
                                logger.error("Data_type mismatch! [{}].{}.{} = ({}), Field should be of type: {}".format(
                                    section.keyword, entry.keyword, field_index, field.value, types_str))
                    else:
                        if not VENDOR_SPECIFIC.validate(section.keyword) and not VENDOR_SPECIFIC.validate(entry.keyword):
                            logger.warning("Unknown Field [{}].{}.{}".format(section.keyword, entry.keyword, field.name))

        for _, section in self.sections.items():
           for _, entry in section.entries.items():
                for field in entry.fields:
                    if isinstance(field.data, REF):
                        if "Param" in field.value:
                            if self.get_entry("Params", field.value) is None:
                                logger.error("Missing referenced Entry [Params].{} required by [{}].{}.{}".format(
                                    field.value, section.keyword, entry.keyword, field.name))
                        elif "Assem" in field.value:
                            if self.get_entry("Assembly", field.value) is None:
                                logger.error("Missing referenced Entry [Assembly].{} required by [{}].{}.{}".format(
                                    field.value, section.keyword, entry.keyword, field.name))
                        else:
                            logger.warning("Reference checking not implemented!")
                            # TODO
    def __str__(self):
        indent = 4
        eds_str = ""

        if self.hcomment != "":
            eds_str = "\n".join("$ {}".format(line.strip()) for line in self.hcomment.splitlines())

        # sections
        sorted_sections = []
        section = self.get_section("File")
        if section: sorted_sections.append(section)

        section = self.get_section("Device")
        if section: sorted_sections.append(section)

        section = self.get_section("Device Classification")
        if section: sorted_sections.append(section)

        sorted_sections += [section for key, section in self.sections.items() if section not in sorted_sections]

        for section in sorted_sections:
            if section.hcomment:
                eds_str += "\n" + "\n".join("$ {}".format(line.strip()) for line in section.hcomment.splitlines())
            eds_str += "\n[{}]".format(section.keyword)

            if section.fcomment != "":
                eds_str += "".ljust(indent, " ") + "$ {}".format(section.fcomment.strip())
            eds_str += "\n"

            # Entries
            for _, entry in section.entries.items():

                if entry.hcomment:
                    eds_str += "".join("".ljust(indent, " ") + "$ {}\n".format(line.strip()) for line in entry.hcomment.splitlines())
                eds_str += "".ljust(indent, " ") + "{} = ".format(entry.keyword)

                # fields
                # Entry has only one field and the field's value has only one line of Data
                if len(entry.fields) == 1 and len(str(entry.fields[0].data).splitlines()) <= 1:
                    # Print entry, field and comment on the same line
                    if isinstance(entry.fields[0].data, STRING) or isinstance(entry.fields[0].data, EPATH):
                        field_str = "\"{}\";".format(str(entry.fields[0].data))
                    else:
                        field_str = "{};".format(str(entry.fields[0].data))
                    if entry.fields[0].fcomment:
                        field_str += " $ ".rjust(indent, " ") + ("\n" + " $ ".rjust(32, " ")).join("{}".format(line.strip()) for line in entry.fields[0].fcomment.splitlines())
                    eds_str += field_str + "\n"
                else: # Entry holds multiple Fields
                    # print fields on a new line separated by commas
                    for index, field in enumerate(entry.fields):
                        field_str = "\n" + "".ljust(2 * indent) # Indent for the first field
                        if isinstance(field.data, STRING) or isinstance(field.data, EPATH) and field.value:
                            field_str += "\"" + "\n".ljust((2 * indent) + 1, " ").join(line.strip() for line in str(field.data).splitlines()) + "\""
                        else:
                            field_str += "\n".ljust((2 * indent) + 1, " ").join(line.strip() for line in str(field.data).splitlines())
                        if index + 1 == len(entry.fields):
                            field_str += ";"
                        else:
                            field_str += ","

                        if field.fcomment:
                            field_str += " $ ".rjust(33-len(field_str), " ") # Indent for the first field
                            field_str +=  ("\n" + " $ ".rjust(32, " ")).join("{}".format(line.strip()) for line in field.fcomment.splitlines())

                        eds_str += field_str
                    eds_str += "\n"
        # end comment
        eds_str += "\n"
        if self.fcomment:
            eds_str += "".join("$ {}\n".format(line.strip()) for line in self.fcomment.splitlines())
        return eds_str

class Section:
    def __init__(self, eds, keyword, name, class_id=0, line_number=0):
        self.parent  = eds
        self.keyword = keyword
        self.name = name
        self.class_id = class_id
        self.line_number = line_number # line number in the eds data. required for comment assignment
        self.entries = {}
        self.hcomment = ""
        self.fcomment = ""

    def add_entry(self, entry_keyword, line_number=0):
        if entry_keyword == "":
            raise Exception("Invalid Entry keyword! [{}]\"{}\"".format(self.keyword, entry_keyword))

        if entry_keyword in self.entries.keys():
            raise Exception("Duplicate Entry! [{}]\"{}\"".format(self.keyword, entry_keyword))

        entry_name = entry_keyword # using entry keyword as the default entry name
        entry = Entry(self, entry_keyword, entry_name, line_number)
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

    def list(self, indent=0):
        print ("".ljust(indent, " ") + self.__repr__())
        for key, entry in self.entries.items():
            entry.list(indent+4)

    def __str__(self):
        return self.keyword

    def __repr__(self):
        return "SECTION({})".format(self.keyword)

class Entry:

    def __init__(self, section, keyword, name, line_number=0):
        self.parent = section
        self.keyword = keyword
        self.name = name
        self.line_number = line_number # line number in the eds data. required for comment assignment
        self.fields = [] # Unlike the sections and entries, fields are implemented as a list.
        self.hcomment = ""
        self.fcomment = ""

    def add_field(self, field_value, field_data_type=None, line_number=0):
        entry_keyword = self.keyword
        section_keyword = self.parent.keyword

        field_data_object = None # This going to be an instance of CIP_TYPE
        field_name = "field{}".format(len(self.fields))

        if field_data_type:
            field_data_object = field_data_type(field_value)
        elif field_value == "":
            field_data_object = EMPTY(field_value)
        elif VENDOR_SPECIFIC.validate(field_value):
            field_data_object = VENDOR_SPECIFIC(field_value)
        else:
            field_data_object = UNDEFINED(field_value)

        field = Field(self, field_name, field_data_object, len(self.fields), line_number)
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
    def __init__(self, entry, name, data, index, line_number=0):
        self.index = index
        self.parent = entry
        self.name = name
        self.line_number = line_number # line number in the eds data. required for comment assignment
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
        data = "\"\"" if self.data is None else self.data
        return str(data)

    def __repr__(self):
        if self.data is None:
            return "FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})".format(
                self.index, self.name, "", "", "")

        return "FIELD(index: {}, name: \"{}\", value: ({}), type: <{}>{})".format(
            self.index, self.name, str(self.data), type(self.data).__name__, self.data.range)

class EDS_RefDatabase:
    def __init__(self):
        self.multi_protocol_db = {}
        self.meta_db = {}
        self.common_object_db = {}
        self.protocol = None # Default: Generic
        self.protocol_db = {}

        ref_dir = Path(__file__).parent / "references"
        json_files = [f for f in ref_dir.iterdir() if f.suffix==".json"]

        if not json_files:
            logger.warning("Found no reference Databases! Semantic checking cannot be performed.")

        for file in json_files:
            with file.open("r", encoding="utf-8") as src:
                data = json.loads(src.read())
                if data.get("project", None) == "eds_pie" and data["lib_name"] == "MetaEDS":
                    self.meta_db = data
                elif data.get("project", None) == "eds_pie" and data["lib_name"] == "Common Object Class":
                    self.common_object_db = data
                elif data.get("project", None) == "eds_pie" and file != "edslib_schema.json":
                    self.multi_protocol_db[data["lib_name"]] = data
        assert self.meta_db
        assert self.common_object_db
        self.protocol_db = self.multi_protocol_db

    def set_protocol(self, protocol):
        if protocol in ["CompoNet", "ControlNet", "DeviceNet", "EtherNetIP"]:
            if protocol in self.multi_protocol_db:
                self.protocol = protocol
                self.protocol_db = {protocol: self.multi_protocol_db[protocol]}
                logger.info("Protocol Database access restricted to {}.".format(protocol))
            else:
                logger.error("Requested Protocol Database \"{}\" not available!".format(protocol))
        else:
            logger.error("Requested Protocol Database \"{}\" not a valid protocol!".format(protocol))

    def reset_protocol(self):
        self.protocol = None
        self.protocol_db = self.multi_protocol_db
        logger.info("Protocol Database access set to Generic.")

    def get_section(self, section_keyword):
        section = None

        section = self.meta_db["sections"].get(section_keyword, None)
        if section is None:
            for lib_name, lib in self.protocol_db.items():
                section = lib["sections"].get(section_keyword, None)
                if section:
                    if self.protocol is None:
                        # Section found in a protocol specific database. Restrict the access to other protocols
                        self.set_protocol(lib_name)
                    break
        return section

    def get_section_name_byclass_id(self, class_id):
        """
        To get a protocol specific EDS section_keyword by its CIP class ID
        """
        for lib_name, lib in self.protocol_db.items():
            for section in lib["sections"]:
                if section["class_id"] == class_id:
                    return section
        return ""

    def get_section_name(self, section_keyword):
        """
        To get a protocol specific EDS section name by its section keyword
        """
        section = self.get_section(section_keyword)
        if section:
            return section["name"]
        return None

    def get_section_class_id(self, section_keyword):
        section = self.get_section(section_keyword)
        if section:
            return section.get("class_id", None)
        return None

    def has_section(self, section_keyword):
        if section_keyword in self.meta_db["sections"]:
            return True
        for lib_name, lib in self.protocol_db.items():
            if section_keyword in lib["sections"]:
                return True
        return False

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

        # First check if the entry is in common class object
        section_id = self.get_section_class_id(section_keyword)
        if section_id and section_id > 0:
            entry = self.common_object_db["sections"]["CommonObjectClass"]["entries"].get(entry_keyword, None)
        if entry is None:
            section = self.get_section(section_keyword)
            if section:
                entry = section["entries"].get(entry_keyword, None)
        return entry

    def get_entry_name(self, section_keyword, entry_keyword):
        entry = self.get_entry(section_keyword, entry_keyword)
        if entry:
            return entry["name"]
        return None

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

    def get_type(self, type_name):
        return getattr(__import__("eds_pie.cip_eds_types", fromlist=[type_name]), type_name, None)

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

    def assign_type_to_field(self, section_keyword, entry_keyword, field_index, field_value):
        ref_field = self.get_field_byindex(section_keyword, entry_keyword, field_index)
        if ref_field is not None:
            ref_data_types = ref_field.get("data_types", {})

            for type_name, type_meta in ref_data_types.items():
                if self.validate(type_name, type_meta, field_value):
                    return self.get_type(type_name)(field_value, type_meta)
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
