#!/bin/sh

mkdir -p jsons

#for file in json/*.json; do
for file in json/clnono.json; do
    newfile=`echo $file | sed s/json/jsons/`
    echo $file
    cat $file | js sortjson-out.js > $newfile &
    echo index
    cat $file | js sortjson-idx.js > $newfile.idx
done
