#!/bin/bash
# This file is part of account_stock_cos module.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license

LANGS=(
    "en"
    "es"
)

FILE_NAME="minimal_chart"
XSL="localize.xsl"

rm -f $FILE_NAME"_"*.xml
for lang in ${LANGS[@]}; do
    echo "Creating" $FILE_NAME"_"$lang.xml "..."
    xsltproc -o $FILE_NAME"_"$lang.xml --stringparam lang $lang $XSL $FILE_NAME.xml
done
echo "Done!"
