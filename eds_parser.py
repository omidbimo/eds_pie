
from cip_eds_types import *
from eds_lexer import Lexer
from eds import EDS, EDS_Section, EDS_Entry, EDS_Field

import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')

class State(ENUMS):
    EXPECT_SECTION = 0
    EXPECT_ENTRY   = 1
    EXPECT_SECTION_OR_ENTRY = 2
    EXPECT_FIELD   = 3

class Parser(object):
    def __init__(self, eds_data, showprogress = False):
        self.src_text = eds_data
        self.src_len  = len(eds_data)
        self.lexer = Lexer(eds_data)
        self.state = State.EXPECT_SECTION
        self.eds = EDS()
        self.section_in_process = None
        self.entry_in_process = None
        self.field_in_process = None
        self.hcomment = ""
        self.fcomment = ""

        # these two are only to keep track of element comments. A comment on the
        # same line of a field is the field's footer comment. Otherwise it's the
        # entry's header comment.
        """
        self.token     = None
        self.prevtoken = None
        self.comment   = ''

        self.section_in_process = None
        self.entry_in_process = None
        self.last_created_element = None
        self.state = State.EXPECT_SECTION

        self.showprogress = showprogress
        self.progress = 0.0
        self.progress_step = float(self.src_len) / 100.0
        """
    def parse(self):

        while True:
            token = self.lexer.get_token()

            if token.type is TOKEN_TYPE.EOF:
                break

            if self.match(token, TOKEN_TYPE.COMMENT):
                self.cashe_comment(token)
                continue

            if self.state is State.EXPECT_SECTION:
                if self.match(token, TOKEN_TYPE.SECTION):
                    self.add_section(token)
                    continue
                else:
                    raise Exception("Invalid token! Expected a Section token but got: {}".format(token))

            if self.state is State.EXPECT_ENTRY:
                if self.match(token, TOKEN_TYPE.IDENTIFIER):
                    self.add_entry(token)
                    # Expecting at least one field.
                    token = self.lexer.get_token()
                    self.expect(token, TOKEN_TYPE.OPERATOR, SYMBOLS.ASSIGNMENT)
                    self.state = State.EXPECT_FIELD
                    continue
                else:
                    raise Exception("Invalid token! Expected an Entry token but got: {}".format(token))

            if self.state is State.EXPECT_FIELD:
                self.add_field(token)
                token = self.lexer.get_token()
                if self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.SEMICOLON):
                    # End of Entry. The next token might be an entry or a new section
                    self.state = State.EXPECT_SECTION_OR_ENTRY
                    continue
                self.expect(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.COMMA)
                continue

            if self.state is State.EXPECT_SECTION_OR_ENTRY:
                if self.match(token, TOKEN_TYPE.SECTION):
                    self.add_section(token)
                elif self.match(token, TOKEN_TYPE.IDENTIFIER):
                    self.add_entry(token)
                    # Expecting at least one field.
                    token = self.lexer.get_token()
                    self.expect(token, TOKEN_TYPE.OPERATOR, SYMBOLS.ASSIGNMENT)
                    self.state = State.EXPECT_FIELD
                else:
                    raise Exception("Invalid token! Expected a Section or an Entry token but got: {}".format(token))
                continue

            raise Exception(__name__ + ':> Invalid Parser state! {}'.format(self.state))

        return self.eds

    def add_section(self, token):
        self.section_in_process = self.eds.add_section(token.value)

        if self.section_in_process is None:
            raise Exception("Unable to create section: {}".format(token.value))

        # If there are cached comments then they are header comments of the new element
        self.section_in_process.hcomment = self.hcomment
        self.last_created_element = self.section_in_process
        self.hcomment = ""

        # This is a new section. Expecting at least one entry.
        self.state = State.EXPECT_ENTRY

    def add_entry(self, token):
        self.entry_in_process = self.eds.add_entry(self.section_in_process.name, token.value)

        if self.entry_in_process is None:
            raise Exception("Unable to create entry: {}".format(token.value))

        # If there are cached comments then they are header comments of the new element
        self.entry_in_process.hcomment = self.hcomment
        self.last_created_element = self.entry_in_process
        self.hcomment = ""

    def add_field(self, token):
        field_value = ""
        field_type  = None

        field = self.eds.add_field(self.section_in_process.name, self.entry_in_process.name, token.value, token.type)
        if field is None:
            raise Exception("Unable to create field: {} of type: {}".format(token.value, token.type))
        return
        # It's possible that a field value contains multiple tokens. Fetch tokens
        # in a loop until reaching the end of the field. Concatenate the values
        # if possible(to support multi-line strings)
        while True:

            if token is TOKEN_TYPE.EOF:
                raise Exception("Unexpected token. Expected a field token but got EOF.")

            if (self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.COMMA) or
                self.match(token, TOKEN_TYPE.SEPARATOR, SYMBOLS.SEMICOLON)):
                field = self.eds.add_field(self.section_in_process.name, self.entry_in_process.name, field_value, field_type)

                if field is None:
                    raise Exception("Unable to create field: {} of type: {}".format(token.value, token.type))

                # If there are cached comments then they are header comments of the new element
                field.hcomment = self.hcomment
                self.last_created_element = field
                self.hcomment = ""
                field_value = ""
                field_type = None


                break

            elif (self.match(token, TOKEN_TYPE.IDENTIFIER)  or
                  self.match(token, TOKEN_TYPE.STRING)      or
                  self.match(token, TOKEN_TYPE.NUMBER)      or
                  self.match(token, TOKEN_TYPE.DATE)        or
                  self.match(token, TOKEN_TYPE.TIME)        or
                  self.match(token, TOKEN_TYPE.DATASET)):

                if field_value == '' and field_type is None:
                    field_value += token.value
                    field_type = token.type
                elif field_type == TOKEN_TYPE.STRING and self.match(token, TOKEN_TYPE.STRING):
                    # There are two strings literals in one field that must be Concatenated
                    field_value += token.value
                else:
                    # There are different types of tokens to be concatenated.
                    raise Exception("Concatenating these literals is not allowed."
                        + '({})<{}> + ({})<{}> @({})'.format(field_value, TOKEN_TYPE.stringify(field_type), token.value, TOKEN_TYPE.stringify(token.type), token))
            else:
                raise Exception("Unexpected token type. Expected a field value token but got: {}".format(token))



    def cashe_comment(self, token):
        if self.state is State.EXPECT_SECTION:
            self.hcomment += token.value.strip() + '\n'
            return

    def add_comment(self, token):
        if self.state is State.EXPECT_SECTION:
            self.eds.heading_comment += token.value.strip() + '\n'
            return
        # The footer comment only appears on the same line after the eds item
        # otherwise the comment is a header comment
        if self.prevtoken and self.prevtoken.line == token.line:
            # Footer comment
            self.last_created_element.fcomment = token.value.strip()
        else:
            # Caching the header comment for the next element.
            self.hcomment += token.value.strip() + '\n'

    def on_EOF(self):
        # The rest of cached comments belong to no elements
        self.eds.end_comment = self.fcomment
        self.fcomment = ""

    def expect(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is None or token.value == expected_value:
                return

        raise Exception("Unexpected token! Expected: (\"{}\": {}) but received: {}".format(
                    TOKEN_TYPE.stringify(exptokentype), exptokenval, self.token))

    def match(self, token, expected_type, expected_value=None):
        if token.type == expected_type:
            if expected_value is not None:
                if token.value != expected_value:
                    return False
            return True
        return False
