#!/bin/sh

sphinx-apidoc -T -f ../src/PyAPplus64 -o source/generated
sphinx-build -a -E -b html source build/html
