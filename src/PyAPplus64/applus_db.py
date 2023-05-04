# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

import pyodbc # type: ignore
import logging
from .sql_utils import SqlStatement
from . import sql_utils
from typing import *


logger = logging.getLogger(__name__);

class APplusDBSettings:
    """
    Einstellungen, mit welcher DB sich verbunden werden soll.
    """
    
    def __init__(self, server : str, database : str, user : str, password : str):
        self.server = server
        self.database = database;
        self.user = user
        self.password = password


    def getConnectionString(self) -> str:
        """Liefert den ODBC Connection-String für die Verbindung.
        :return: den Connection-String
        """
        return ("Driver={SQL Server Native Client 11.0};"
                "Server="+self.server+";"
                "Database="+self.database+";"
                "UID="+self.user+";"
                "PWD="+self.password + ";")    

    def connect(self) -> pyodbc.Connection:
        """Stellt eine neue Verbindung her und liefert diese zurück.
        """
        return pyodbc.connect(self.getConnectionString())



def row_to_dict(row : pyodbc.Row) -> Dict[str, Any]:
    """Konvertiert eine Zeile in ein Dictionary"""
    return dict(zip([t[0] for t in row.cursor_description], row))

def _logSQLWithArgs(sql : SqlStatement, *args : Any) -> None:
    if args:
        logger.debug("executing '{}' with args {}".format(str(sql), str(args)))
    else:
        logger.debug("executing '{}'".format(str(sql)))

def rawQueryAll(
        cnxn : pyodbc.Connection,
        sql : SqlStatement, 
        *args : Any, 
        apply : Optional[Callable[[pyodbc.Row], Any]]=None) -> Sequence[Any]:
    """
    Führt eine SQL Query direkt aus und liefert alle Zeilen zurück.
    Wenn apply gesetzt ist, wird die Funktion auf jeder Zeile ausgeführt und das Ergebnis ausgeben, die nicht None sind.
    """
    _logSQLWithArgs(sql, *args)
    with cnxn.cursor() as cursor:
        cursor.execute(str(sql), *args)

        rows = cursor.fetchall();
        if apply is None:
            return rows
        else:
            res = []
            for r in rows:
                rr = apply(r)
                if not (rr == None):
                    res.append(rr)
            return res

def rawQuery(cnxn : pyodbc.Connection, sql : sql_utils.SqlStatement, f : Callable[[pyodbc.Row], None], *args : Any) -> None:
    """Führt eine SQL Query direkt aus und führt für jede Zeile die übergeben Funktion aus."""
    _logSQLWithArgs(sql, *args)
    with cnxn.cursor() as cursor:
        cursor.execute(str(sql), *args)
        for row in cursor:
            f(row);

def rawQuerySingleRow(cnxn : pyodbc.Connection, sql : SqlStatement, *args : Any) -> Optional[pyodbc.Row]:
    """Führt eine SQL Query direkt aus, die maximal eine Zeile zurückliefern soll. Diese Zeile wird geliefert."""
    _logSQLWithArgs(sql, *args)
    with cnxn.cursor() as cursor:
        cursor.execute(str(sql), *args)
        return cursor.fetchone();

def rawQuerySingleValue(cnxn : pyodbc.Connection, sql : SqlStatement, *args : Any) -> Any:
    """Führt eine SQL Query direkt aus, die maximal einen Wert zurückliefern soll. Dieser Wert oder None wird geliefert."""
    _logSQLWithArgs(sql, *args)
    with cnxn.cursor() as cursor:
        cursor.execute(str(sql), *args)
        row = cursor.fetchone();
        if row:
            return row[0];
        else:
            return None;

def getUniqueFieldsOfTable(cnxn : pyodbc.Connection, table : str) -> Dict[str, List[str]] :     
    """
    Liefert alle Spalten einer Tabelle, die eindeutig sein müssen. 
    Diese werden als Dictionary gruppiert nach Index-Namen geliefert. 
    Jeder Eintrag enthält eine Liste von Feldern, die zusammen eindeutig sein 
    müssen.
    """

    sql = sql_utils.SqlStatementSelect("sys.indexes AS i")
    join = sql.addInnerJoin("sys.index_columns AS ic")
    join.on.addCondition("i.OBJECT_ID = ic.OBJECT_ID")
    join.on.addCondition("i.index_id = ic.index_id")
    sql.where.addConditionFieldEq("OBJECT_NAME(ic.OBJECT_ID)", table)
    sql.where.addConditionFieldEq("i.is_unique", True)
    sql.addFields("i.name AS INDEX_NAME", "COL_NAME(ic.OBJECT_ID,ic.column_id) AS COL")
    _logSQLWithArgs(sql)

    indices : Dict[str, List[str]] = {}
    with cnxn.cursor() as cursor:
        cursor.execute(str(sql))
        for row in cursor:
            cols = indices.get(row.INDEX_NAME, [])
            cols.append(sql_utils.normaliseDBfield(row.COL))
            indices[row.INDEX_NAME] = cols
    return indices


class DBTableIDs():
    """Klasse, die Mengen von IDs gruppiert nach Tabellen speichert"""
    
    def __init__(self) -> None:
        self.data : Dict[str, Set[int]]= {}

    def add(self, table:str, *ids : int) -> None:
        """
        fügt Eintrag hinzu
        
        :param table: die Tabelle
        :type table: str
        :param id: die ID
        """
        table = table.upper()
        if not (table in self.data):
            self.data[table] = set(ids);            
        else:
            self.data[table].update(ids)

    def getTable(self, table : str) -> Set[int]:
        """
        Liefert die Menge der IDs für eine bestimmte Tabelle.

        :param table: die Tabelle
        :type table: str
        :return: die IDs        
        """

        table = table.upper()
        return self.data.get(table, set())

    def __str__(self) -> str:
        return str(self.data)


