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
import datetime

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
    if data is None:  return False
    data = data.split(MINUS)
    if len(data) != 3:
        return False
    try:
        mm = data[0]
        dd = data[1]
        yyyy = data[2]

        if len(mm) != 2 or len(dd) != 2:
            return False

        if int(mm) < 1 or  int(mm) > 12:
            return False

        if len(yyyy) == 2:
            pass
        elif len(yyyy) == 4:
            if int(yyyy) < 1900 or int(yyyy) > 2048:
                return False
        else:
            return False
        if int(dd) < 1 or (int(dd) > (monthrange(int(yyyy), int(mm))[1]) ):
            return False
    except:
        return False
    return True


def getdate():
    mm = format(date.today().month, '02')
    dd = format(date.today().day, '02')
    yyyy = format(date.today().year, '04')
    return "%s-%s-%s" %(mm, dd, yyyy)


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





class EDS_DT(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def value(self):
        raise NotImplementedError

    @abstractproperty
    def range(self):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def validate(*args):
        raise NotImplementedError

class EDS_DataType(EDS_DT):
    def __init__(self, value):
        self.__value = value

    @property
    def value(self):
        return int(self.__value, 0)

    def __str__(self):
        return "{}".format(self.__value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.__value)

class CIP_DataType(EDS_DT):
    @abstractproperty
    def cip_typeid(self):
        raise NotImplementedError

    def __init__(self,value):
        self.__value = value

    @property
    def value(self):
        return getnumber(self.__value)

    def __str__(self):
        return "{}".format(self.__value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.__value)


class BOOL(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 1
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC1

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(BOOL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(BOOL, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        if value >= cls.__range[0] and value <= cls.__range[1]:
            return True
        return False


class USINT(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 255
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC6

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(USINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(USINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class UINT(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 65535
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC7

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(UINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(UINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class UDINT(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 4294967295
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC8

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(UDINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(UDINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class ULINT(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 18446744073709551615
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC9

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(ULINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(ULINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class SINT(CIP_DataType):
    TYPE_MIN = -128
    TYPE_MAX = 127
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC2

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(SINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(SINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class INT(CIP_DataType):
    TYPE_MIN = -32768
    TYPE_MAX = 32767
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC3

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(INT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(INT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class DINT(CIP_DataType):
    TYPE_MIN = -2147483648
    TYPE_MAX = 2147483647
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC4

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(DINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class LINT(CIP_DataType):
    TYPE_MIN = -9223372036854775808
    TYPE_MAX = 9223372036854775807
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xC5

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LINT, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(LINT, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class BYTE(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 255
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xD1

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(BYTE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(BYTE, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]


class WORD(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 65535
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xD2

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(WORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(WORD, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class DWORD(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 4294967295
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xD3

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(DWORD, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class LWORD(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 18446744073709551615
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xD4

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        super(LWORD, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        return value is not None and value >= cls.__range[0] and value <= cls.__range[1]

class REAL(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 18446744073709551615 #TODO
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xCA

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(REAL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        #self.__value = value
        super(REAL, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    #@property
    #def value(self):
    #    return self.__value

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        if value >= cls.__range[0] and value <= cls.__range[1]:
            return True
        return False


class LREAL(CIP_DataType):
    TYPE_MIN = 0
    TYPE_MAX = 18446744073709551615 #TODO
    __range = [TYPE_MIN, TYPE_MAX]
    cip_typeid = 0xCB

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(LREAL, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(LREAL, self).__init__(value)

    @property
    def range(self):
        return self.__class__.__range

    @property
    def value(self):
        return self.__value

    @classmethod
    def validate(cls, value, *args):
        value = getnumber(value)
        if value >= cls.__range[0] and value <= cls.__range[1]:
            return True
        return False


class STRING(CIP_DataType):
    cip_typeid = 0xD0

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STRING, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(STRING, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @classmethod
    def validate(cls, value, *args):
        if isinstance(value, str):
            return True
        return False

    def __str__(self):
        return '\n'.join('\"{}\"'.format(self.value[offset : offset + 60])
            for offset in range(0, len(self.value), 60))

class STRINGI(CIP_DataType):
    cip_typeid = 0xDE

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STRINGI, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(STRINGI, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @classmethod
    def validate(cls, value, *args):
        #TODO
        pass


class DATE(CIP_DataType):
    cip_typeid = 0xCD

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DATE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(DATE, self).__init__(value)

    @property
    def range(self):
        return ["mm.dd.yyyy"]

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        try:
            data = value.split('-')
        except:
            return False

        if len(data) != 3:
            return False

        mm = data[0]
        dd = data[1]
        yyyy = data[2]

        # Tolerate no leading zeros
        #if len(mm) != 2 or len(dd) != 2:
        #    return False

        # Tolerate short year form
        #if len(yyyy) < 4:
        #    return False

        if ((len(yyyy) < 1 or len(yyyy) > 4) or
            (len(mm) < 1 or len(mm) > 2) or
            (len(dd) < 1 or len(dd) > 2)):
            return False

        try:
            datetime.datetime(year = int(yyyy), month = int(mm), day = int(dd))
        except:
            return False
        return True



class TIME(CIP_DataType):
    cip_typeid = 0xD8

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(TIME, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(TIME, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

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


class STIME(CIP_DataType):
    cip_typeid = 0xCC

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(STIME, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(STIME, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        #TODO
        return True


class TIME_OF_DAY(CIP_DataType):
    cip_typeid = 0xCE

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(TIME_OF_DAY, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(TIME_OF_DAY, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        #TODO
        return True


class DATE_AND_TIME(CIP_DataType):
    cip_typeid = 0xCF

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DATE_AND_TIME, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(DATE_AND_TIME, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        #TODO
        return True


class EPATH(CIP_DataType):
    cip_typeid = 0xDC

    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EPATH, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{} (CIP typeID: 0x{:X})> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(EPATH, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

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
                if (element[0] == '[' and element[-1] == ']'):
                    continue
                return False
            elif not ishex(element):
                return False
        return True

    def __str__(self):
        return "\"{}\"".format(self.value)

class REVISION(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(REVISION, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(REVISION, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

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


class ETH_MAC_ADDR(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(ETH_MAC_ADDR, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__, cls.cip_typeid))

    def __init__(self, value, *args):
        self.__value = value
        super(ETH_MAC_ADDR, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        macaddr = value.rstrip('}').lstrip('{').strip().replace(':', '-').replace('.', '-').split('-')
        if len(macaddr) != 6:
            return False
        for field in macaddr:
            if USINT.validate(field) == False:
                return False
        return True


class REF(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value, *args):
            return super(REF, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__range = args[0]
        self.__value = value
        super(REF, self).__init__(value)

    @property
    def range(self):
        return self.__range

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        if not isinstance(value, str):
            return False
        for keyword in args[0]:
            keyword = keyword.rstrip('N').lower()
            if value[:len(keyword)].lower() == keyword:
                return True
        return False


class KEYWORD(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value, *args):
            return super(KEYWORD, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} ".format(arg[0])
                                     + "for <{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__range = args[0]
        self.__value = value
        super(KEYWORD, self).__init__(value)

    @property
    def range(self):
        return self.__range

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        for keyword in args[0]:
            if value.lower() == keyword.lower():
                return True
        return False


class DATATYPE_REF(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(DATATYPE_REF, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__value = value
        super(DATATYPE_REF, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        return True

class EDS_SERVICE(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EDS_SERVICE, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__value = value
        super(EDS_SERVICE, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        return True

class EMPTY(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(EMPTY, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__value = value
        super(EMPTY, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        if args is None or value == '':
            return True
        return False

    def __str__(self):
        return ""


class VENDOR_SPECIFIC(EDS_DataType):
    def __new__(cls, value, *args):
        if cls.validate(value):
            return super(VENDOR_SPECIFIC, cls).__new__(cls)
        else:
            raise Exception(__name__ + ":> Invalid value: {} for ".format(value)
                                     + "<{}> data type."
                                       .format(cls.__name__))

    def __init__(self, value, *args):
        self.__value = value
        super(VENDOR_SPECIFIC, self).__init__(value)

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        if isinstance(value, str) and value != '': #TODO
            if value[0].isdigit():
                return True
        return False


class UNDEFINED(EDS_DataType):
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

    @property
    def range(self):
        return []

    @property
    def value(self):
        return self.__value

    @staticmethod
    def validate(value, *args):
        return True
