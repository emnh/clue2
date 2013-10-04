#!/usr/bin/env python

import sys
import re

from pyPgSQL import PgSQL, libpq

# pyPgSQL.PgSQL

from clue import *
from pprint import pprint

sqlcharset = 'utf-8'

class SQLClueRecord(Record):

    def __init__(self, row):
        attrs = 'word', 'grammar', 'reference', 'country', 'context', 'text'
        for k, v  in zip(attrs, row):
            v = v.decode(sqlcharset)
            setattr(self, k, v)

class SQLClue(object):
    
    def __init__(self):
        host = 'localhost'
        dbname = 'clue'
        user = 'clue'
        passwd = 'clue'
        self.cnx = PgSQL.connect('%s::%s:%s:%s' % (host, dbname, user, passwd))
        self.cur = self.cnx.cursor()

    def lookup(self, lang, word):
        recs = []
        word = word.encode(sqlcharset)
        word = PgSQL.PgQuoteString(word)
        self.cur.execute('SELECT * from %s WHERE word = %s' % (lang, word))
        rows = self.cur.fetchall()
        for row in rows:
            scr = SQLClueRecord(row)
            recs.append(scr)
        return recs

def getBase(fname):
    bname = os.path.basename(fname).lower().replace('.dat', '')
    return bname

def rlookup(searchWord):
    visited = {}
    tovisit = []
    tovisit.append(searchWord)
    gfd = file('wordcluster.dot', 'w')
    gfd.write('digraph G {\n')
    while len(tovisit) > 0 and len(tovisit) < 1000:
        searchWord = tovisit.pop(0)
        print searchWord.encode(termcharset)
        for fname in fnames:
            bname = getBase(fname)
            recs = sc.lookup(bname, searchWord)
            for r in recs:
                print r
                for word in re.findall(r'[^,()!-]+', r.text):
                    word = word.strip()
                    gfd.write((u'"%s" -> "%s";\n' % (searchWord, word)).encode(termcharset))
                    #tag = (bname, word)
                    tag = word
                    if not tag in visited:
                        visited[tag] = True
                        tovisit.append(word)
    gfd.write('}')

fnames = glob.glob('/media/data1/clue/CL*.DAT')
fnames = [x for x in fnames if 'uk' in x.lower() and 'no' in x.lower()]

sc = SQLClue()

print fnames
cfs = [ClueFile(fname) for fname in fnames]
word = sys.argv[1]
rlookup(word)
