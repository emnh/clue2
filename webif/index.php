<?php

require ('/var/www/emh/xajax/xajax_core/xajax.inc.php');
$xajax = new xajax();

/*
	- enable debugging if desired
	- set the javascript uri (location of xajax js files)
*/
//$xajax->configure('debug', true);
$xajax->configure('javascript URI', '../');

function searchWord($word, $lang) {
	$objResponse = new xajaxResponse();

    error_reporting(0);

    $conn = pg_connect("host=localhost dbname=clue user=clue password=clue");
    $word = pg_escape_string($word);
    $res = pg_query("SELECT * FROM $lang WHERE word LIKE '$word%' LIMIT 30");

    if (!$res) {
        $err = pg_last_error($conn);
        $objResponse->assign("result", 'innerHTML', '<p>' . $err . '</p>');
        return $objResponse;
    }

    $attrs = array('grammar', 'reference', 'country', 'context', 'text');

    $s = "<table>\n";
    while ($r = pg_fetch_assoc($res)) {
        $s .= "<tr>\n";
        $s .= "<td><span class='word'>" . $r[word] . "</span></td>\n";
        $text = "";
        foreach ($attrs as $k) {
            if ($r[$k] != "") {
                $text .= "<span class='$k'>" . $r[$k] . '</span>' . "\n";
            }
        }
        $s .= "<td>$text</td>\n";
        $s .= "</tr>\n";
    }
    $s .= "</table>\n";

	$objResponse->assign('result', 'innerHTML', $s);
	
	return $objResponse;
}

$xajax->registerFunction('searchWord');

$xajax->processRequest();

echo '<?xml version="1.0" encoding="UTF-8"?>';
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<title>Dictionary lookup</title>
    <style type='text/css'>
        table {
            background: black;
            border: 3px solid gray;
        }
        span.word {
            color: blue;
        }
        span.text {
            color: gray;
        }
        span.grammar {
            color: red;
        }
        span.reference {
            color: magenta;
        }
        span.country {
            color: cyan;
        }
        span.context {
            color: white;
        }
    </style>
<?php
	// output the xajax javascript. This must be called between the head tags
	$xajax->printJavascript();
?>
	<script type='text/javascript'>
        function searchWord() {
            word = document.getElementById("word");
            selectlang = document.getElementById("selectlang");
            lang = selectlang.options[selectlang.selectedIndex].value;
            xajax_searchWord(word.value, lang);
        }
	</script>
</head>
<body>
    <span>Search</span>
    <input id="word" type="text" onkeyup='searchWord();'/>
    <select id="selectlang" onchange='searchWord();'>
        <?php
            $langMap = array(
                "clabfr" => "French Abbreviations",
                "clabno" => "Norwegian Abbreviations",
                "clabsv" => "Swedish Abbreviations",
                "clabuk" => "English Abbreviations",
                "cldenomx" => "German -> Norwegian",
                "clesukmx" => "Spanish -> English",
                "clfrukmx" => "French -> English",
                "clsvukmx" => "Swedish -> English",
                "clnodemx" => "Norwegian -> German",
                "clnono" => "Norwegian -> Norwegian",
                "clnoukmx" => "Norwegian -> English",
                "clnonome" => "Norwegian Medical",
                "clukesmx" => "English -> Spanish",
                "clukfrmx" => "English -> French",
                "cluknomx" => "English -> Norwegian",
                "cluksvmx" => "English -> Swedish",
                "clukuk" => "English -> English",
            );
            foreach ($langMap as $k => $v) {
                echo "<option value='$k'>$v</option>";
            }
        ?>
    </select>

	<div id="result">Search results</div>
    <?php

    ?>


	<br/>
</body>
</html>
