
from cip_eds_types import *
import cip_eds_types as EDS_Types

import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')

'''
    EDS grammatics:
    ---------------

    OPERATOR
        {=}

    SEPARATOR
        {,;-:}

    LF
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
        $ {ASCII symbols} LF

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



SECTION_NAME_VALID_SYMBOLES = "-.\\_/"

class Token():
    def __init__(self, type, value, cursor):
        self.type   = type
        self.value  = value

        self.offset = cursor.offset
        self.col    = cursor.col
        self.line   = cursor.line

    def __str__(self):
        return '[Pos: {}, Ln: {}, Col: {}] {} \"{}\"'.format(
            str(self.offset).rjust(5),
            str(self.line).rjust(4),
            str(self.col).rjust(3),
            TOKEN_TYPE.stringify(self.type).ljust(11),
            self.value)

class Cursor():
    def __init__(self):
        self.offset = -1
        self.col = 0
        self.line = 1

class Lexer():
    def __init__(self, eds_data):
        self.eds_data = eds_data
        self.eds_length = len(self.eds_data)
        self.cursor = Cursor()

    def get_char(self):
        assert self.cursor.offset + 1 <= self.eds_length

        self.cursor.offset += 1

        if self.cursor.offset  < self.eds_length:
            ch = chr(self.eds_data[self.cursor.offset])

            self.cursor.col += 1
            if ch == SYMBOLS.LF:
                self.cursor.line += 1
                self.cursor.col = 0
        else: # EOF
            ch = SYMBOLS.EOF

        return ch

    def look_ahead(self, offset = 1):
        if self.cursor.offset + offset < self.eds_length:
            return chr(self.eds_data[self.cursor.offset + offset])
        return SYMBOLS.LF

    def lookbehind(self, offset = 1):
        if self.cursor.offset - offset >= 0:
            return self.eds_data[self.cursor.offset - offset]
        return None

    def get_token(self):

        token = None

        while True:
            ch = self.get_char()

            if token is None:
                if ch is SYMBOLS.EOF:
                    token = Token(TOKEN_TYPE.EOF, '', cursor=self.cursor)
                    break

                if ch.isspace():
                    # Ignoring space characters including: space, tab, carriage return
                    continue

                if ch == SYMBOLS.DOLLAR:
                    token = Token(TOKEN_TYPE.COMMENT, '', self.cursor)
                    next = self.look_ahead()
                    if next == SYMBOLS.LF or next == SYMBOLS.EOF:
                        break

                    token.offset += 1
                    token.col += 1
                    continue

                if ch == SYMBOLS.OPENING_BRACKET:
                    token = Token(TOKEN_TYPE.SECTION, '', self.cursor)
                    continue

                if ch == SYMBOLS.OPENING_BRACE:
                    token = Token(TOKEN_TYPE.DATASET, ch, self.cursor)
                    continue

                if ch == SYMBOLS.POINT or ch == SYMBOLS.MINUS or ch == SYMBOLS.PLUS  or ch.isdigit():
                    token = Token(TOKEN_TYPE.NUMBER, ch, self.cursor)
                    next = self.look_ahead()
                    if next in SYMBOLS.OPERATORS or next in SYMBOLS.SEPARATORS:
                        break
                    continue

                if ch.isalpha():
                    token = Token(TOKEN_TYPE.IDENTIFIER, ch, self.cursor)
                    next = self.look_ahead()
                    if next in SYMBOLS.OPERATORS or next in SYMBOLS.SEPARATORS:
                        break
                    continue

                if ch == SYMBOLS.QUOTATION:
                    token = Token(TOKEN_TYPE.STRING, '', self.cursor)
                    continue

                if ch in SYMBOLS.OPERATORS:
                    token = Token(TOKEN_TYPE.OPERATOR, ch, self.cursor)
                    break

                if ch in SYMBOLS.SEPARATORS:
                    token = Token(TOKEN_TYPE.SEPARATOR, ch, self.cursor)
                    break

            if token.type == TOKEN_TYPE.COMMENT:
                if ch == SYMBOLS.LF or ch == SYMBOLS.CR or ch == SYMBOLS.EOF:
                    break
                token.value += ch
                continue

            if token.type is TOKEN_TYPE.SECTION:
                if ch == SYMBOLS.LF:
                    raise Exception(".lexer:> Unexpected end of line during processing of section data at offset:{}".format(cursor.offset))
                if ch == SYMBOLS.EOF:
                    raise Exception(".lexer:> Unexpected end of file during processing of section data at offset:{}".format(cursor.offset))
                if ch == SYMBOLS.CLOSING_BRACKET:
                    break

                # filtering invalid symbols in section name
                if (not ch.isspace() and not ch.isalpha() and not ch.isdigit()
                    and (ch not in SECTION_NAME_VALID_SYMBOLES)):

                    raise Exception( __name__ + ".lexer:> Invalid section identifier! Unexpected char sequence: {}".format(token))

                # unexpected symbols at the beginning or at the end of the section identifier
                if ((token.value == '' or self.look_ahead() == ']') and
                    (not ch.isalpha() and not ch.isdigit())):
                    raise Exception( __name__ + ".lexer:> Invalid section identifier! Unexpected char sequence: {}".format(token))

                # Sequential spaces
                if ch == ' ' and self.look_ahead().isspace():
                    raise Exception( __name__ + ".lexer:> Invalid section identifier! Sequential spaces are not allowed."
                        + " Unexpected char sequence: {}".format(token))

                if ch == SYMBOLS.EOF or ch == SYMBOLS.LF:
                    raise Exception( __name__ + ".lexer:> Invalid section identifier! Unexpected char sequence: {}".format(token))

                token.value += ch
                continue

            if token.type is TOKEN_TYPE.NUMBER:
                if ch.isspace():
                    break
                # Switching the token type to other types
                if   ch is SYMBOLS.COLON:     token.type = TOKEN_TYPE.TIME
                elif ch is SYMBOLS.MINUS:     token.type = TOKEN_TYPE.DATE
                elif ch is SYMBOLS.UNDERLINE: token.type = TOKEN_TYPE.IDENTIFIER

                token.value += ch
                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    break
                continue

            if token.type is TOKEN_TYPE.IDENTIFIER:
                if ch == SYMBOLS.EOF or ch == SYMBOLS.LF:
                    break

                if ch.isspace():
                    break

                token.value += ch
                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    break
                continue

            if token.type is TOKEN_TYPE.STRING:
                if ch == SYMBOLS.QUOTATION and self.lookbehind() != SYMBOLS.BACKSLASH:
                    break

                if ch == SYMBOLS.EOF or ch == SYMBOLS.LF:
                    raise Exception( __name__ + ".lexer:> Invalid string value! Unexpected char sequence: {}".format(token))

                token.value += ch
                continue

            if token.type is TOKEN_TYPE.DATASET:
                if self.look_ahead() == SYMBOLS.SEMICOLON:
                    break

                token.value += ch
                if ch == SYMBOLS.CLOSINGBRACE:
                    break
                continue

            if token.type is TOKEN_TYPE.TIME:
                if ch.isspace():
                    break

                if not ch.isdigit() and ch is not SYMBOLS.COLON:
                    raise Exception( __name__ + '.lexer:> Invalid TIME value! {}'.format(token))
                token.value += ch

                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    break
                continue

            if token.type is TOKEN_TYPE.DATE:
                if ch.isspace():
                    break

                if not ch.isdigit() and ch is not SYMBOLS.MINUS:
                    raise Exception( __name__ + '.lexer:> Invalid DATE value! {}'.format(token))

                token.value += ch

                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    break
                continue

        logger.debug('token: {}'.format(token or 'EOF'))
        return token