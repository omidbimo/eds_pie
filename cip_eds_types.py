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

from collections import namedtuple
from calendar    import monthrange
from string      import digits
from datetime    import datetime, timedelta
import inspect

from collections import namedtuple
RANGE = namedtuple('RANGE', 'min max')

import logging
logging.basicConfig(level=logging.WARNING,
    format='%(asctime)s - %(name)s.%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

class ENUMS(object):

    def stringify(self, enum):
        for attr in vars(self.__class__):
            if isinstance(self.__class__.__dict__[attr], int) and self.__class__.__dict__[attr] == enum: return '{}'.format(attr)
        for base in self.__class__.__bases__:
            for attr in vars(base):
                if isinstance(base.__dict__[attr], int) and base.__dict__[attr] == enum: return '{}'.format(attr)
        return ''

    @classmethod
    def stringify(cls, enum):
        for attr in vars(cls):
            if isinstance(cls.__dict__[attr], int) and cls.__dict__[attr] == enum: return '{}'.format(attr)
        for base in cls.__bases__:
            for attr in vars(base):
                if isinstance(base.__dict__[attr], int) and base.__dict__[attr] == enum: return '{}'.format(attr)
        return ''

class CIP_STD_TYPES(ENUMS):
    CIP_EDS_UTIME         = 0xC0
    CIP_EDS_BOOL          = 0xC1
    CIP_EDS_SINT          = 0xC2
    CIP_EDS_INT           = 0xC3
    CIP_EDS_DINT          = 0xC4
    CIP_EDS_LINT          = 0xC5
    CIP_EDS_USINT         = 0xC6
    CIP_EDS_UINT          = 0xC7
    CIP_EDS_UDINT         = 0xC8
    CIP_EDS_ULINT         = 0xC9
    CIP_EDS_REAL          = 0xCA
    CIP_EDS_LREAL         = 0xCB
    CIP_EDS_STIME         = 0xCC
    CIP_EDS_DATE          = 0xCD
    CIP_EDS_TIME_OF_DAY   = 0xCE
    CIP_EDS_DATE_AND_TIME = 0xCF
    CIP_EDS_STRING        = 0xD0
    CIP_EDS_BYTE          = 0xD1
    CIP_EDS_WORD          = 0xD2
    CIP_EDS_DWORD         = 0xD3
    CIP_EDS_LWORD         = 0xD4
    CIP_EDS_STRING2       = 0xD5
    CIP_EDS_FTIME         = 0xD6
    CIP_EDS_LTIME         = 0xD7
    CIP_EDS_ITIME         = 0xD8
    CIP_EDS_STRINGN       = 0xD9
    CIP_EDS_SHORT_STRING  = 0xDA
    CIP_EDS_TIME          = 0xDB
    CIP_EDS_EPATH         = 0xDC
    CIP_EDS_ENGUNIT       = 0xDD
    CIP_EDS_STRINGI       = 0xDE
    CIP_EDS_NTIME         = 0xDF

def getnumber(data):
    '''
    Converts an input of string type into its numeric representaion.
    '''
    if data is None:  return None
    if data == '':    return None
    if isint(data):   return int(data)
    if isfloat(data): return float(data)
    if ishex(data):   return int(data, 16)
    if isbin(data):   return int(data, 2)
    return None


def isnumber(data):
    '''
    Checks if a string represents a numeric value.
    '''
    if data is None:  return False
    if data == '':    return False
    if isint(data):   return True
    if isfloat(data): return True
    if ishex(data):   return True
    if isbin(data):   return True
    return False


def isint(data):
    '''
    Checks if a string represents a decimal coded numeric value.
    '''
    if data is None: return False
    try:
        int(data)
    except ValueError:
        return False
    return True


def isfloat(data):
    '''
    Checks if a string represents a floating point numeric value.
    '''
    if data is None: return False
    try:
        float(data)
    except ValueError:
        return False
    return True


def ishex(data):
    '''
    Checks if a string represents a hexadecimal coded numeric value.
    '''
    if data is None: return False
    try:
        int(data, 16)
    except ValueError:
        return False
    return True


def isbin(data):
    '''
    Checks if a string represents a binary coded numeric value.
    '''
    if data is None: return False
    try:
        int(data, 2)
    except ValueError:
        return False
    return True


def isdate(data):
    if data is None:
        return False

    try:
        m, d, y = data.split('-')

        if len(m) != 2 or len(d) != 2 or int(m) < 1 or int(m) > 12:
            logger.error('Invalid EDS_DATE month length or month value!')
            return False

        if len(y) == 4:
            if int(y) < 1994:
                logger.error('Invalid EDS_DATE yyyy value!')
                return False
        elif len(y) == 2:
            if int(y) < 94:
                logger.error('Invalid EDS_DATE yy value!')
                return False
        else:
            logger.error('Invalid EDS_DATE year format!')
            return False

        if int(d) < 1 or (int(d) > (monthrange(int(y), int(m))[1]) ):
            logger.error('Invalid EDS_DATE day value!')
            return False
    except:
        return False
    return True


def getdate():
    return datetime.strftime(datetime.now(), "%m-%d-%Y")

def cast2date(val):
    '''
    Converts a 16-bit value to a valid DATE string between 01.01.1972 and 06.06.2151
    '''
    return datetime.strftime(datetime.strptime('01-01-1972', "%m-%d-%Y") + timedelta(days=val), "%m-%d-%Y")

def istime(data):
    if data is None: return False
    data = data.split(':')
    if len(data) != 3:
        return False
    hh = data[0]
    mm = data[1]
    ss = data[2]

    if len(mm) != 2 or len(hh) != 2 or len(ss) != 2:
        return False

    if int(hh) > 24 or int(hh) < 0:
        return False
    if int(mm) > 60 or int(mm) < 0:
        return False
    if int(ss) > 60 or int(ss) < 0:
        return False
    return True


def gettime():
    hh = format(datetime.now().hour, '02')
    mm = format(datetime.now().minute, '02')
    ss = format(datetime.now().second, '02')
    return "%s:%s:%s" %(hh, mm, ss)



class CIP_EDS_BASE_TYPE(object):
    _typeid = None
    _range  = []

    def __init__(self, value, *args):
        self._value = value
        #sele._range = *args

    @property
    def range(self):
        return self._range

    @property
    def value(self):
        return self._value

    @classmethod
    def validate(value, *args):
        raise(NotImplementedError)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.__value)

    def __str__(self):
        return '{}'.format(self._value)

class CIP_EDS_BASE_INT(CIP_EDS_BASE_TYPE):

    def __init__(self, value, *args):
        self._value = value
        #sele._range = *args

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls._range.min and value <= cls._range.max

    def __format__(self, format_spec):
            return format(self._value, format_spec)

    def __hex__(self):
        return '0x{:X}'.format(self._value)

    def __eq__( self , other):
        return self._value == other

    def __ne__( self , other):
        return self._value != other

    def __lt__( self , other):
        return self._value < other

    def __gt__( self , other):
        return self._value > other

    def __le__( self , other):
        return self._value <= other

    def __ge__( self , other):
        return self._value <= other

    def __add__(self, other):
        return self._value + other

    def __sub__(self, other):
        return self._value - other

    def __mul__(self, other):
        return self._value * other

    def __truediv__(self, other):
        return self._value / other

    def __floordiv__(self, other):
        return self._value // other

    def __int__(self):
        return self._value

    def __index__(self):
        return self.__int__()

    def __len__(self):
        return self._size


class BOOL(CIP_EDS_BASE_TYPE):
    _typeid = CIP_STD_TYPES.CIP_EDS_BOOL
    _range = RANGE(0, 1)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(BOOL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(BOOL, self).__init__(value)

    def __str__(self):
        return str(self._value != 0)


class USINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_USINT
    _range = RANGE(0, 255)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(USINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(USINT, self).__init__(value)


class SINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_USINT
    _range = RANGE(0, 255)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(SINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(SINT, self).__init__(value)


class UINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_UINT
    _range = RANGE(0, 65535)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(UINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(UINT, self).__init__(value)


class INT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_INT
    _range = RANGE(-32768, 32767)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(INT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(INT, self).__init__(value)


class UDINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_UDINT
    _range = RANGE(0, 4294967295)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(UDINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(UDINT, self).__init__(value)


class DINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_DINT
    _range = RANGE(-2147483648, 2147483647)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(DINT, self).__init__(value)



class ULINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_ULINT
    _range = RANGE(0, 18446744073709551615)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(ULINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(ULINT, self).__init__(value)


class LINT(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_LINT
    _range = RANGE(-9223372036854775808, 9223372036854775807)
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(LINT, self).__init__(value)


class BYTE(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_BYTE
    _range = RANGE(0, 255)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(BYTE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(BYTE, self).__init__(value)


class WORD(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_WORD
    _range = RANGE(0, 65535)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(WORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(WORD, self).__init__(value)


class DWORD(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_DWORD
    _range = RANGE(0, 4294967295)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(DWORD, self).__init__(value)


class LWORD(CIP_EDS_BASE_INT):
    _typeid = CIP_STD_TYPES.CIP_EDS_LWORD
    _range = RANGE(0, 18446744073709551615)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(LWORD, self).__init__(value)

class REAL(CIP_EDS_BASE_INT): # TODO: improve validate
    _typeid = CIP_STD_TYPES.CIP_EDS_REAL
    _range = RANGE(-16777216.0, 16777216.0)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(REAL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(REAL, self).__init__(value)

class LREAL(CIP_EDS_BASE_INT): # TODO: improve validate
    _typeid = CIP_STD_TYPES.CIP_EDS_LREAL
    _range = RANGE(-9007199254740992.0, 9007199254740992.0)

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LREAL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(LREAL, self).__init__(value)


class STIME(CIP_EDS_BASE_TYPE): #  dummy type! TODO
    _typeid = CIP_STD_TYPES.CIP_EDS_STIME

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STIME, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(STIME, self).__init__(value)

class STRING(CIP_EDS_BASE_TYPE):
    _typeid = CIP_STD_TYPES.CIP_EDS_STRING

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STRING, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(STRING, self).__init__(value)

    @classmethod
    def validate(cls, value, *args):
        return isinstance(value, str)

    def __str__(self):
        return '\n'.join('\"{}\"'.format(self.value[offset : offset + 60])
            for offset in range(0, len(self.value), 60))


class STRINGI(CIP_EDS_BASE_TYPE):
    _typeid = CIP_STD_TYPES.CIP_EDS_STRINGI

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STRINGI, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        self._range = ['mm-dd-yyyy']
        super(STRINGI, self).__init__(value)

    @classmethod
    def validate(cls, value, *args):
        # TODO
        pass

    def __str__(self):
        return 'STRINGI...' # TODO


class DATE(CIP_EDS_BASE_TYPE):
    # EDS_DATE mm.dd.yyyy from 1994 to 9999
    _range = ['mm.dd.yyyy', 'mm.dd.yy']

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DATE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(DATE, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        return isdate(value)


class TIME(CIP_EDS_BASE_TYPE):
    _typeid = CIP_STD_TYPES.CIP_EDS_TIME

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(TIME, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(TIME, self).__init__(value)

    @property
    def range(self):
        return ['HH:MM:SS'] # TODO

    @staticmethod
    def validate(value, *args):
        try:
            data = value.split(':')
        except:
            return False

        if len(data) != 3:
            return False
        hh = data[0]
        mm = data[1]
        ss = data[2]

        # Tolerate no leading zeros
        #if len(mm) < 2 or len(hh) < 2 or len(ss) < 2:
        #    return False

        if ((len(hh) < 1 or len(hh) > 2) or
            (len(mm) < 1 or len(mm) > 2) or
            (len(ss) < 1 or len(ss) > 2)):
            return False

        if int(hh) > 24 or int(hh) < 0:
            return False
        if int(mm) > 60 or int(mm) < 0:
            return False
        if int(ss) > 60 or int(ss) < 0:
            return False
        return True


class EPATH(CIP_EDS_BASE_TYPE):
    _typeid = CIP_STD_TYPES.CIP_EDS_EPATH

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EPATH, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(EPATH, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        try:
            elements = value.split()
        except:
            return False
        for element in elements:
            if len(element) < 2:
                return False
            if not isnumber(element):
                if (element[0] == '[' and element[-1] == ']'): #TODO: accept references without brackets
                    continue
                return False
            elif not ishex(element):
                return False
        return True

    def __str__(self):
        return "\"{}\"".format(self.value)


class REVISION(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(REVISION, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(REVISION, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        try:
            elements = value.split('.')
        except:
            return False

        if len(elements) != 2:
            return False
        for element in elements:
            if not isnumber(element):
                return False
        return True


class ETH_MAC_ADDR(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(ETH_MAC_ADDR, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__, cls._typeid))

    def __init__(self, value, *args):
        super(ETH_MAC_ADDR, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        macaddr = value.rstrip('}').lstrip('{').strip().replace(':', '-').replace('.', '-').split('-')
        if len(macaddr) != 6:
            return False
        for field in macaddr:
            if USINT.validate(field) == False:
                return False
        return True


class REF(CIP_EDS_BASE_TYPE):
    def __new__(cls, value, *args):
        if cls.validate(value, *args):
            return super(REF, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self._range = args[0] # TODO
        super(REF, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        if not isinstance(value, str):
            return False
        for keyword in args[0]:
            keyword = keyword.rstrip('N').lower()
            if value[:len(keyword)].lower() == keyword:
                return True
        return False


class KEYWORD(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value, *args):
            return super(KEYWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} ".format(arg[0])
                                     + "for <{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self._range = args[0]
        super(KEYWORD, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        for keyword in args[0]:
            if value.lower() == keyword.lower():
                return True
        return False


class DATATYPE_REF(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DATATYPE_REF, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        super(DATATYPE_REF, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        return True # TODO


class EDS_SERVICE(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EDS_SERVICE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        super(EDS_SERVICE, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        return True # TODO


class EMPTY(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EMPTY, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        super(EMPTY, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        if args is None or value == '':
            return True
        return False

    def __str__(self):
        return ''


class VENDOR_SPECIFIC(CIP_EDS_BASE_TYPE):

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(VENDOR_SPECIFIC, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        super(VENDOR_SPECIFIC, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        if isinstance(value, str) and value != '': #TODO
            if value[0].isdigit():
                return True
        return False


class UNDEFINED(CIP_EDS_BASE_TYPE):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(UNDEFINED, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__value = value
        super(UNDEFINED, self).__init__(value)

    @staticmethod
    def validate(value, *args):
        return True
