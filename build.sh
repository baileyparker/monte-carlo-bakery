#!/bin/sh

pandoc --webtex -f markdown -t html README.md.raw | pandoc -f html -t markdown -o README.md
