# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

# Einfaches Script, das verschiedene Werte des Servers ausliest.
# Dies sind SysConfig-Einstellungen, aber auch der aktuelle Mandant,
# Systemnamen, ...

import pathlib
import PyAPplus64
import applus_configs
from typing import Optional, Union


def main(confFile: Union[str, pathlib.Path], user: Optional[str] = None, env: Optional[str] = None) -> None:
    server = PyAPplus64.applusFromConfigFile(confFile, user=user, env=env)

    print("\n\nSysConf Lookups:")

    print("  Default Auftragsart:", server.sysconf.getString("STAMM", "DEFAULTAUFTRAGSART"))
    print("  Auftragsarten:")
    arten = server.sysconf.getList("STAMM", "AUFTRAGSART", sep='\n')
    if not arten:
        arten = []
    for a in arten:
        print("    - " + a)

    print("  Firmen-Nr. automatisch vergeben:", server.sysconf.getBoolean("STAMM", "FIRMAAUTOMATIK"))
    print("  Anzahl Artikelstellen:", server.sysconf.getInt("STAMM", "ARTKLASSIFNRLAENGE"))

    print("\n\nScriptTool:")

    print("  CurrentDate:", server.scripttool.getCurrentDate())
    print("  CurrentTime:", server.scripttool.getCurrentTime())
    print("  CurrentDateTime:", server.scripttool.getCurrentDateTime())
    print("  LoginName:", server.scripttool.getLoginName())
    print("  UserName:", server.scripttool.getUserName())
    print("  UserFullName:", server.scripttool.getUserFullName())
    print("  SystemName:", server.scripttool.getSystemName())
    print("  Mandant:", server.scripttool.getMandant())
    print("  MandantName:", server.scripttool.getMandantName())
    print("  InstallPath:", server.scripttool.getInstallPath())
    print("  InstallPathAppServer:", server.scripttool.getInstallPathAppServer())
    print("  InstallPathWebServer:", server.scripttool.getInstallPathWebServer())
    print("  ServerInfo - Version:", server.scripttool.getServerInfo().find("version").text)


if __name__ == "__main__":
    main(applus_configs.serverConfYamlTest)
