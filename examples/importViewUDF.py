# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import PySimpleGUI as sg  # type: ignore
import pathlib
import PyAPplus64
from PyAPplus64 import applus
from PyAPplus64 import sql_utils
import applus_configs
import traceback
import pathlib
import sys

def importViewsUDFs(server, views, udfs, dbanpass):
  res = ""
  try:    
    if views or udfs:
      for env in server.scripttool.getAllEnvironments():
        res = res + server.importUdfsAndViews(env, views, udfs);
        res = res + "\n\n";

    for xml in dbanpass:
      res = res + "Verarbeite " + xml + "\n"
      xmlRes = server.updateDatabase(xml);
      if (xmlRes == ""): xmlRes = "OK";
      res = res + xmlRes
      res = res + "\n\n"

    sg.popup_scrolled("Importiere", res)
  except:
    sg.popup_error("Fehler", traceback.format_exc())

def importIntoSystem(server, system):
  try:
    if (len(sys.argv) < 2):
      sg.popup_error("Keine Datei zum Import übergeben")
      return

    views = []
    udfs = []
    dbanpass = []
    errors = ""


    for i in range (1, len(sys.argv)):
      arg = pathlib.Path(sys.argv[i])
      if arg == server.scripttool.getInstallPathAppServer().joinpath("Database", "View", arg.stem + ".sql"):
        views.append(arg.stem)
      elif arg == server.scripttool.getInstallPathAppServer().joinpath("Database", "UDF", arg.stem + ".sql"):
        udfs.append(arg.stem)
      elif arg == server.scripttool.getInstallPathAppServer().joinpath("DBChange", arg.stem + ".xml"):
        dbanpass.append(arg.stem + ".xml")
      else:
        errors = errors + "  - " + str(arg) + "\n";

    if len(errors) > 0:
      msg = "Folgende Dateien sind keine View, UDF oder DB-Anpass-Dateien des "+system+"-Systems:\n" + errors;
      sg.popup_error("Fehler", msg);
    if views or udfs or dbanpass:
      importViewsUDFs(server, views, udfs, dbanpass)
      
  except:
    sg.popup_error("Fehler", traceback.format_exc())

if __name__ == "__main__":
  server = PyAPplus64.applusFromConfigFile(applus_configs.serverConfYamlDeploy)
  importIntoSystem(server, "Deploy");
  


