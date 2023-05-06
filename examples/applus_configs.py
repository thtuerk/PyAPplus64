# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import pathlib

basedir = pathlib.Path(__file__)
configdir = basedir.joinpath("config")

serverConfYamlDeploy = configdir.joinpath("applus-server-deploy.yaml")
serverConfYamlTest = configdir.joinpath("applus-server-test.yaml")
serverConfYamlProd = configdir.joinpath("applus-server-prod.yaml")
