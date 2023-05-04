# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import PyAPplus64
import applus_configs
import pathlib

def main(confFile : pathlib.Path, outfile : str) -> None:
    server = PyAPplus64.applus.applusFromConfigFile(confFile) 

    # Einfache SQL-Anfrage 
    sql1 = ("select Material, count(*) as Anzahl from ARTIKEL "
            "group by MATERIAL having MATERIAL is not null "
            "order by Anzahl desc")
    df1 = PyAPplus64.pandas.pandasReadSql(server, sql1)

    # Sql Select-Statements können auch über SqlStatementSelect zusammengebaut
    # werden. Die ist bei vielen, komplizierten Bedingungen teilweise hilfreich.
    sql2 = PyAPplus64.SqlStatementSelect("ARTIKEL")        
    sql2.addFields("Material", "count(*) as Anzahl")
    sql2.addGroupBy("MATERIAL")
    sql2.having.addConditionFieldIsNotNull("MATERIAL")
    sql2.order = "Anzahl desc"
    df2 = PyAPplus64.pandas.pandasReadSql(server, sql2)

    # Ausgabe als Excel mit 2 Blättern
    PyAPplus64.pandas.exportToExcel(outfile, [(df1, "Materialien"), (df2, "Materialien 2")], addTable=True)


if __name__ == "__main__":
    main(applus_configs.serverConfYamlTest, "myout.xlsx")