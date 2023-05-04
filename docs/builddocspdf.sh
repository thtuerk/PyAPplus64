#!/bin/sh
##
## Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
##
## This file is part of PyAPplus64.
##

sphinx-apidoc -T -f ../src/PyAPplus64 -o source/generated
sphinx-build -a -E -b latex source build/pdf
cd build/pdf
pdflatex pyapplus64.tex
pdflatex pyapplus64.tex


