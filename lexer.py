
from cip_eds_types import *
import logging
logging.basicConfig(level=logging.WARNING,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
    
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

class SYMBOLS(EDS_Types.ENUMS):
    ASSIGNMENT      = '='
    COMMA           = ','
    SEMICOLON       = ';'
    COLON           = ':'
    MINUS           = '-'
    UNDERLINE       = '_'
    PLUS            = '+'
    POINT           = '.'
    BACKSLASH       = '\\'
    QUOTATION       = '\"'
    TAB             = '\t'
    DOLLAR          = '$'
    OPENING_BRACKET = '['
    CLOSING_BRACKET = ']'
    OPENING_BRACE   = '{'
    CLOSING_BRACE   = '}'
    AMPERSAND       = '&'
    SPACE           = ' '
    EOL             = '\n'
    EOF             = None
    OPERATORS       = [ASSIGNMENT]
    SEPARATORS      = [COMMA, SEMICOLON]

SECTION_NAME_VALID_SYMBOLES = "-.\\_/"

class token():
    def __init__(self, type=None, valueNone, cursor=None):
        self.type   = type
        self.value  = value
        self.cursor = cursor

    def __str__(self):
        return '[Ln: {}, Col: {}, Pos: {}] {} \"{}\"'.format(
            str(self.cursor.line).rjust(4),
            str(self.cursor.col).rjust(3),
            str(self.cursor.offset).rjust(5),
            TOKEN_TYPE.stringify(self.type).ljust(11),
            self.value)

class cursor():
    self.offset = 0
    self.column = 0
    self.line = 0

class lexer():
    def __init__(self, eds_data):
        self.eds_data = eds_data.encode("ascii")
        slef.eds_length
        self.cursor = cursor()

    def next_token(self):
        token = self.get_token()
        self.prevtoken = self.token
        self.token = token
        logger.debug('token: {}'.format(token or 'EOF'))
        return token

    def get_char(self):
        assert self.cursor.offset <= self.eds_length

        # EOF
        if self.cursor.offset == self.eds_length:
            return TOKEN_TYPE.EOF

        ch = self.eds_data[self.cursor.offset]
        self.cursor.offset += 1
        self.col += 1
        if char == SYMBOLS.EOL:
            self.cursor.line += 1
            self.cursor.col = 0
        return ch

    def look_ahead(self, offset = 1):
        if self.cursor.offset + offset < self.eds_length:
            return self.eds_data[self.cursor.offset + offset]
        return SYMBOLS.EOL


    def lookbehind(self, offset = 1):
        if self.cursor.offset - offset >= 0:
            return self.eds_data[self.offset - offset]
        return None

    def get_token(self):

        token = None

        while True:
            ch = self.get_char()

            if token is None:

                if ch is SYMBOLS.EOF:
                    return token(TOKEN_TYPE.EOF, cursor=self.cursor)

                if ch.isspace():
                    # Ignoring space characters including: space, tab, carriage return
                    continue

                if ch == SYMBOLS.DOLLAR:
                    token = token(TOKEN_TYPE.COMMENT, '', cursor)
                    next = self.look_ahead()
                    if next != SYMBOLS.EOL and next != SYMBOLS.EOF:
                        token.cursor.offset += 1
                        token.cursor.column += 1
                    continue

                if ch == SYMBOLS.OPENING_BRACKET:
                    token = token(TOKEN_TYPE.SECTION, '', self.cursor)
                    next = self.look_ahead()
                    if next != SYMBOLS.EOL and next != SYMBOLS.EOF and next != SYMBOLS.CLOSING_BRACKET:
                        token.cursor.offset += 1
                        token.cursor.column += 1
                    continue

                if ch == SYMBOLS.OPENING_BRACE:
                    token = token(TOKEN_TYPE.DATASET, ch, self.cursor)
                    if next != SYMBOLS.EOL and next != SYMBOLS.EOF and next != SYMBOLS.CLOSING_BRACE:
                        token.cursor.offset += 1
                        token.cursor.column += 1
                    continue

                if ch == SYMBOLS.POINT or ch == SYMBOLS.MINUS or ch == SYMBOLS.PLUS  or ch.isdigit():
                    token = token(TOKEN_TYPE.NUMBER, ch, self.cursor)
                    if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                        return token
                    continue

                if ch.isalpha():
                    token = token(TOKEN_TYPE.IDENTIFIER, ch, self.cursor)
                    if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                        return token
                    continue

                if ch == SYMBOLS.QUOTATION:
                    token = token(TOKEN_TYPE.STRING, '', self.cursor)
                    continue

                if ch in SYMBOLS.OPERATORS:
                    return token(TOKEN_TYPE.OPERATOR, ch, self.cursor)

                if ch in SYMBOLS.SEPARATORS:
                    return token(TOKEN_TYPE.SEPARATOR, ch, self.cursor)

            if token.type == TOKEN_TYPE.COMMENT:
                if ch == SYMBOLS.EOL or ch == SYMBOLS.EOF:
                    return token
                token.value += ch
                continue

            if token.type is TOKEN_TYPE.SECTION:
                if ch == SYMBOLS.EOL:
                    raise Exception(".lexer:> Unexpected end of line during processing of section data at offset:{}".format(cursor.offset))
                if ch == SYMBOLS.EOF:
                    raise Exception(".lexer:> Unexpected end of file during processing of section data at offset:{}".format(cursor.offset))
                if ch == SYMBOLS.CLOSING_BRACKET:
                    return token

                # filtering invalid symbols in section name
                if (not ch.isspace() and not ch.isalpha() and not ch.isdigit()
                    and (ch not in SECTION_NAME_VALID_SYMBOLES)):

                    raise Exception( __name__ + ".lexer:> Invalid section identifier!"
                                   + " Unexpected char sequence "
                                   + "@[idx: {}] [ln: {}] [col: {}]"
                                   .format(self.cursor.offset, self.cursor.line, self.cursor.col))

                # unexpected symbols at the beginning or at the end of the section identifier
                if ((token.value == '' or self.look_ahead() == ']') and
                    (not ch.isalpha() and not ch.isdigit())):
                    raise Exception( __name__ + ".lexer:> Invalid section identifier!"
                        + " Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]".format(self.cursor.offset, self.cursor.line, self.cursor.col))

                # Sequential spaces
                if ch == ' ' and self.look_ahead().isspace():
                    raise Exception( __name__ + ".lexer:> Invalid section identifier! Sequential spaces are not allowed."
                        + " Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]".format(self.cursor.offset, self.cursor.line, self.cursor.col))

                if ch == SYMBOLS.EOF or ch == SYMBOLS.EOL:
                    raise Exception( __name__ + '.lexer:> Invalid section identifier!'
                        + ' Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]'.format(self.cursor.offset, self.cursor.line, self.cursor.col))

                token.value += ch
                continue

            if token.type is TOKEN_TYPE.NUMBER:
                if ch.isspace():
                    return token
                # Switching the token type to other types
                if   ch is SYMBOLS.COLON:     token.type = TOKEN_TYPE.TIME
                elif ch is SYMBOLS.MINUS:     token.type = TOKEN_TYPE.DATE
                elif ch is SYMBOLS.UNDERLINE: token.type = TOKEN_TYPE.IDENTIFIER

                token.value += ch
                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    return token
                continue

            if token.type is TOKEN_TYPE.IDENTIFIER:
                if ch.isspace():
                    return token

                token.value += ch
                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    return token
                continue

            if token.type is TOKEN_TYPE.STRING:
                if ch == SYMBOLS.QUOTATION and self.lookbehind() != SYMBOLS.BACKSLASH:
                    return token

                if ch == SYMBOLS.EOF or ch == SYMBOLS.EOL:
                    raise Exception( __name__ + '.lexer:> Invalid string value!'
                        + ' Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]'.format(self.cursor.offset, self.cursor.line, self.cursor.col))

                token.value += ch
                continue

            if token.type is TOKEN_TYPE.DATASET:
                if self.look_ahead() == SYMBOLS.SEMICOLON:
                    return token

                token.value += ch
                if ch == SYMBOLS.CLOSINGBRACE:
                    return token
                continue

            if token.type is TOKEN_TYPE.TIME:
                if ch.isspace():
                    return token

                if not ch.isdigit() and ch is not SYMBOLS.COLON:
                    raise Exception( __name__ + '.lexer:> Invalid TIME value!'
                        + ' Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]'.format(self.cursor.offset, self.cursor.line, self.cursor.col))
                token.value += ch

                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    return token
                continue

            if token.type is TOKEN_TYPE.DATE:
                if ch.isspace():
                    return token

                if not ch.isdigit() and ch is not SYMBOLS.MINUS:
                    raise Exception( __name__ + '.lexer:> Invalid DATE value!'
                        + ' Unexpected char sequence @[idx: {}] [ln: {}] [col: {}]'.format(self.cursor.offset, self.cursor.line, self.cursor.col))
                token.value += ch

                if self.look_ahead() in SYMBOLS.OPERATORS or self.look_ahead() in SYMBOLS.SEPARATORS:
                    return token
                continue
