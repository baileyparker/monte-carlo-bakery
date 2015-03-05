#!/bin/sh

pandoc --webtex -f markdown -t html README.md.raw | pandoc -f html -t markdown | perl -p -000 -e 's/\\\n!\[(?:.|\n)*?\]\(([^ ]+) "([^\"]+)"\)\\\n/\n\n<p align="center">\n\n<img src="$1" alt="$2">\n\n<\/p>\n\n/' > README.md
