var records = [];
var i = 0;

load('jslib/json2.js');

function Record(rec) {
    this.word = rec[0];
    this.grammar = rec[1];
    this.reference = rec[2];
    this.country = rec[3];
    this.context = rec[4];
    this.text = rec[5];
    this.rec = rec;

    this.toString = function() {
        return JSON.stringify(this.rec);
    }
}

// read input
while(true) {
    var a = readline();
    if (a == '') break;

    records[i] = new Record(eval(a));
    i++;
}

// sort
sortfun = function(a, b) {
    a = a.word;
    b = b.word;
    if (a < b) return -1;
    if (a == b) return 0;
    if (a > b) return 1;
    //return a.localeCompare(b);
}
records.sort(sortfun);

// output records
function output(records) {
    var i;
    for (i = 0; i < records.length; i++) {
        print(records[i]);
    }
}

// write index
function index(records) {
    var offset = 0;
    var CHUNKSIZE = 4096;
    var lastchunk = -1;
    
    var chunkwords = [];
    var rec;
    for (i = 0; i < records.length; i++) {
        rec = records[i];
        a = new String(rec);
        offset += a.length + 1; // 1: newline

        chunk = Math.floor(offset / CHUNKSIZE);
        if (chunk > lastchunk) {
            chunkwords[chunk] = rec.word;
            lastchunk = chunk;
        }
    }

    print(JSON.stringify(chunkwords));
}
