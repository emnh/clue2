#!/usr/bin/env python

from clue import *
import sys
import re

def normalize(word):
    cmap = {}
    start = ord('a')
    norm = ''
    for c in word:
        if not c in cmap:
            cmap[c] = chr(start)
            start += 1
        norm += cmap[c]
    return norm

def check(norms):
    words = '''
    XLIVI EVIXA SOMRH WSJGV CTXSW CWXIQ
    WWCQQ IXVMG ERHEW CQQIX VMGWC QQIXV
    MGGVC TXSWC WXIQW YWIXL IWEQI OICXL
    IWIGV IXOIC XSIRG VCTXE RHHIG VCTXE
    QIWWE KIERH EWCQQ IXVMG GVCTX SWCWX
    IQWYW ISRIO ICXLI TYFPM GOICX SIRGV
    CTXEQ IWWEK IERHE HMJJI VIRXO ICXLI
    TVMZE XIOIC XSHIG VCTXM XEWWC QIXVM
    GGVCT XSWCW XIQWE VIEPW SGEPP IHTYF
    PMGOI CGVCT XSWCW XIQW
    '''.lower()
    #words = 'should shakespeare'
    words = re.split(r'\s', words)
    words = filter(lambda x: not x.isspace() and x != '', words)
    choices = {}
    for word in words:
        norm = normalize(word)
        ct = 0
        if norm in norms:
            ct = len(norms[norm])
            # generate set of possible character mappings for a character based on possible word matches
            newchoices = {}
            for i, c in enumerate(word):
                if not c in newchoices:
                    newchoices[c] = set()
                for normMatch in norms[norm]:
                    newchoices[c].add(normMatch[i])
            print 'new:', newchoices
            for c, v in newchoices.items():
                if not c in choices:
                    choices[c] = v
                else:
                    bef = len(choices[c])
                    choices[c].intersection_update(v)
                    print 'b/a:', bef, len(choices[c])

        if 1 <= ct < 10:
            print word, norms[norm]
        print word, norm, ct
    # XXX: sort by word choice ct and iterate
    for c, v in choices.items():
        print c + ':', v

def dumpwords():
    fname = sys.argv[1]
    fd = file(fname)
    buf = fd.read()
    #for recData in buf.split('\0'):
    bpos = 0
    for recData in buf.split('\0'):
        r = Record(recData)
        word = r.word.lower()
        if ' ' in word: continue
        print word.encode('utf-8')
        #if searchFun(r.word):
        #    #print 'bpos: %d, %s' % (bpos, hex(bpos))
        #    #print 'w: %s, r: %s' % (r.word.encode('utf-8'), r.rest.encode('utf-8'))
        #    if r.hasRare:
        #        print str(r)
        bpos += len(recData) + 1

def readwords():
    fname = sys.argv[1]
    fd = file(fname)
    lines = fd.readlines()

    norms = {}
    for line in lines:
        word = line.rstrip()
        #word = word.decode('utf-8')
        word = word.decode('iso-8859-1')
        norm = normalize(word)
        if not norm in norms:
            norms[norm] = []
        norms[norm].append(word)
        #print word, norm
    normcts = norms.items()
    normcts.sort(lambda a,b: cmp(len(a[1]),len(b[1])))
    for norm, words in normcts:
        ct = len(words)
        #print norm, ct
    return norms
    
if sys.argv[1] == 'dump':
    del sys.argv[1]
    dumpwords()
else:
    norms = readwords()
    word = 'xswcw'
    norm = normalize(word)
    print word, norms[norm]
    #check(norms)
