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
from eds_pie import eds_pie

with open('netx.eds', 'r') as srcfile:
    eds_content = srcfile.read()
eds = eds_pie.parse(eds_content, showprogress = True)

if eds.protocol == 'EtherNetIP':
    entry = eds.getentry('device', 'ProdType')
    field = entry.fields[0]
    if field.value == 12:
        print 'This is an EtherNet/IP Communication adapter device.'
    # Alternate way: The value attribute of an entry always returns its first field value.
    if entry.value == 12:
        print 'This is an EtherNet/IP Communication adapter device.'

    if eds.hassection(0x5D):
        eds.list(eds.get_cip_section_name(0x5D))
        '''
        The device is capable of CIP security.
        Do some stuff with security objects.
        '''
    else:
        print 'Device doesn\'t support CIP security'
