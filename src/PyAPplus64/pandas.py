# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Pandas Interface für PyAPplus64."""

from typing import Annotated as Ann
import pandas as pd # type: ignore
from pandas._typing import AggFuncType, FilePath, WriteExcelBuffer # type: ignore
import sqlalchemy
import traceback
from .applus import APplusServer
from .applus import sql_utils
from typing import *


def createSqlAlchemyEngine(server : APplusServer) -> sqlalchemy.Engine:
    """Erzeugt eine SqlAlchemy-Engine für die Verbindung zur DB."""
    return sqlalchemy.create_engine(sqlalchemy.engine.URL.create("mssql+pyodbc", query={"odbc_connect": server.db_settings.getConnectionString()}))


def pandasReadSql(
        server : APplusServer, 
        sql : sql_utils.SqlStatement, 
        raw:bool=False, 
        engine:Optional[sqlalchemy.Engine]=None) -> pd.DataFrame:    
    """Wrapper für pd.read_sql für sqlalchemy-engine.
    
    :param server: APplusServer für Datenbankverbindung und complete-SQL
    :type server: APplusServer
    :param sql: das SQL-statement
    """

    if engine is None:
        engine = createSqlAlchemyEngine(server);
    with engine.connect() as conn:
        return pd.read_sql(sqlalchemy.text(server.completeSQL(sql, raw=raw)), conn)


def _createHyperLinkGeneral(genOrg : Callable[[], str|int|float], genLink: Callable[[], str]) -> str|int|float:
    """
    Hilfsfunktion zum Generieren eines Excel-Links.
    
    :param genLink: Funktion, die  Parameter aufgerufen wird und einen Link generiert    
    """
    org:str|int|float=""
    org2:str|int|float
    try:           
        org = genOrg();
        if not org:
            return org
        else :
            if isinstance(org, (int, float)):
                org2 = org;
            else:
                org2 = "\""  + str(org).replace("\"", "\"\"") + "\""

            return "=HYPERLINK(\"{}\", {})".format(genLink(), org2)
    except:
        msg = traceback.format_exc();
        print ("Exception: {}".format(msg))
        return org


def mkDataframeColumn(df : pd.DataFrame, makeValue : AggFuncType) -> pd.Series:    
    """
    Erzeugt für alle Zeilen eines Dataframes eine neuen Wert. Dies wird benutzt, um eine Spalte zu berechnen.
    Diese kann eine Originalspalte ersetzen, oder neu hinzugefügt werden.
    
    :param df: der Dataframe
    :param makeValue: Funktion, die eine Zeile als Parameter bekommt und den neuen Wert berechnet
    """
    def mkValueWrapper(r): # type: ignore
        try:
            return makeValue(r)
        except:
            msg = traceback.format_exc();
            print ("Exception: {}".format(msg))
            return ""

    if (len(df.index) > 0):
        return df.apply(mkValueWrapper, axis=1)
    else:
        return df.apply(lambda r: "", axis=1);


def mkHyperlinkDataframeColumn(df : pd.DataFrame, makeOrig : AggFuncType, makeLink : Callable[[Any], str]) -> pd.Series :    
    """
    Erzeugt für alle Zeilen eines Dataframes einen Hyperlink. Dies wird benutzt, um eine Spalte mit einem Hyperlink zu berechnen.
    Diese kann eine Originalspalte ersetzen, oder neu hinzugefügt werden.
    
    :param df: der Dataframe
    :param makeOrig: Funktion, die eine Zeile als Parameter bekommt und den Wert berechnet, der angezeigt werden soll
    :param makeLink: Funktion, die eine Zeile als Parameter bekommt und den Link berechnet
    """
    if (len(df.index) > 0):
        return df.apply(lambda r: _createHyperLinkGeneral(lambda : makeOrig(r), lambda : makeLink(r)), axis=1)
    else:
        return df.apply(lambda r: "", axis=1);


def exportToExcel(
        filename:FilePath | WriteExcelBuffer | pd.ExcelWriter, 
        dfs : Sequence[Tuple[pd.DataFrame, str]], 
        addTable:bool=True) -> None:
    """
    Schreibt eine Menge von Dataframes in eine Excel-Tabelle
    
    :param filename: Name der Excel-Datei 
    :param dfs: Liste von Tupeln aus DataFrames und Namen von Sheets.
    """
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:  
        for (df, name) in dfs:
            df.to_excel(writer, sheet_name=name, index=False, header=True)
            ws = writer.sheets[name]

            # Table
            if addTable:
                (max_row, max_col) = df.shape
                if max_row > 0 and max_col > 0:
                    column_settings = [{'header': column} for column in df.columns]
                    ws.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

            # Spaltenbreiten anpassen
            ws.autofit();


