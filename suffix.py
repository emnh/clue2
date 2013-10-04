#!/usr/bin/env python

'Build an XML suffix tree for dictionary'

import sys
import re

from clue import *
from pprint import pprint

termcharset = sys.stdout.encoding
if termcharset == None:
    termcharset = 'utf-8'

class Element(object):

    def __init__(self, name):
        self.name = name
        self.children = {}
        self.records = []

    def toXML(self):
        name = self.name.encode(termcharset)
        s = '<e name="%s">' % name 
        for c in self.children.values():
            #s += '' + c.toXML().replace('\n', '\n ')
            s += c.toXML()
        s += '</e>'
        return s

fnames = glob.glob('/media/data1/clue/CL*.DAT')
print fnames
fname = fnames[1]
fd = file(fname)
buf = fd.read()
elements = {}
i = 0
bufsp = buf.split('\0')
for recData in bufsp:
    i += 1
    r = Record(recData)
    print i * 100 / len(bufsp), r.word.encode(termcharset)
    curElements = elements
    for c in r.word:
        if c in curElements:
            elm = curElements[c]
        else:
            elm = Element(c)
            curElements[c] = elm
        curElements = elm.children
    elm.records.append(r)

outfd = file('suffix.xml', 'w')
outfd.write('<?xml version="1.0" encoding="utf-8"?>')
outfd.write('<root>')
for elm in elements.values():
    outfd.write(elm.toXML())
outfd.write('</root>')
