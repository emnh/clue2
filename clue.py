#!/usr/bin/env python
# *-* coding: utf-8 *-*

'''
Reads the clue file format.
See http://www.clue-international.com/index_no.asp.
'''

import re
import os
import sys
import struct
import glob
from threading import Thread
from bisect import bisect
#from subprocess import Popen, PIPE
from emhpy.terminal import ANSIColor
from emhpy import Singleton
from optparse import OptionParser
#from itertools import islice

FILECHARSET = 'utf-8' # charset of this python file
TERMCHARSET = 'utf-8' # used for terminal io
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
    TERMCHARSET = sys.stdout.encoding
CLUECHARSET = 'cp1252'
BUFSIZE = 4096 # should be greater than size of greatest record
DEBUG = False

class NoLookupWordException(ValueError):
    '''Raised when no lookup word is found in a clue record.
       This is a bug in the dictionary.
    '''
    count = 0
    #records = []

def split(iterable, splitonthis):
    '''splits an iterable by elements returning true when passed to the function
    splitonthis'''
    lst = []
    for item in iterable:
        if splitonthis(item):
            yield lst
            lst = []
        else:
            lst.append(item)
    yield lst

class CharMap(object):
    'Maps for decoding clue encoded characters to unicode.'

    tables16Uncommon = [None] * 4

    tables16 = '\t eartnsli\x08,    \x00bcdfghjkmpquvwx\x00yz'   + \
    "\xf8\xe5-.A\xe6()1*!SU\x0059BWDE'0CT\xe9:\xe8/2\x003KG46L"  + \
    'HOFIJ8Po \x00'

    # from clue 7.3
    alphatable = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'  + \
    '\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19'     + \
    '\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?'  + \
    '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvw'  + \
    'xyz{|}~\x7f\xc7\xfc\xe9\xe2\xe4\xe0\xe5\xe7\xea\xeb\xe8'    + \
    '\xef\xee\xec\xc4\xc5\xc9\xe6\xc6\xf4\xf6\xf2\xfb\xf9\xff'   + \
    '\xd6\xdc\xf8\xa3\xd8\xd7\xbf\xe1\xed\xf3\xfa\xf1\xd1\xaa'   + \
    '\xba\xbf\xae\xac\xbd\xbc\xa1\xab\xbb\xbf\xbf\xbf\xbf\xbf'   + \
    '\xc1\xc2\xc0\xa9\xbf\xbf\xbf\xbf\xa2\xa5\x9c\xbf\xbf\xbf'   + \
    '\xbf\xbf\xbf\xe3\xc3\xbf\xbf\xbf\xbf\xbf\xbf\xbf\xa4\xf0'   + \
    '\xd0\xca\xcb\xc8\xbf\xcd\xce\xcf\xbf\xbf\xbf\xbf\xa6\xcc'   + \
    '\xbf\xd3\xdf\xd4\xd2\xf5\xd5\xb5\xfe\xde\xda\xdb\xd9\xfd'   + \
    '\xdd\xaf\xb4\xb7\xb1\xbf\xbe\xb6\xa7\xf7\xb8\xb0\xa8\xbf'   + \
    '\xb9\xb3\xb2\xbf\xbf'

    uncommonSetBits = 0xC
    lookupWordTerminator = 0

    @classmethod
    def init(cls):
        'class initializer'
        cls.alphatable = cls.alphatable.decode(CLUECHARSET)
        cls.tables16Common = cls.tables16[0:17].decode(CLUECHARSET)
        for i in range(4):
            j = i + 1
            start, end = 1 + j * 16, 1 + (j + 1) * 16
            cls.tables16Uncommon[i] = \
                    cls.tables16[start:end].decode(CLUECHARSET)
            assert len(cls.tables16Uncommon[i]) == 16

    class WordTerminator(object):
        'Represents word termination.'
        pass

    @classmethod
    def mapNibbles(cls, nibblebuf, isReadingLookupWord=True):
        '''Map nibble buffer to unicode characters.  i is the index to start
        reading from.  isReadingLookupWord should be set to true if we're
        starting to read in lookup word.  Returns (number of nibbles consumed,
        character).  character is WordTerminator when the word terminates.
        '''
        # XXX: return WordTerminator for \t

        i = 0
        #print repr(list(nibblebuf))

        table = None

        while i < len(nibblebuf):
            nibble = nibblebuf[i]
            i += 1
            if nibble >= cls.uncommonSetBits:
                # uncommon character
                table = cls.tables16Uncommon[nibble &
                        (0xF - cls.uncommonSetBits)]
                tableIndex = nibblebuf[i]
                #print 'look', tableIndex
                i += 1
                if nibble == 0xF and tableIndex == 0xF:
                    # rare character
                    #cls.hasRare = True
                    table = cls.alphatable
                    tableIndex = nibblebuf[i] << 4 | nibblebuf[i + 1]
                    i += 2
                else:
                    tableIndex -= 1
            else:
                # common character
                table = cls.tables16Common
                tableIndex = nibble
                if tableIndex == cls.lookupWordTerminator and \
                        isReadingLookupWord:
                    isReadingLookupWord = False
                    yield i, cls.WordTerminator
                    continue

            #tables = {
            #        cls.alphatable: 'alpha',
            #        cls.tables16Common: 'common',
            #        cls.tables16Uncommon[0]: 'uncommon0',
            #        cls.tables16Uncommon[1]: 'uncommon1',
            #        cls.tables16Uncommon[2]: 'uncommon2',
            #        cls.tables16Uncommon[3]: 'uncommon3',
            #    }
            #tablename = tables[table]
            #print 'table: %s, len: %d, idx: %d, char: %s' % (
            #        tablename, len(table), tableIndex,
            #        table[tableIndex]
            #        )
            assert isinstance(table[tableIndex], unicode)
            yield i, table[tableIndex]

CharMap.init()

class HashCharMap(object):
    '''
    Map from ord(char) where char is cp1252 character to value in hash function.
    Comparing strings after mapping characters through these maps is probably a
    valid sort order.
    '''

    class DictAccess(type):
        'dict access to class attributes'
        def __getitem__(mcs, item):
            return getattr(mcs, item)

    __metaclass__ = DictAccess

    n = None

    no = [0, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, 1, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, 2, 3,
            4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
            22, 23, 24, 25, 26, 27, n, n, n, n, n, n, 2, 3, 4, 5, 6, 7, 8, 9,
            10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
            27, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, [16, 6], n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, 2, 2, 2, 2, 28, 30, 28, 4, 6, 6, 6, 6, 10, 10,
            10, 10, 5, 15, 16, 16, 16, 16, 29, n, 29, 22, 22, 22, 22, 26, n,
            [20, 20], 2, 2, 2, 2, 28, 30, 28, 4, 6, 6, 6, 6, 10, 10, 10, 10, 5,
            15, 16, 16, 16, 16, 29, n, 29, 22, 22, 22, 22, 26, n, 26]

    sv = [0, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, 1, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, 2, 3,
            4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
            22, 23, 23, 25, 26, 27, n, n, n, n, n, n, 2, 3, 4, 5, 6, 7, 8, 9,
            10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 23, 25, 26,
            27, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, [16, 6], n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, 2, 2, 2, 2, 29, 28, 29, 4, 6, 6, 6, 6, 10, 10,
            10, 10, 5, 15, 16, 16, 16, 16, 30, n, 30, 22, 22, 22, 22, 26, n,
            [20, 20], 2, 2, 2, 2, 29, 28, 29, 4, 6, 6, 6, 6, 10, 10, 10, 10, 5,
            15, 16, 16, 16, 16, 30, n, 30, 22, 22, 22, 22, 26, n, 26]

    uk = [0, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, 1, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, 2, 3,
            4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
            22, 23, 24, 25, 26, 27, n, n, n, n, n, n, 2, 3, 4, 5, 6, 7, 8, 9,
            10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
            27, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, [16, 6], n, n, n, n, n, n, n,
            n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n, n,
            n, n, n, n, n, n, 2, 2, 2, 2, 2, 2, 2, 4, 6, 6, 6, 6, 10, 10, 10,
            10, 5, 15, 16, 16, 16, 16, 16, n, 16, 22, 22, 22, 22, 26, n, [20,
                20], 2, 2, 2, 2, 2, 2, 2, 4, 6, 6, 6, 6, 10, 10, 10, 10, 5, 15,
            16, 16, 16, 16, 16, n, 16, 22, 22, 22, 22, 26, n, 26]

    de = fr = es = uk

    @classmethod
    def map(cls, langcode, char):
        'map character in language langcode to its hash value'
        if isinstance(char, str):
            char = ord(char)
        return cls[langcode][char]

class LangMap(object):
    'Maps between language and dictionary filenames.'

    __metaclass__ = Singleton

    langMap = {
        "clabfr.dat": "French Abbreviations",
        "clabno.dat": "Norwegian Abbreviations",
        "clabsv.dat": "Swedish Abbreviations",
        "clabuk.dat": "English Abbreviations",
        "cldenomx.dat": "German -> Norwegian",
        "clesukmx.dat": "Spanish -> English",
        "clfrukmx.dat": "French -> English",
        "clsvukmx.dat": "Swedish -> English",
        "clnodemx.dat": "Norwegian -> German",
        "clnono.dat": "Norwegian -> Norwegian",
        "clnonome.dat": "Norwegian Medical",
        "clnoukmx.dat": "Norwegian -> English",
        "clukesmx.dat": "English -> Spanish",
        "clukfrmx.dat": "English -> French",
        "cluknomx.dat": "English -> Norwegian",
        "cluksvmx.dat": "English -> Swedish",
        "clukuk.dat": "English -> English",
    }

    langCodes = {
            'de': 'German',
            'es': 'Spanish',
            'fr': 'French',
            'no': 'Norwegian',
            'sv': 'Swedish',
            'uk': 'English'
            }

    def __init__(self):
        self.revLangMap = dict((y, x) for (x, y) in self.langMap.items())

    def fileNameToLanguage(self, filename):
        'Map filename to language.'
        filename = os.path.basename(filename)
        filename = filename.lower()
        return self.langMap[filename]

    def languageToFileName(self, language):
        'Map language to filename.'
        return self.revLangMap[language]

    def getSourceLang(self, fname, useCode=True):
        'Map filename to source language or language code.'
        return self.getLangs(fname, useCode)[0]

    def getLangs(self, fname, useCode=True):
        '''Map filename to (fromLanguage, toLanguage). if useCode is True
        (default) language codes are returned instead.'''

        fname = os.path.basename(fname)
        match = re.search('^cl([a-z]{2})([a-z]{2})', fname, re.I)
        # XXX: check for match
        fromLang = match.group(1).lower()
        toLang = match.group(2).lower()
        if fromLang == 'ab':
            fromLang = toLang
        if not useCode:
            # XXX: check that code exists
            fromLang = self.langCodes[fromLang]
            toLang = self.langCodes[toLang]
        return fromLang, toLang

def hdstr(txt):
    'hexdump string for debugging'
    return [hex(ord(y)) for y in txt]

class ClueIndex(object):
    'Read a file indexing words in a dictionary.'
    # index "header" is 0x500 long
    # each index "block" is 0x600 long
    HEADERSIZE = 0x500
    BLOCKSIZE = 0x600
    HASHLEN = 6
    hashCache = {}

    def __init__(self, fname):
        fd = file(fname)
        self.idxdata = fd.read()
        self.idxheader = self.idxdata[:self.HEADERSIZE]
        self.lang = LangMap().getSourceLang(fname)

    def hashString(self, txt):
        'Calculate clue hash from string.'
        assert isinstance(txt, unicode)

        txt = txt.encode(CLUECHARSET)

        #if txt in self.hashCache:
        #    return self.hashCache[txt]

        cvals = [0] * self.HASHLEN

        # translate characters
        i = 0
        for char in txt[0:self.HASHLEN]:
            val = HashCharMap.map(self.lang, char)
            if val != None:
                if isinstance(val, list):
                    for item in val:
                        cvals[i] = item
                        i += 1
                else:
                    cvals[i] = val
                    i += 1

        # hash em
        hstr = ''
        out = (cvals[0] << 3) | (cvals[1] >> 2)
        hstr += chr(out & 0xFF)
        out = (cvals[1] << 6) | (cvals[2] << 1) | (cvals[3] >> 4)
        hstr += chr(out & 0xFF)
        out = (cvals[3] << 4) | (cvals[4] >> 1)
        hstr += chr(out & 0xFF)
        out = (cvals[4] << 7) | (cvals[5] << 2)
        hstr += chr(out & 0xFF)

        self.hashCache[txt] = hstr

        return hstr

    def lookupHash(self, hstr):
        'lookup hash in index header'
        val = None
        for i in xrange(0, len(self.idxheader), 4):
            val = i
            dt = self.idxheader[i:i + 4]
            if hstr < dt:
                #print hdstr(dt)
                break
        idx = (val / 4) * self.BLOCKSIZE + self.HEADERSIZE
        #print 'block', hex(idx)
        block = self.idxdata[idx:idx + self.BLOCKSIZE]

        overflow = 0
        rsize = 6 # record: 4 byte hash, 2 byte data offset
        val = None
        for i in xrange(rsize, len(block), rsize):
            val = i
            dt = block[i:i + 4]
            if hstr <= dt:
                #print 'ebx=%s, cmp(%s, %s)' % (hex(i / rsize),
                #        hdstr(hstr), hdstr(dt))
                break
            # detect overflows and make up for them.  they presumably don't
            # wrap twice because two hashes are too close, so if the next
            # offset is less than previous, must be overflow
            #print 'woff', hex(struct.unpack('H', block[i+4:i+4+2])[0])
            if block[i:i + rsize + 4] > block[i:i + 2*rsize + 4]:
                overflow += 0x10000

        idx = val + 0xA - rsize

        dataoffset = struct.unpack('H', block[idx:idx+2])[0]
        dataoffset += struct.unpack('I', block[0:4])[0]
        dataoffset += overflow
        #print 'dataoffset:', hex(dataoffset)

        return dataoffset

    def testIndex(self, printRec):
        'for each character in the alphabet lookup first word starting with it'
        for char in range(ord('a'), ord('z') + 1):
            char = chr(char)
            hstr = self.hashString(char)
            dataoffset = self.lookupHash(hstr)
            #print char, hdstr(hstr), hex(dataoffset)
            printRec(dataoffset)

class NibbleBuffer(object):

    'View bytes as nibbles.'

    def __init__(self, buf):
        assert isinstance(buf, basestring)
        self.buf = buf

    def __getitem__(self, i):
        reali = int(i / 2)
        if i % 2 == 0:
            nibble = ord(self.buf[reali]) >> 4
        else:
            nibble = ord(self.buf[reali]) & 0xF
        return nibble

    def __getslice__(self, start, end):
        return [self[i] for i in range(start, end)]

    def __len__(self):
        return len(self.buf) * 2

class Record(object):

    ''' Read a clue record from file.
        Properties:
        word - the lookup word
        grammar - grammatical info
        reference - to other word
        country - geographical use info
        context -
        text - the lookup text

    '''

    class Colorer(object):
        '''use/subclass this to color record when formatted as string.
        '''

        def __init__(self, colorfunc=None):
            '''colorfunc is a function that takes a string and a color name
            and returns a colorized string.'''
            self.colorfunc = colorfunc

        def lookupWord(self, string):
            'color lookup word'
            return self.colorfunc(string, 'blue')

        def grammar(self, string):
            'color grammar'
            return self.colorfunc(string, 'red')

        def reference(self, string):
            'color reference'
            return self.colorfunc(string, 'magenta')

        def country(self, string):
            'color country'
            return self.colorfunc(string, 'cyan')

        def context(self, string):
            'color context'
            return self.colorfunc(string, 'white')

        @staticmethod
        def text(string):
            'color text'
            return string

    def __init__(self, buf, comparator=None):
        nibblebuf = NibbleBuffer(buf)
        chars = [iAndChar[1] for iAndChar in CharMap.mapNibbles(nibblebuf)]
        if CharMap.WordTerminator not in chars:
            raise NoLookupWordException(
                    'no lookup word in record: len: %d, chars: %s' %
                    (len(buf), repr(''.join(chars)))
                    )
        else:
            words = list(split(chars, lambda x: x is CharMap.WordTerminator))
            #print chars, words
            self.word, rest = [u''.join(x) for x in words]
            #print self.word.encode('utf-8')

        tmp = rest.split('\b')
        meta = tmp[0:-1]
        meta.extend([''] * (4 - len(meta)))
        self.grammar = meta[0]
        self.reference = meta[1]
        self.country = meta[2]
        self.context = meta[3]
        self.text = tmp[-1]
        self.text = self.text.rstrip('\t')
        self._comparator = comparator

    def __str__(self):
        return self.toString()

    def toString(self, incword=True, colorer=None):
        '''format as string. arguments:
        bool incword - include lookup word,
        Record.Colorer colorer - colouring handler
        '''

        if not colorer:
            colorer = self.Colorer()

        if incword:
            word = self.word
        else:
            word = ''
        s = colorer.lookupWord(word.ljust(40))

        other = u''
        if self.grammar:
            other += '%s.' % colorer.grammar(self.grammar)
        if self.reference:
            other += ' (%s.)' % colorer.reference(self.reference)
        if self.country:
            other += ' (%s)' % colorer.country(self.country)
        if self.context:
            other += ' [%s]' % colorer.context(self.context)
        other += ' ' + colorer.text(self.text)
        s += other.strip()
        return s.encode(TERMCHARSET)

    def __cmp__(self, other):
        assert self._comparator != None, \
                'initalize with comparator to use __cmp__'
        comparator = self._comparator
        retcmp = comparator(self.word, other.word)
        if retcmp == 0:
            # if FakeRecord is involved that means bisect, which means we're
            # searching for upper bounds, not matches.
            if isinstance(self, FakeRecord):
                retcmp = -1
            elif isinstance(other, FakeRecord):
                retcmp = 1
        return retcmp

#    @classmethod
#    def readFd(cls, fd, pos):
#        'read clue record at pos in file fd'
#        if pos > 0:
#            fd.seek(pos - 1)
#            if fd.read(1) != '\0':
#                print 'not a record'
#                return
#        fd.seek(pos)
#        recData = fd.read(BUFSIZE).split('\0')[0]
#        record = cls(recData)
#        return record

#class RecordsViewIndex(object):
#    'map raw records to cluerecords'

#    def __init__(self, data, lang):
#        self.rawrecords = data.split('\x00')
#        self.lang = lang

#    def __getitem__(self, index):
#        record = Record(self.rawrecords[index], self.comparator)
#        return record

#    def __getslice__(self, start, end):
#        return [self[i] for i in range(start, end)]

#    def __len__(self):
#        return len(self.rawrecords)

class RecordsViewOffset(object):
    'map raw records to cluerecords for bisect'

    def __init__(self, fd, comparator):
        self.fd = fd
        self.comparator = comparator

    def __getitem__(self, offset):
        #print index, repr(self.rawrecords[index])
        'get record surrounding offset'
        halfsize = int(BUFSIZE / 2)
        if offset - halfsize < 0:
            self.fd.seek(0)
            rawrecord = self.fd.read(BUFSIZE).split('\x00', 1)[0]
        else:
            self.fd.seek(max(offset - halfsize, 0))
            data = self.fd.read(BUFSIZE)
            before, after = data[0:halfsize], data[halfsize:BUFSIZE]
            rawrecord = before.rsplit('\x00', 1)[-1] + \
                        after.split('\x00', 1)[0]
        assert isinstance(rawrecord, basestring)
        record = Record(rawrecord, self.comparator)
        return record

#    def __getslice__(self, start, end):
#        offset = int((start + end) / 2)
#        avgRecordSize = 20 # wild guess
#        size = (end - start) * avgRecordSize
#        halfsize = int(size / 2)
#        self.fd.seek(max(offset - halfsize, 0))
#        data = self.fd.read(size)
#        iview = RecordsViewIndex(data, self.lang)
#        return iview[1:-1]

    def __len__(self):
        # seek to end
        self.fd.seek(0, 2)
        return self.fd.tell()

class FakeRecord(Record):
    'fake record for bisect purposes'
    def __init__(self, word, comparator):
        self.word = word
        self._comparator = comparator
        if False:
            super(FakeRecord, self).__init__()


class ClueFile(object):

    'Represents clue dictionary file.'

    def __init__(self, fname):
        self.fname = fname
        self.fd = file(fname)
        self.idxfname = fname.replace('.DAT', '.IDX')
        self.cidx = ClueIndex(self.idxfname)
        self._len = None
        self._comparator = getClueCmp(LangMap().getSourceLang(self.fname))

    def compare(self, word1, word2):
        'compare lookup words in the language of the current file'
        return self._comparator(word1, word2)

    def lookupBisect(self, word):
        'Lookup clue records matching word using binary search'
        #rview = RecordsViewIndex(self.fd.read(), lang)
        rview = RecordsViewOffset(self.fd, self.compare)
        matchOffset = bisect(rview, FakeRecord(word, self.compare))
        #records = [x for x in rview[max(match - 100, 0):match + 100]]
        bisectFuzz = 0 # wild guess for maximum bisect inaccuracy
        records = self.getSequential(self.fd, matchOffset - bisectFuzz, False)
        return records

    def lookupIndex(self, word):
        '''Lookup clue records matching word using clue index.
        Returns an iterator over records starting at the matched word.
        '''
        hstr = self.cidx.hashString(word)
        off = self.cidx.lookupHash(hstr)
        recs = self.getSequential(self.fd, off)
        return recs

    #lookup = lookupIndex
    lookup = lookupBisect

    def __iter__(self):
        return self.getSequential(self.fd, 0)

    def __len__(self):
        if not self._len:
            oldpos = self.fd.tell()
            self.fd.seek(0)
            data = self.fd.read()
            self.fd.seek(oldpos)
            self._len = len(data.split('\x00'))
        return self._len

    @staticmethod
    def group(records):
        'group records by lookup word'
        # XXX: implement order fuzz
        oldword = None
        thisWordRecords = []
        for record in records:
            if oldword == None or oldword == record.word:
                #self.compare(oldword, record.word) == 0:
                thisWordRecords.append(record)
            elif thisWordRecords:
                yield thisWordRecords
                thisWordRecords = []
            oldword = record.word

    @staticmethod
    def getSequential(fd, off, exact=True):
        '''Iterator over clue records from fd starting at offset off.  Set
        exact to False if you're not sure offset is at the start of a clue
        record; this will skip backwards until offset is at a record.
        '''
        if not exact:
            # seek backwards until we find record separator
            seekback = (BUFSIZE if off >= BUFSIZE else off)
            fd.seek(off - seekback)
            data = fd.read(seekback)
            # backskip is the amount of data we missed in the start record
            backskip = len(data.rsplit('\x00', 1)[-1])
        else:
            backskip = 0
        fd.seek(off - backskip)
        rest = ''
        done = False
        while not done:
            newdata = fd.read(BUFSIZE)
            if len(newdata) == 0:
                done = True
            data = rest + newdata
            datasp = data.split('\0')
            userecords = datasp[:-1]
            for recData in userecords:
                if len(recData) > 0:
                    try:
                        record = Record(recData)
                        yield record
                    except NoLookupWordException:
                        NoLookupWordException.count += 1
            rest = datasp[-1]

def printWords(txt, title, fname):
    'lookup word txt and print searchFun-filtered list of records from fname'
    cf = ClueFile(fname)

    # print matching records
    recs = cf.lookup(txt)
    foundMatch = False
    colorer = Record.Colorer(ANSIColor.colorize)
    for group in cf.group(recs):
        if cf.compare(txt, group[0].word) == 0:
            if not foundMatch:
                print title + ':'
                foundMatch = True
            print group[0].toString(True, colorer)
            for record in group[1:]:
                print record.toString(False, colorer)
        else:
            break
    if foundMatch:
        print

def cmpHash(s, lang):
    'hash string s for use in string order comparison.'
    assert not isinstance(s, unicode), s
    ret = []
    s = re.sub(r'\(.*?\).*', '', s) # omit paranthesized chars
    #s = re.sub(r' /', ' \xff', s) # omit paranthesized chars
    for i, char in enumerate(s):
        if ord(char) > 255:
            print type(s), s, char, ord(char)
        if char == ' ' and i + 1 < len(s) and s[i + 1] == '/':
            val = None
        else:
            val = HashCharMap.map(lang, char)
        if val != None:
            if isinstance(val, list):
                ret.extend(val)
            else:
                ret.append(val)
    if ret:
        while ret[-1] == 1:
            del ret[-1]
    return ret

def getClueCmp(lang):
    'return clue string comparison function for language lang'
    def cluecmp(a, b, debug=False, lang=lang):
        'compare two clue strings'
        #print 'a: %s / b: %s' % (a, b)
        assert isinstance(a, unicode), a
        assert isinstance(b, unicode), b
        a = a.encode(CLUECHARSET)
        b = b.encode(CLUECHARSET)
        a2, b2 = cmpHash(a, lang), cmpHash(b, lang)
        if debug:
            print a, a2, b, b2, cmp(a2, b2)
        return cmp(a2, b2)
    return cluecmp

class TestStats(object):
    'test statistics'
    def __init__(self):
        self.goodct = 0
        self.badct = 0

#class FileLogger(object):

#    def __init__(self, fname):
#        self.fd = file(fname, 'w')

#    def log(self, msg):
#        'log message'
#        self.fd.write(msg)
#
#    def close(self):
#        'cleanup'
#        self.fd.close()

#    def __del__(self):
#        self.close()

class TestFile(Thread):
    'run tests on file fname'

    def __init__(self, pfx, fname):
        super(TestFile, self).__init__()
        self.pfx = pfx
        self.fname = fname
        bname = os.path.basename(fname)
        self.ofname = os.path.join(pfx, bname)
        self.ofname2 = os.path.join(pfx, bname + 'nonascii')
        self.clang = LangMap().getSourceLang(fname)
        self.cluecmp = getClueCmp(LangMap().getSourceLang(fname))

    def run(self):
        'run test'
        ofd = file(self.ofname, 'w')
        ofd2 = file(self.ofname2, 'w')
        lastword = None
        stats = TestStats()

        cf = ClueFile(self.fname)
        lang = LangMap().fileNameToLanguage(self.fname)

        for i, record in enumerate(cf):
            # print words with cp1252 special chars
            #cw = [x for x in r.word.encode('cp1252')
            #        if ord(x) >= 0x80 and ord(x) <= 0x9f]

            #if len(cw) > 0:
            #    print r.word.encode('utf-8')

            # print all words with nonascii characters
            nonascii = [x for x in record.word.encode('cp1252')
                    if not re.search('[-A-Za-z0-9 ]', x)]
            if len(nonascii) > 0:
                ofd2.write(record.word.encode('utf-8') + '\n')

            if lastword != None:
                ret = self.cluecmp(lastword, record.word)
                if ret > 0:
                    stats.badct += 1
                    ofd.write(
                            '%s > %s\n' % (
                            lastword.encode('utf-8'),
                            record.word.encode('utf-8'))
                            )
                    ofd.write(
                            '%s > %s\n' % (
                            cmpHash(lastword.encode(CLUECHARSET), self.clang),
                            cmpHash(record.word.encode(CLUECHARSET),
                                self.clang))
                            )
                    ofd.flush()
                else:
                    stats.goodct += 1
            lastword = record.word
            if i % (len(cf) / 100) == 0:
                print '%s: %.2f' % (lang, float(i) / len(cf) * 100)
        ofd.close()
        ofd2.close()
        print 'good/bad: %d/%d' % (stats.goodct, stats.badct)

def test(fnames):
    'run tests on files named in fnames'
    # more test code

    pfx = '/home/emh/debug'

    if not os.path.exists(pfx):
        os.mkdir(pfx)

    pids = []
    for fname in fnames:
        #if not 'DENO' in fname:
        #    continue
        tf = TestFile(pfx, fname)
        pid = os.fork()
        if pid == 0:
            tf.run()
            break
        else:
            pids.append(pid)
            if len(pids) >= 2:
                pid = os.wait()[0]
                del pids[pids.index(pid)]

def readfile(fname):
    'read whole file'
    fd = file(fname)
    data = fd.read()
    fd.close()
    return data

def filterByLang(fnames, fromLangs=None, toLangs=None):
    'filter filenames by fromLanguages and toLanguages'
    for fname in fnames:
        fromLangCode, toLangCode = LangMap().getLangs(fname)
        fromLang, toLang = LangMap().getLangs(fname, False)
        if (fromLangs == None or fromLangCode in fromLangs
                or fromLang in fromLangs) and \
                (toLangs == None or toLangCode in toLangs or toLang in
                        toLangs):
            yield fname

def listDictionaries(fnames):
    'list dictionaries with language names'
    fnames = list(fnames)
    maxflen = max(len(x) for x in fnames)
    maxllen = max(len(x) for x in LangMap().langCodes.values())
    for fname in fnames:
        fromLangCode, toLangCode = LangMap().getLangs(fname)
        fromLang, toLang = LangMap().getLangs(fname, False)
        lfname = fname.ljust(maxflen)
        fromLang = fromLang.ljust(maxllen)
        print '%s  %s/%s  %s/%s' % (lfname,
                fromLangCode, fromLang, toLangCode, toLang)

def dumpWords(fname):
    'dump lookup words in fname'
    cf = ClueFile(fname)
    for records in cf.group(cf.getSequential(cf.fd, 0)):
        print records[0].word.encode(TERMCHARSET)

def main():
    'entry point'

    op = OptionParser()
    op.set_usage('%prog [options] <word>')

    op.add_option('-d',
            '--dict-dir',
            action = 'append',
            help='set/add directory to list of directories searched ' +
            'for dictionaries')

    op.add_option('',
            '--dump-words',
            action = 'store_true',
            help = "dump words in dictionary"
            )

    op.add_option('-l',
            '--list-dicts',
            action = 'store_true',
            help = 'list languages for found dictionaries')

    op.add_option('-f',
            '--from-lang',
            action = 'append',
            help = 'select/add from-language. default is all found.')

    op.add_option('-t',
            '--to-lang',
            action = 'append',
            help = 'select/add to-language. default is all found.')

    op.add_option('',
        '--test-order',
        action = 'store',
        help = 'test sort order. dumps results to $HOME/debug.')

    options, args = op.parse_args()

    # find dictionaries
    dictdirs = [ '/media/data/software/clue' ]
    if options.dict_dir:
        dictdirs = options.dict_dir
    globpat = '[Cc][Ll]*.[Dd][Aa][Tt]'
    fnames = sum([glob.glob(os.path.join(dirname, globpat))
        for dirname in dictdirs], [])
    fnames.sort()

    fromLangs = options.from_lang
    toLangs = options.to_lang
    fnames = filterByLang(fnames, fromLangs, toLangs)

    if options.dump_words:
        for fname in fnames:
            lang = LangMap().fileNameToLanguage(fname)
            print lang + ':'
            dumpWords(fname)
    elif options.list_dicts:
        listDictionaries(fnames)
    elif options.test_order:
        test(fnames)
    elif len(args) > 0:
        # lookup word
        txt = args[0].decode(TERMCHARSET)

        for fname in fnames:
            lang = LangMap().fileNameToLanguage(fname)
            printWords(txt, lang, fname)
    else:
        op.print_help()

if __name__ == '__main__':
    main()
