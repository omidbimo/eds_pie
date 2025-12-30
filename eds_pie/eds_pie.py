
from .cip_eds_types import *
from .eds_lexer import Lexer, TOKEN_TYPES, SYMBOLS
from .eds import EDS

from ._version import __version__

import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

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
        self.cached_comment = ""

    def parse(self):

        while True:
            token = self.lexer.get_token()

            if token.type is TOKEN_TYPES.EOF:
                self.on_EOF()
                break

            if self.match(token, TOKEN_TYPES.COMMENT):
                self.add_comment(token.value, token.line)
                continue

            if self.state is State.EXPECT_SECTION:
                self.expect(token, TOKEN_TYPES.SECTION)
                self.entry_in_process = None
                self.field_in_process = None
                self.section_in_process = self.eds.add_section(token.value, token.line)

                if self.section_in_process is None:
                    raise Exception("Unable to create Section: {}".format(token.value))

                if self.cached_comment:
                    self.section_in_process.hcomment = self.cached_comment
                    self.cached_comment = ""

                self.state = State.EXPECT_ENTRY
                continue


            if self.state is State.EXPECT_ENTRY:

                self.expect(token, TOKEN_TYPES.IDENTIFIER)
                self.entry_in_process = None
                self.entry_in_process = self.eds.add_entry(self.section_in_process.keyword, token.value, token.line)

                if self.entry_in_process is None:
                    raise Exception("Unable to create Entry: {}".format(token.value))

                if self.cached_comment:
                    self.entry_in_process.hcomment = self.cached_comment
                    self.cached_comment = ""

                # Expecting at least one field.
                self.expect(self.lexer.get_token(), TOKEN_TYPES.OPERATOR, SYMBOLS.ASSIGNMENT)
                self.state = State.EXPECT_FIELD
                continue

            if self.state is State.EXPECT_FIELD:

                if self.match(token, TOKEN_TYPES.SEPARATOR, SYMBOLS.SEMICOLON) or self.match(token, TOKEN_TYPES.SEPARATOR, SYMBOLS.COMMA):
                    # Empty Field
                    self.field_in_process = self.eds.add_field(self.section_in_process.keyword, self.entry_in_process.keyword, "", line_number=token.line)
                else:
                    # Store token data to concatenate field values if required
                    field_value = token.value

                    # Strings can be teared down into multiple lines
                    if token.type == TOKEN_TYPES.STRING:
                        while True:
                            token = self.lexer.get_token()
                            if not self.match(token, TOKEN_TYPES.STRING): break
                            field_value += token.value
                    else:
                        token = self.lexer.get_token()

                    self.field_in_process = self.eds.add_field(self.section_in_process.keyword, self.entry_in_process.keyword, field_value, line_number=token.line)

                if self.field_in_process is None:
                    raise Exception("Unable to create Field: {}".format(token.value))

                if self.cached_comment:
                    self.field_in_process.hcomment = self.cached_comment
                    self.cached_comment = ""

                if self.match(token, TOKEN_TYPES.SEPARATOR, SYMBOLS.COMMA):
                    continue

                self.expect(token, TOKEN_TYPES.SEPARATOR, SYMBOLS.SEMICOLON)
                # End of Entry. The next token might be an entry or a new section
                self.state = State.EXPECT_SECTION_OR_ENTRY
                continue

            if self.state is State.EXPECT_SECTION_OR_ENTRY:

                if self.match(token, TOKEN_TYPES.SECTION):
                    self.entry_in_process = None
                    self.field_in_process = None
                    self.section_in_process = self.eds.add_section(token.value, token.line)
                    if self.section_in_process is None:
                        raise Exception("Unable to create section: {}".format(token.value))
                    if self.cached_comment:
                        self.section_in_process.hcomment = self.cached_comment
                        self.cached_comment = ""
                    self.state = State.EXPECT_ENTRY
                    continue

                self.expect(token, TOKEN_TYPES.IDENTIFIER)
                self.entry_in_process = None
                self.entry_in_process = self.eds.add_entry(self.section_in_process.keyword, token.value, token.line)
                if self.entry_in_process is None:
                    raise Exception("Unable to create entry: {}".format(token.value))
                if self.cached_comment:
                    self.entry_in_process.hcomment = self.cached_comment
                    self.cached_comment = ""
                # Expecting at least one field.
                self.expect(self.lexer.get_token(), TOKEN_TYPES.OPERATOR, SYMBOLS.ASSIGNMENT)
                self.state = State.EXPECT_FIELD
                continue

            raise Exception(__name__ + ':> Invalid Parser state! {}'.format(self.state))

        return self.eds

    def add_comment(self, comment, line_number):
        if self.section_in_process is None:
            self.eds.hcomment += comment.strip() + '\n'
        elif self.field_in_process:
            if line_number == self.field_in_process.line_number:
                self.field_in_process.fcomment += comment.strip() + '\n'
            elif line_number > self.field_in_process.line_number:
                self.cached_comment += comment.strip() + '\n'
        elif self.entry_in_process:
            if line_number == self.entry_in_process.line_number:
                self.entry_in_process.fcomment += comment.strip() + '\n'
            elif line_number > self.entry_in_process.line_number:
                self.cached_comment += comment.strip() + '\n'
        elif self.section_in_process:
            if line_number == self.section_in_process.line_number:
                self.section_in_process.fcomment += comment.strip() + '\n'
            elif line_number > self.section_in_process.line_number:
                self.cached_comment += comment.strip() + '\n'
        else:
            assert False

    def on_EOF(self):
        # The rest of cached comments belong to no elements
        self.eds.fcomment = self.cached_comment
        self.cached_comment = ""

    def expect(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is None or token.value == expected_value:
                return

        if expected_value:
            raise Exception("Unexpected token! Expected: (\"{}\": {}) but found: {}".format(
                            TOKEN_TYPES.stringify(expected_type), expected_value, token))
        raise Exception("Unexpected token! Expected: (\"{}\") but found: {}".format(
                        TOKEN_TYPES.stringify(expected_type), token))

    def match(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is not None:
                if token.value != expected_value:
                    return False
            return True
        return False

class CIP_EDS():
    def __new__(cls, eds_data):
        if isinstance(eds_data, bytes):
            eds_data = eds_data.decode("ascii")
        eds = Parser(eds_data).parse().validate()
        eds.validate()
        return eds
