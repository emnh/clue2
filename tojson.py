#!/usr/bin/env python

import sys
import re
import pickle
import json

from pyPgSQL import PgSQL, libpq

from bsddb import dbshelve
# bsddb.dbshelve

from clue import *
from pprint import pprint

# Remember to run initdb with locale setting no_NO.UTF-8

if __name__ == '__main__':
    fnames = glob.glob('/media/data1/clue/CL*.DAT')
    #fnames = glob.glob('/media/data1/clue/CLDENOMX.DAT')

    host = 'localhost'
    dbname = 'clue'
    user = 'clue'
    passwd = 'clue'

    cnx = PgSQL.connect('%s::%s:%s:%s' % (host, dbname, user, passwd))

    cur = cnx.cursor()

    for fname in fnames:
        elements = {}
        i = 0
        bname = os.path.basename(fname).lower()
        tablename = bname.replace('.dat', '')
        bname = bname.replace('.dat', '.json')
        dbdir = 'json'
        if not os.path.exists(dbdir):
            os.mkdir(dbdir)
        jsondbname = os.path.join(dbdir, bname)
        print fname, '->', jsondbname
        try:
            os.unlink(jsondbname)
        except:
            pass
        outfd = file(jsondbname, 'w')
        idxfd = file(jsondbname + '.idx', 'w')

        try:
            sql = "SELECT * FROM %s ORDER BY word" % tablename
            cur.execute(sql)
        except PgSQL.Error, msg:
            print "Select from database failed\n%s" % msg,
            sys.exit()

        dbcharset = 'utf-8'
        jsoncharset = 'utf-8'

        bpos = 0
        chunksize = 4096
        lastbchunk = -1

        chunkwords = []
        while True:
            bpos = outfd.tell()
            rs = cur.fetchone()
            if rs == None:
                break
            rec = []

            for x in ('word', 'grammar', 'reference', 'country', 'context', 'text'):
                val = rs[x] #.decode(dbcharset).encode(jsoncharset)
                rec.append(val)
            jstr = json.write(rec)
            outfd.write(jstr + '\n')

            bchunk = int(bpos / chunksize)
            if bchunk > lastbchunk:
                word = rec[0]
                chunkwords.append(word)
                #print rs['word'], bpos - bchunk*chunksize
                lastbchunk = bchunk

        chunkwords = json.write(chunkwords)
        idxfd.write(chunkwords)

        outfd.close()
        idxfd.close()
