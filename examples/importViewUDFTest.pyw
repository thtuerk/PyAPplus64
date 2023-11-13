# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import importViewUDF
import applus_configs
import PyAPplus64

if __name__ == "__main__":
  server = PyAPplus64.applusFromConfigFile(applus_configs.serverConfYamlTest)
  importViewUDF.importIntoSystem(server, "Test")
