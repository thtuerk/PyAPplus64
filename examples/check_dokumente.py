# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import pathlib
import PyAPplus64
import applus_configs

def main(confFile : pathlib.Path, docDir:str, updateDB:bool) -> None:
  server = PyAPplus64.applus.applusFromConfigFile(confFile) 

  sql = PyAPplus64.sql_utils.SqlStatementSelect("ARTIKEL");
  sql.addFields("ID", "ARTIKEL", "DOCUMENTS");
  sql.where.addConditionFieldStringNotEmpty("DOCUMENTS");

  for row in server.dbQueryAll(sql):
    doc = pathlib.Path(docDir + row.DOCUMENTS);
    if not doc.exists():
        print("Bild '{}' für Artikel '{}' nicht gefunden".format(doc, row.ARTIKEL))
        
        if updateDB:
              upd = server.mkUseXMLRowUpdate("ARTIKEL", row.ID);
              upd.addField("DOCUMENTS", None);
              upd.update();

if __name__ == "__main__":
  main(applus_configs.serverConfYamlTest, "somedir\\WebServer\\DocLib", False)