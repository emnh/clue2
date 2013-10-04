#!/usr/bin/env python

import sys
import re

from clue import *
from pprint import pprint

fnames = glob.glob('/media/data1/clue/CL*.DAT')

for fname in fnames:
    fd = file(fname)
    buf = fd.read()
    elements = {}
    i = 0
    bname = os.path.basename(fname).lower()
    bname = bname.replace('.dat', '.xml')
    if not os.path.exists('xml'):
        os.mkdir('xml')
    bname = os.path.join('xml', bname)
    print fname, '->', bname
    outfd = file(bname, 'w')

    xmlcharset = 'utf-8'
    outfd.write('<?xml version="1.0" encoding="%s"?>' % xmlcharset)
    outfd.write('<records>\n')

    bufsp = buf.split('\0')
    for recData in bufsp:
        i += 1
        r = Record(recData)
        print i * 100 / len(bufsp), r.word.encode(termcharset)
        if r.word == 'NOWORD': continue
        attrs = ['word', 'grammar', 'reference', 'country', 'context']
        rs = '<record'
        for attr in attrs:
            val = getattr(r, attr)
            if val != '':
                rs += ' %s="%s"' % (attr, val)
        rs += '>%s</record>\n' % r.text
        rs = rs.encode(xmlcharset)
        outfd.write(rs)
    outfd.write('</records>\n')
