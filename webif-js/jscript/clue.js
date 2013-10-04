function create(tag) {
    return document.createElement(tag);
}

function Record(rec) {
    this.word = rec[0];
    this.grammar = rec[1];
    this.reference = rec[2];
    this.country = rec[3];
    this.context = rec[4];
    this.text = rec[5];

    this.formatAsRow = function() {
        s = '';
        s += '<tr>\n';
        s += "<td><span class='word'>" + this.word + "</span></td>\n";
        text = "";
        var k;
        var attrs = ['grammar', 'reference', 'country', 'context', 'text'];
        for (k = 0; k < attrs.length; k++) {
            var attr = attrs[k];
            if (this[attr] != "") {
                text += "<span class='" + attr + "'>" + this[attr] + '</span>' + "\n";
            }
        }
        s += "<td>" + text + "</td>\n";
        s += "</tr>\n";
        return s;
    }
}

cmpwords = function(a, b) {
    if (a < b) return -1;
    if (a == b) return 0;
    if (a > b) return 1;
    //return a.localeCompare(b);
}

function SearchIndex(lang, successCallback) {

    this.searchwords = {};

    var clueidx = 'clue/' + lang + '.json.idx';
    var callback = {
        success: function(o) {
            var data = o.responseText;
            var searchwords = YAHOO.lang.JSON.parse(data);
            var i;
            var debug = $('debug');
            debug.innerHTML = '';
            for (i = 1; i < searchwords.length; i++) {
                if (cmpwords(searchwords[i - 1], searchwords[i]) > 0) {
                    debug.innerHTML += searchwords[i - 1] + " > " + searchwords[i] + '<br/>';
                }
                /*var wordobj = {
                    word: searchwords[i],
                    offset: i * SearchIndex.CHUNKSIZE
                }*/
            }
            this.searchwords = searchwords;
            var results = $('results');
            results.innerHTML = 'successfully loaded dictionary index: ' + clueidx;
            if (successCallback != undefined) successCallback();
        },
        failure: function(o) {
            var results = $('results');
            results.innerHTML = 'failed to load dictionary index: ' + clueidx;
        },
        argument: [],
        scope: this
    }
    YAHOO.util.Connect.asyncRequest('GET', clueidx, callback);

    this.getOffset = function(word) {
        // XXX: use binary search
        var i;
        var ret = null;
        var debug = $('debug');
        for (i = 1; i < this.searchwords.length; i++) {
            sword = this.searchwords[i];
            if (cmpwords(sword, word) > 0) {
                //debug.innerHTML = '"' + this.searchwords[i - 1] + '" "' + this.searchwords[i] + '"';
                ret =  i * SearchIndex.CHUNKSIZE;
                break;
            } else {
                //debug.innerHTML = 'damn ' + i;
            }
        }
        if (ret == null) ret = this.searchwords.length * SearchIndex.CHUNKSIZE;
        //debug.innerHTML += 'ret: ' + ret;
        return ret;
    }
}

SearchIndex.CHUNKSIZE = 4096;

function SearchHandler(lang) {

    this.search = function(word) {
        if (this.conn != undefined) {
            YAHOO.util.Connect.abort(this.conn);
        }
        var callback = {
            success: function(o) {
                var data = o.responseText;
                var lines = data.split('\n');
                var line;
                var i;
                lines = lines.slice(1, lines.length - 2); // first and last may be incomplete records
                var restable = '<table id="result">';
                var started = false;
                for (i = 0; i < lines.length; i++) {
                    line = lines[i];
                    var rec = YAHOO.lang.JSON.parse(line);
                    results = $('results');
                    rec = new Record(rec);
                    if (rec.word.toLowerCase().startsWith(word.toLowerCase())) {
                        started = true;
                    }
                    if (started) restable += rec.formatAsRow();
                }
                restable += '</table>';
                var results = $('results');
                results.innerHTML = restable;
                this.searching = false;
            },
            failure: function(o) {
                var results = $('results');
                results.innerHTML = 'failed to load dictionary';
                this.searching = false;
            },
            argument: [],
            scope: this
        }
        var offset = Dict.searchIndex.getOffset(word);
        var from = offset - SearchIndex.CHUNKSIZE;
        if (from < 0) from = 0;
        var to = offset + SearchIndex.CHUNKSIZE;
        YAHOO.util.Connect.initHeader('Range', 'bytes=' + from + '-' + to, false);
        var cluefile = 'clue/' + lang + '.json';
        this.conn = YAHOO.util.Connect.asyncRequest('GET', cluefile, callback);
    }

}

function Dict() {
}

Dict.addLanguages = function() {
    langMap = {
        "clabfr": "French Abbreviations",
        "clabno": "Norwegian Abbreviations",
        "clabsv": "Swedish Abbreviations",
        "clabuk": "English Abbreviations",
        "cldenomx": "German -> Norwegian",
        "clesukmx": "Spanish -> English",
        "clfrukmx": "French -> English",
        "clsvukmx": "Swedish -> English",
        "clnodemx": "Norwegian -> German",
        "clnono": "Norwegian -> Norwegian",
        "clnonome": "Norwegian Medical",
        "clnoukmx": "Norwegian -> English",
        "clukesmx": "English -> Spanish",
        "clukfrmx": "English -> French",
        "cluknomx": "English -> Norwegian",
        "cluksvmx": "English -> Swedish",
        "clukuk": "English -> English"
    };
    selectlang = $('selectlang');
    var val;
    var i = 0;
    selectlang.remove(0); // remove 'test' option
    for (val in langMap) {
        var text = langMap[val];
        o = create('option');
        o.value = val;
        o.text = text;
        selectlang.add(o, null);
        if (o.value == "clnoukmx") selectlang.selectedIndex = i;
        i++;
    }
}

Dict.searchWord = function() {
    var word = ($('searchword')).value;
    Dict.searchHandler.search(word);
}

Dict.resetLang = function(callback) {
    var lang = Dict.getLang();
    Dict.searchHandler = new SearchHandler(lang);
    Dict.searchIndex = new SearchIndex(lang, callback);
}

Dict.getLang = function() {
    selectlang = $('selectlang');
    return selectlang.options[selectlang.selectedIndex].value;
}

function init() {
    Dict.addLanguages();
    Dict.resetLang(Dict.searchWord);
}

YAHOO.util.Event.onDOMReady(init);
