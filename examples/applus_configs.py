# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import pathlib
from PyAPplus64.applus import APplusServerConfigDescription

basedir = basedir = pathlib.Path(__file__) # Adapt to your needs
configdir = basedir.joinpath("config")

serverConfYamlDeploy = configdir.joinpath("applus-server-deploy.yaml")
serverConfYamlTest = configdir.joinpath("applus-server-test.yaml")
serverConfYamlProd = configdir.joinpath("applus-server-prod.yaml")


serverConfDescProdEnv1 = APplusServerConfigDescription("Prod/Env1", serverConfYamlProd, env="Env1")
serverConfDescProdEnv2 = APplusServerConfigDescription("Prod/Env2", serverConfYamlProd, env="Env2")
serverConfDescTestEnv1 = APplusServerConfigDescription("Test/Env1", serverConfYamlTest, env="Env1")
serverConfDescTestEnv2 = APplusServerConfigDescription("Test/Env2", serverConfYamlTest, env="Env2")
serverConfDescDeploy = APplusServerConfigDescription("Deploy", serverConfYamlDeploy)

serverConfDescs = [
  serverConfDescProdEnv1,
  serverConfDescProdEnv2,
  serverConfDescTestEnv1,
  serverConfDescTestEnv2,
  serverConfDescDeploy
]