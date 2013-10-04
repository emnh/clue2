#!/usr/bin/env python

import sys
import re
import pickle

from bsddb import dbshelve
# bsddb.dbshelve

from clue import *
from pprint import pprint

fnames = glob.glob('/media/data1/clue/CL*.DAT')

for fname in fnames:
    fd = file(fname)
    buf = fd.read()
    elements = {}
    i = 0
    bname = os.path.basename(fname).lower()
    bname = bname.replace('.dat', '.db')
    dbdir = 'db'
    if not os.path.exists(dbdir):
        os.mkdir(dbdir)
    bname = os.path.join(dbdir, bname)
    print fname, '->', bname
    try:
        os.unlink(bname)
    except:
        pass
    db = dbshelve.open(bname)

    dbcharset = 'utf-8'

    bufsp = buf.split('\0')
    bpos = 0
    for recData in bufsp:
        bpos += len(recData) + 1
        i += 1
        r = Record(recData)
        print i * 100 / len(bufsp), r.word.encode(termcharset)
        if r.word == 'NOWORD': continue
        word = r.word.encode(dbcharset)
        db[word] = bpos
    db.close()
