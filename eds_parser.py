
from cip_eds_types import *
from eds_lexer import Lexer
from eds import EDS

import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')

class State(ENUMS):
    EXPECT_SECTION = 0
    EXPECT_ENTRY   = 1
    EXPECT_SECTION_OR_ENTRY = 2
    EXPECT_FIELD   = 3

class Parser:
    def __init__(self, eds_data, showprogress = False):
        self.lexer = Lexer(eds_data)
        self.state = State.EXPECT_SECTION
        self.eds = EDS()
        self.section_in_process = None
        self.entry_in_process = None
        self.field_in_process = None
        self.hcomment = ""
        self.fcomment = ""

    def parse(self):

        while True:
            token = self.lexer.get_token()

            if token.type is TOKEN_TYPE.EOF:
                break

            if self.match(token, TOKEN_TYPE.COMMENT):
                self.cashe_comment(token)
                continue

            if self.state is State.EXPECT_SECTION:
                self.expect(token, TOKEN_TYPE.SECTION)
                self.entry_in_process = None
                self.field_in_process = None
                self.section_in_process = self.eds.add_section(token.value)

                if self.section_in_process is None:
                    raise Exception("Unable to create Section: {}".format(token.value))

                self.add_comment(self.section_in_process)

                self.state = State.EXPECT_ENTRY
                continue


            if self.state is State.EXPECT_ENTRY:

                self.expect(token, TOKEN_TYPE.IDENTIFIER)
                self.entry_in_process = None
                self.entry_in_process = self.eds.add_entry(self.section_in_process.name, token.value)

                if self.entry_in_process is None:
                    raise Exception("Unable to create Entry: {}".format(token.value))

                self.add_comment(self.entry_in_process)

                # Expecting at least one field.
                self.expect(self.lexer.get_token(), TOKEN_TYPE.OPERATOR, SYMBOLS.ASSIGNMENT)
                self.state = State.EXPECT_FIELD
                continue

            if self.state is State.EXPECT_FIELD:

                # A field can be also empty
                if self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.SEMICOLON) or self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.COMMA):
                    self.field_in_process = self.eds.add_field(self.section_in_process.name, self.entry_in_process.name, "")
                else:
                    self.field_in_process = self.eds.add_field(self.section_in_process.name, self.entry_in_process.name, token.value, token.type)
                    token = self.lexer.get_token()

                if self.field_in_process is None:
                    raise Exception("Unable to create Field: {}".format(token.value))

                self.add_comment(self.field_in_process)

                if self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.COMMA):
                    continue

                self.expect(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.SEMICOLON)
                # End of Entry. The next token might be an entry or a new section
                self.state = State.EXPECT_SECTION_OR_ENTRY
                continue

            if self.state is State.EXPECT_SECTION_OR_ENTRY:

                if self.match(token, TOKEN_TYPE.SECTION):
                    self.entry_in_process = None
                    self.field_in_process = None
                    self.section_in_process = self.eds.add_section(token.value)
                    if self.section_in_process is None:
                        raise Exception("Unable to create section: {}".format(token.value))
                    self.add_comment(self.section_in_process)
                    self.state = State.EXPECT_ENTRY
                    continue

                self.expect(token, TOKEN_TYPE.IDENTIFIER)
                self.entry_in_process = None
                self.entry_in_process = self.eds.add_entry(self.section_in_process.name, token.value)
                if self.entry_in_process is None:
                    raise Exception("Unable to create entry: {}".format(token.value))
                self.add_comment(self.entry_in_process)
                # Expecting at least one field.
                self.expect(self.lexer.get_token(), TOKEN_TYPE.OPERATOR, SYMBOLS.ASSIGNMENT)
                self.state = State.EXPECT_FIELD
                continue

            raise Exception(__name__ + ':> Invalid Parser state! {}'.format(self.state))

        return self.eds

    def cashe_comment(self, token):
        if self.field_in_process:
            self.fcomment += token.value.strip() + '\n'
        elif self.entry_in_process:
            self.fcomment += token.value.strip() + '\n'
        elif self.section_in_process:
            self.fcomment += token.value.strip() + '\n'
        else:
            self.hcomment += token.value.strip() + '\n'

    def add_comment(self, obj):
        print(obj.name, self.fcomment)
        obj.hcomment = self.hcomment
        obj.fcomment = self.fcomment
        self.hcomment = ""
        self.fcomment = ""

    def on_EOF(self):
        # The rest of cached comments belong to no elements
        self.eds.end_comment = self.fcomment
        self.fcomment = ""

    def expect(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is None or token.value == expected_value:
                return

        if expected_value:
            raise Exception("Unexpected token! Expected: (\"{}\": {}) but found: {}".format(
                            TOKEN_TYPE.stringify(expected_type), expected_value, token))
        raise Exception("Unexpected token! Expected: (\"{}\") but found: {}".format(
                        TOKEN_TYPE.stringify(expected_type), token))

    def match(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is not None:
                if token.value != expected_value:
                    return False
            return True
        return False
