#!/usr/bin/env python

import sys
import re

from pyPgSQL import PgSQL

# pyPgSQL.PgSQL

from clue import *
from pprint import pprint

fnames = glob.glob('/media/data1/clue/CL*.DAT')

host = 'localhost'
dbname = 'clue'
user = 'clue'
passwd = 'clue'

cnx = PgSQL.connect('%s::%s:%s:%s' % (host, dbname, user, passwd))

for fname in fnames:
    fd = file(fname)
    buf = fd.read()
    elements = {}
    i = 0
    bname = os.path.basename(fname).lower()
    bname = bname.replace('.dat', '')
    print fname, '->', bname

    cur = cnx.cursor()

    try:
        res = cur.execute('DROP TABLE %s' % bname)
    except StandardError:
        pass
    res = cur.execute('CREATE TABLE %s (word varchar, grammar varchar, reference varchar, country varchar, context varchar, text varchar)' % bname)

    sqlcharset = 'utf-8'

    bufsp = buf.split('\0')
    for recData in bufsp:
        i += 1
        r = Record(recData)
        print i * 100 / len(bufsp), r.word.encode(termcharset)
        if r.word == 'NOWORD': continue
        attrs = ['word', 'grammar', 'reference', 'country', 'context', 'text']
        values = []
        for attr in attrs:
            val = getattr(r, attr)
            val = val.encode(sqlcharset)
            val = PgSQL.PgQuoteString(val)
            values.append(val) 
        rs = 'INSERT INTO %s (%s) VALUES (%s)' % (bname, ','.join(attrs), ','.join(values))
        cur.execute(rs)

    cur.execute('CREATE INDEX %s_word_index on %s (word)' % (bname, bname))
    cnx.commit()
