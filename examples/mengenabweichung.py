# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

# Erzeugt Excel-Tabellen mit Werkstattaufträgen und Werkstattauftragspositionen mit Mengenabweichungen

import datetime
import PyAPplus64
import applus_configs
import pandas as pd # type: ignore
import pathlib
from typing import *

def ladeAlleWerkstattauftragMengenabweichungen(
        server:PyAPplus64.APplusServer, 
        cond:PyAPplus64.SqlCondition|str|None=None) -> pd.DataFrame:
    sql = PyAPplus64.sql_utils.SqlStatementSelect("WAUFTRAG w");
    sql.addLeftJoin("personal p", "w.UPDUSER = p.PERSONAL")

    sql.addFieldsTable("w", "ID", "BAUFTRAG", "POSITION")
    sql.addFields("(w.MENGE-w.MENGE_IST) as MENGENABWEICHUNG")
    sql.addFieldsTable("w", "MENGE", "MENGE_IST", 
                       "APLAN as ARTIKEL", "NAME as ARTIKELNAME")
    sql.addFields("w.UPDDATE", "p.NAME as UPDNAME")

    sql.where.addConditionFieldGe("w.STATUS", 5)
    sql.where.addCondition("abs(w.MENGE-w.MENGE_IST) > 0.001")    
    sql.where.addCondition(cond)
    sql.order="w.UPDDATE"
    dfOrg = PyAPplus64.pandas.pandasReadSql(server, sql);

    # Add Links
    df = dfOrg.copy();
    df = df.drop(columns=["ID"]);
    # df = df[['POSITION', 'BAUFTRAG', 'MENGE']] # reorder / filter columns

    df['POSITION'] = PyAPplus64.pandas.mkHyperlinkDataframeColumn(dfOrg, 
                        lambda r: r.POSITION, 
                        lambda r: server.makeWebLinkWauftrag(
                            bauftrag=r.BAUFTRAG, accessid=r.ID))
    df['BAUFTRAG'] = PyAPplus64.pandas.mkHyperlinkDataframeColumn(dfOrg, 
                        lambda r: r.BAUFTRAG, 
                        lambda r: server.makeWebLinkBauftrag(bauftrag=r.BAUFTRAG))

    colNames = {
        "BAUFTRAG" : "Betriebsauftrag",
        "POSITION" : "Pos",
        "MENGENABWEICHUNG" : "Mengenabweichung",
        "MENGE" : "Menge",
        "MENGE_IST" : "Menge-Ist",
        "ARTIKEL" : "Artikel",
        "ARTIKELNAME" : "Artikel-Name",
        "UPDDATE" : "geändert am",
        "UPDNAME" : "geändert von"
    }
    df.rename(columns=colNames, inplace=True);

    return df


def ladeAlleWerkstattauftragPosMengenabweichungen(
        server : PyAPplus64.APplusServer, 
        cond:PyAPplus64.SqlCondition|str|None=None) -> pd.DataFrame:
    sql = PyAPplus64.sql_utils.SqlStatementSelect("WAUFTRAGPOS w");
    sql.addLeftJoin("personal p", "w.UPDUSER = p.PERSONAL")

    sql.addFieldsTable("w", "ID", "BAUFTRAG", "POSITION", "AG")
    sql.addFields("(w.MENGE-w.MENGE_IST) as MENGENABWEICHUNG")
    sql.addFieldsTable("w", "MENGE", "MENGE_IST", "APLAN as ARTIKEL")
    sql.addFields("w.UPDDATE", "p.NAME as UPDNAME")

    sql.where.addConditionFieldEq("w.STATUS", 4)
    sql.where.addCondition("abs(w.MENGE-w.MENGE_IST) > 0.001")    
    sql.where.addCondition(cond)
    sql.order="w.UPDDATE"

    dfOrg = PyAPplus64.pandas.pandasReadSql(server, sql);

    # Add Links
    df = dfOrg.copy();
    df = df.drop(columns=["ID"]);
    df['POSITION'] = PyAPplus64.pandas.mkHyperlinkDataframeColumn(dfOrg, 
                        lambda r: r.POSITION, 
                        lambda r: server.makeWebLinkWauftrag(
                            bauftrag=r.BAUFTRAG, accessid=r.ID))
    df['BAUFTRAG'] = PyAPplus64.pandas.mkHyperlinkDataframeColumn(dfOrg, 
                        lambda r: r.BAUFTRAG, 
                        lambda r: server.makeWebLinkBauftrag(bauftrag=r.BAUFTRAG))
    df['AG'] = PyAPplus64.pandas.mkHyperlinkDataframeColumn(dfOrg, 
                        lambda r: r.AG, 
                        lambda r: server.makeWebLinkWauftragPos(
                            bauftrag=r.BAUFTRAG, position=r.POSITION, accessid=r.ID))
    
    # Demo zum Hinzufügen einer berechneten Spalte
    # df['BAUFPOSAG'] = PyAPplus64.pandas.mkDataframeColumn(dfOrg, 
    #                     lambda r: "{}.{} AG {}".format(r.BAUFTRAG, r.POSITION, r.AG))

    # Rename Columns
    colNames = {
        "BAUFTRAG" : "Betriebsauftrag",
        "POSITION" : "Pos",
        "AG" : "AG",
        "MENGENABWEICHUNG" : "Mengenabweichung",
        "MENGE" : "Menge",
        "MENGE_IST" : "Menge-Ist",
        "ARTIKEL" : "Artikel",
        "UPDDATE" : "geändert am",
        "UPDNAME" : "geändert von"
    }
    df.rename(columns=colNames, inplace=True);
    return df

def computeInYearMonthCond(field : str, year:int|None=None, 
                           month:int|None=None) -> PyAPplus64.SqlCondition | None:
    if not (year is None): 
        if month is None:
            return PyAPplus64.sql_utils.SqlConditionDateTimeFieldInYear(field, year)
        else:
            return PyAPplus64.sql_utils.SqlConditionDateTimeFieldInMonth(field, year, month)
    else:
        return None

def computeFileName(year:int|None=None, month:int|None=None) -> str:
    if year is None: 
        return 'mengenabweichungen-all.xlsx';
    else:
        if month is None:
            return 'mengenabweichungen-{:04d}.xlsx'.format(year);
        else:
            return 'mengenabweichungen-{:04d}-{:02d}.xlsx'.format(year, month);

def _exportInternal(server: PyAPplus64.APplusServer, fn:str, 
                    cond:Union[PyAPplus64.SqlCondition, str, None]) -> int:
    df1 = ladeAlleWerkstattauftragMengenabweichungen(server, cond)
    df2 = ladeAlleWerkstattauftragPosMengenabweichungen(server, cond)
    print ("erzeuge " + fn);
    PyAPplus64.pandas.exportToExcel(fn, [(df1, "WAuftrag"), (df2, "WAuftrag-Pos")], addTable=True)
    return len(df1.index) + len(df2.index)

def exportVonBis(server: PyAPplus64.APplusServer, fn:str, 
                 von:datetime.datetime|None, bis:datetime.datetime|None) -> int:
  cond = PyAPplus64.sql_utils.SqlConditionDateTimeFieldInRange("w.UPDDATE", von, bis)
  return _exportInternal(server, fn, cond)

def exportYearMonth(server: PyAPplus64.APplusServer, 
                    year:int|None=None, month:int|None=None) -> int:
    cond=computeInYearMonthCond("w.UPDDATE", year=year, month=month)
    fn = computeFileName(year=year, month=month)
    return _exportInternal(server, fn, cond)

def computePreviousMonthYear(cyear : int, cmonth :int) -> Tuple[int, int]:
    if cmonth == 1:
        return (cyear-1, 12)
    else:
        return (cyear, cmonth-1);

def computeNextMonthYear(cyear : int, cmonth :int) -> Tuple[int, int]:
    if cmonth == 12:
        return (cyear+1, 1)
    else:
        return (cyear, cmonth+1);

def main(confFile : str|pathlib.Path, user:str|None=None, env:str|None=None) -> None:
    server = PyAPplus64.applusFromConfigFile(confFile, user=user, env=env) 
    
    now = datetime.date.today()
    (cmonth, cyear) = (now.month, now.year)
    (pyear, pmonth) = computePreviousMonthYear(cyear, cmonth);
    
    # Ausgaben    
    exportYearMonth(server, cyear, cmonth) # Aktueller Monat
    exportYearMonth(server, pyear, pmonth) # Vorheriger Monat
    # export(cyear) # aktuelles Jahr
    # export(cyear-1) # letztes Jahr
    # export() # alles

if __name__ == "__main__":
    main(applus_configs.serverConfYamlTest)
