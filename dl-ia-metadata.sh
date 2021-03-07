#!/bin/bash

if [ $# -ne 1 ]; then
	echo "usage: dl-ia-metadata.sh TLD"
	echo "\tTLD is a top-level domain"
	exit
fi

curl -Ls "https://web.archive.org/__wb/search/metadata?q=tld:$1" | jq -S .
