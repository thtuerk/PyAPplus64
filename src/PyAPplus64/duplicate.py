# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

"""
Dupliziert ein oder mehrere APplus Business-Objekte
"""

from . import sql_utils
from . import applus_db
from . import applus_usexml
from .applus import APplusServer
import pyodbc # type: ignore
import traceback
import logging
from typing import *

logger = logging.getLogger(__name__);

noCopyFields = sql_utils.normaliseDBfieldSet({"INSUSER", "UPDDATE", "TIMESTAMP", "MANDANT", "GUID", "ID", "TIMESTAMP_A", "INSDATE", "ID_A", "UPDUSER"})
"""Menge von Feld-Namen, die nie kopiert werden sollen."""


def getFieldsToCopyForTable(server : APplusServer, table : str, force:bool=True) -> Set[str]:
    """
    Bestimmt die für eine Tabelle zu kopierenden Spalten. Dazu wird in den XML-Definitionen geschaut.
    Ist dort 'include' hinterlegt, werden diese Spalten verwendet. Ansonsten alle nicht generierten Spalten, 
    ohne die 'exclude' Spalten. In jedem Fall werden Spalten wie "ID", die nie kopiert werden sollten, entfernt.
    """

    xmlDefs = server.scripttool.getXMLDefinitionObj(table)
    fields : Set[str]
    if (xmlDefs is None):
        if not force:
            raise Exception ("Keine XML-Definitionen für '{}' gefunden".format(table));
        (fields, excl) = (set(), True)
    else: 
        (fields, excl) = xmlDefs.getDuplicate()
    if not excl: 
        return fields.difference(noCopyFields)

    allFields = server.getTableFields(table, isComputed=False)
    return allFields.difference(fields).difference(noCopyFields);



class FieldsToCopyForTableCache():
    """
    Cache für welche Felder für welche Tabelle kopiert werden sollen
    """
    
    def __init__(self, server : APplusServer) -> None:
        self.server = server
        self.cache : Dict[str, Set[str]]= {}

    def getFieldsToCopyForTable(self, table : str) -> Set[str]:
        """
        Bestimmt die für eine Tabelle zu kopierenden Spalten. Dazu wird in den XML-Definitionen geschaut.
        Ist dort 'include' hinterlegt, werden diese Spalten verwendet. Ansonsten alle nicht generierten Spalten, 
        ohne die 'exclude' Spalten. In jedem Fall werden Spalten wie "ID", die nie kopiert werden sollten, entfernt.
        """
        if (table is None):
            return None
        
        t = table.upper()
        fs = self.cache.get(t, None)
        if not (fs is None):
            return fs
        else:
            fs = getFieldsToCopyForTable(self.server, t)
            self.cache[t] = fs
            return fs


def initFieldsToCopyForTableCacheIfNeeded(server : APplusServer, cache : Optional[FieldsToCopyForTableCache]) -> FieldsToCopyForTableCache:
    """
    Hilfsfunktion, die einen Cache erzeugt, falls dies noch nicht geschehen ist.
    """
    if cache is None:
        return FieldsToCopyForTableCache(server)
    else:
        return cache;


class DuplicateBusinessObject():
    """
    Klasse, die alle Daten zu einem BusinessObject speichert und zum Duplizieren dieses Objektes dient.
    Dies beinhaltet Daten zu abhängigen Objekten sowie die Beziehung zu diesen Objekten. Zu einem Artikel
    wird z.B. der Arbeitsplan gespeichert, der wiederum Arbeitsplanpositionen enthält. Als Beziehung ist u.a.
    hinterlegt, dass das Feld "APLAN" der Arbeitsplans dem Feld "ARTIKEL" des Artikels entsprechen muss und dass
    "APLAN" aus den Positionen, "APLAN" aus dem APlan entsprichen muss. So kann beim Duplizieren ein 
    anderer Name des Artikels gesetzt werden und automatisch die Felder der abhängigen Objekte angepasst werden.
    Einige Felder der Beziehung sind dabei statisch, d.h. können direkt aus den zu speichernden Daten abgelesen werden.
    Andere Felder sind dynamisch, d.h. das Parent-Objekt muss in der DB angelegt werden, damit ein solcher dynamischer Wert erstellt 
    und geladen werden kann. Ein typisches Beispiel für ein dynamisches Feld ist "GUID".
    """

    def __init__(self, table : str, fields : Dict[str, Any], fieldsNotCopied:Dict[str, Any]={}, allowUpdate:bool=False) -> None:
        self.table = table
        """für welche Tabelle ist das BusinessObject"""

        self.fields = fields        
        """die Daten"""

        self.fieldsNotCopied = fieldsNotCopied
        """Datenfelder, die im Original vorhanden sind, aber nicht kopiert werden sollen"""
    
        self.dependentObjs : List[Dict[str, Any]] = []
        """Abhängige Objekte"""

        self.allowUpdate = allowUpdate
        """Erlaube Updates statt Fehlern, wenn Objekt schon in DB existiert"""

    def addDependentBusinessObject(self, dObj : Optional['DuplicateBusinessObject'], *args : Tuple[str, str]) -> None:
        """
        Fügt ein neues Unterobjekt zum DuplicateBusinessObject hinzu.
        Dabei handelt es sich selbst um ein DuplicateBusinessObject, das zusammen mit dem
        Parent-Objekt dupliziert werden sollen. Zum Beispiel sollen zu einem 
        Auftrag auch die Positionen dupliziert werden.
        Zusätzlich zum Objekt selbst können mehrere (keine, eine oder viele)
        Paare von Feldern übergeben werden. Ein Paar ("pf", "sf") verbindet das
        Feld "pf" des Parent-Objekts mit dem Feld "sf" des Sub-Objekts. So ist es möglich,
        Werte des Parent-Objekts zu ändern und diese Änderungen für Sub-Objekte zu übernehmen.
        Üblicherweise muss zum Beispiel die Nummer des Hauptobjekts geändert werden. Die
        gleiche Änderung ist für alle abhängigen  Objekte nötig, damit die neuen Objekte sich auf das
        Parent-Objekt beziehen.

        :param dObj: das Unter-Objekt
        :type dObj: DuplicateBusinessObject
        :param args: Liste von Tupeln, die Parent- und Sub-Objekt-Felder miteinander verbinden
        """
        if (dObj is None):
            return 

        args2= {}
        for f1, f2 in args:
            args2[sql_utils.normaliseDBfield(f1)] = sql_utils.normaliseDBfield(f2)
        
        self.dependentObjs.append({
                "dependentObj" : dObj,
                "connection" : args2
            })

    def getField(self, field:str, onlyCopied:bool=False) -> Any:
        """
        Schlägt den Wert eines Feldes nach. Wenn onlyCopied gesetzt ist, werden nur Felder zurückgeliefert, die auch kopiert 
        werden sollen.
        """

        f = sql_utils.normaliseDBfield(field)
        if (f in self.fields):
            return self.fields[f]

        if (not onlyCopied) and (f in self.fieldsNotCopied):
            return self.fieldsNotCopied[f]
        
        return None

    def insert(self, server : APplusServer) -> applus_db.DBTableIDs:
        """
        Fügt alle Objekte zur DB hinzu. Es wird die Menge der IDs der erzeugten
        Objekte gruppiert nach Tabellen erzeugt. Falls ein Datensatz schon
        existiert, wird dieser entweder aktualisiert oder eine Fehlermeldung
        geworfen. Geliefert wird die Menge aller Eingefügten Objekte mit ihrer ID.
        """
        
        res = applus_db.DBTableIDs()

        def insertDO(do : 'DuplicateBusinessObject') -> Optional[int]:
            nonlocal res
            insertRow : applus_usexml.UseXmlRow
            if do.allowUpdate:                
                insertRow = server.mkUseXMLRowInsertOrUpdate(do.table);
            else:
                insertRow = server.mkUseXMLRowInsert(do.table);

            for f, v in do.fields.items():
                insertRow.addField(f, v)
            
            try:
                id = insertRow.exec()
                res.add(do.table, id)
                return id
            except:
                msg = traceback.format_exc();
                logger.error("Exception inserting BusinessObjekt: %s\n%s", str(insertRow), msg)
                return None

        def insertDep(do : 'DuplicateBusinessObject', doID : int, so : 'DuplicateBusinessObject', connect : Dict[str,str]) -> None:
            nonlocal res

            # Abbruch, wenn do nicht eingefügt wurde
            if (doID is None):
                return

            # copy known fields of connect
            connectMissing = {}
            for fd, fs in connect.items():
                if fd in do.fields:
                    so.fields[fs] = do.fields[fd]
                else:
                    connectMissing[fd] = fs
            
            # load missing fields from DB
            if len(connectMissing) > 0:
                sql = sql_utils.SqlStatementSelect(do.table);
                sql.where.addConditionFieldEq("id", doID)
                for fd in connectMissing:
                    sql.addFields(fd)

                rd = server.dbQuerySingleRowDict(sql)
                if not (rd is None):
                    for fd, fs in connectMissing.items():
                        so.fields[fs] = rd[fd]

            # real insert
            id = insertDO(so)
            if not (id is None):
                insertDeps(so, id)


        def insertDeps(do : 'DuplicateBusinessObject', doID : int) -> None:
            for so in do.dependentObjs:
                insertDep(do, doID, so["dependentObj"], so["connection"])
        
        topID = insertDO(self)
        if not (topID is None):
            insertDeps(self, topID)

        return res


    def setFields(self, upds : Dict[str, Any]) -> None:
        """
        Setzt Felder des DuplicateBusinessObjektes und falls nötig seiner Unterobjekte.
        So kann zum Beispiel die Nummer vor dem Speichern geändert werden.

        :param upds: Dictionary mit zu setzenden Werten
        """

        def setFieldsInternal(dobj : 'DuplicateBusinessObject', upds : Dict[str, Any]) -> None:
            # setze alle Felder des Hauptobjekts
            for f, v in upds.items():
                dobj.fields[f] = v
            
            # verarbeite alle Subobjekte
            for su in dobj.dependentObjs:
                subupds = {}
                for fp, fs in su["connection"].items():
                    if fp in upds:
                        subupds[fs] = upds[fp]
                setFieldsInternal(su["dependentObj"], subupds)
            

        updsNorm : Dict[str, Any] = {}
        for f, v in upds.items():
            updsNorm[sql_utils.normaliseDBfield(f)] = v
        setFieldsInternal(self, updsNorm)



def _loadDBDuplicateBusinessObjectDict(
        server : APplusServer, 
        table : str, 
        row : pyodbc.Row, 
        cache:Optional[FieldsToCopyForTableCache]=None, 
        allowUpdate:bool=False) -> Optional[DuplicateBusinessObject]:
    """
    Hilfsfunktion, die ein DuplicateBusinessObjekt erstellt. Die Daten stammen aus
    einer PyOdbc Zeile. So ist es möglich, mit nur einem SQL-Statement,
    mehrere DuplicateBusinessObjekte zu erstellen. 

    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :param table: Tabelle für das neue DuplicateBusinessObjekt
    :param row: die Daten als PyODBC Zeile
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :return: das neue DuplicateBusinessObject
    """
    table = table.upper();

    def getFieldsToCopy() -> Set[str]:
        if cache is None:
            return getFieldsToCopyForTable(server, table)
        else: 
            return cache.getFieldsToCopyForTable(table)
        

    def getFields() -> Tuple[Dict[str, Any], Dict[str, Any]]:
        ftc = getFieldsToCopy()
        fields = {}   
        fieldsNotCopied = {}
        for f, v in applus_db.row_to_dict(row).items():
            f = sql_utils.normaliseDBfield(f);
            if f in ftc:
                fields[f] = v
            else:
                fieldsNotCopied[f] = v
        return (fields, fieldsNotCopied)

    
    if (row is None):
        return None

    (fields, fieldsNotCopied) = getFields()   
    return DuplicateBusinessObject(table, fields, fieldsNotCopied=fieldsNotCopied, allowUpdate=allowUpdate)


def loadDBDuplicateBusinessObject(
        server : APplusServer, 
        table : str, 
        cond : sql_utils.SqlCondition, 
        cache : Optional[FieldsToCopyForTableCache]=None, 
        allowUpdate : bool = False) -> Optional[DuplicateBusinessObject]:
    """
    Läd ein einzelnes DuplicateBusinessObjekt aus der DB. Die Bedingung sollte dabei
    einen eindeutigen Datensatz auswählen. Werden mehrere zurückgeliefert, wird ein 
    zufälliger ausgewählt. Wird kein Datensatz gefunden, wird None geliefert.

    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param table: Tabelle für das neue DuplicateBusinessObjekt
    :type table: str
    :param cond: SQL-Bedingung zur Auswahl eines Objektes
    :type cond: sql_utils.SqlCondition
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :param allowUpdate: ist Update statt Insert erlaubt?
    :type allowUpdate: bool
    :return: das neue DuplicateBusinessObject
    :rtype: Optional[DuplicateBusinessObject]
    """
    table = table.upper();

    def getRow() -> pyodbc.Row:    
        sql = sql_utils.SqlStatementSelect(table)
        sql.setTop(1)
        sql.where.addCondition(cond);
        return server.dbQuerySingleRow(sql)

    return _loadDBDuplicateBusinessObjectDict(server, table, getRow(), cache=cache, allowUpdate=allowUpdate);

def loadDBDuplicateBusinessObjectSimpleCond(
        server : APplusServer, 
        table : str, 
        field : str, 
        value : Optional[Union[sql_utils.SqlValue, bool]], 
        cache : Optional[FieldsToCopyForTableCache]=None, 
        allowUpdate : bool = False) -> Optional[DuplicateBusinessObject]:              
    """
    Wrapper für loadDBDuplicateBusinessObject, das eine einfache Bedingung benutzt,
    bei der ein Feld einen bestimmten Wert haben muss.

    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param table: Tabelle für das neue DuplicateBusinessObjekt
    :type table: str
    :param field: Feld für Bedingung
    :type field: str
    :param value: Wert des Feldes für Bedingung
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :return: das neue DuplicateBusinessObject
    :rtype: Optional[DuplicateBusinessObject]
    """
    cond = sql_utils.SqlConditionFieldEq(field, value)
    return loadDBDuplicateBusinessObject(server, table, cond, cache=cache, allowUpdate=allowUpdate)
    

def loadDBDuplicateBusinessObjects(
        server : APplusServer, 
        table : str, 
        cond : sql_utils.SqlCondition, 
        cache : Optional[FieldsToCopyForTableCache]=None, 
        allowUpdate : bool = False) -> Sequence[DuplicateBusinessObject]:
    """
    Läd eine Liste von DuplicateBusinessObjekten aus der DB. Die Bedingung kann mehrere Datensätze auswählen.

    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param table: Tabelle für das neue DuplicateBusinessObjekt
    :type table: str
    :param cond: SQL-Bedingung zur Auswahl eines Objektes
    :type cond: sql_utils.SqlCondition
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :return: Liste der neuen DuplicateBusinessObjects
    :rtype: Sequence[DuplicateBusinessObject]
    """
    table = table.upper()
    cache = initFieldsToCopyForTableCacheIfNeeded(server, cache)

    def processRow(r : pyodbc.Row) -> Optional[DuplicateBusinessObject]:
        return _loadDBDuplicateBusinessObjectDict(server, table, r, cache=cache, allowUpdate=allowUpdate)        
    
    sql = sql_utils.SqlStatementSelect(table)
    sql.where.addCondition(cond)
    return server.dbQueryAll(sql, apply=processRow)
    
def loadDBDuplicateBusinessObjectsSimpleCond(
        server : APplusServer, 
        table : str, 
        field : str, 
        value : Optional[Union[sql_utils.SqlValue, bool]], 
        cache : Optional[FieldsToCopyForTableCache]=None, 
        allowUpdate : bool = False) -> Sequence[DuplicateBusinessObject]:
    """
    Wrapper für loadDBDuplicateBusinessObjects, das eine einfache Bedingung benutzt,
    bei der ein Feld einen bestimmten Wert haben muss.

    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param table: Tabelle für das neue DuplicateBusinessObjekt
    :type table: str
    :param field: Feld für Bedingung
    :param value: Wert des Feldes für Bedingung
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :return: Liste der neuen DuplicateBusinessObjects
    :rtype: Sequence[DuplicateBusinessObject]
    """
    cond = sql_utils.SqlConditionFieldEq(field, value)
    return loadDBDuplicateBusinessObjects(server, table, cond, cache=cache, allowUpdate=allowUpdate)
    

# Im Laufe der Zeit sollten load-Funktionen für verschiedene BusinessObjekte
# erstellt werden. Dies erfolgt immer, wenn eine solche Funktion wirklich
# benutzt werden soll

def loadDBDuplicateAPlan(
        server : APplusServer, 
        aplan : str, 
        cache:Optional[FieldsToCopyForTableCache]=None) -> Optional[DuplicateBusinessObject]:
    """
    Erstelle DuplicateBusinessObject für einzelnen Arbeitsplan. 
    
    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param aplan: Aplan, der kopiert werden soll.
    :type aplan: str
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :return: das neue DuplicateBusinessObject
    :rtype: DuplicateBusinessObject
    """

    cache = initFieldsToCopyForTableCacheIfNeeded(server, cache);
    boMain = loadDBDuplicateBusinessObjectSimpleCond(server, "aplan", "APLAN", aplan, cache=cache)
    if boMain is None:
        return None

    for so in loadDBDuplicateBusinessObjectsSimpleCond(server, "aplanpos", "APLAN", aplan, cache=cache):
        boMain.addDependentBusinessObject(so, ("aplan", "aplan"))
    
    return boMain


def loadDBDuplicateStueli(server : APplusServer, stueli : str, cache:Optional[FieldsToCopyForTableCache]=None) -> Optional[DuplicateBusinessObject]:
    """
    Erstelle DuplicateBusinessObject für einzelne Stückliste. 
    
    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param stueli: Stückliste, die kopiert werden soll.
    :type stueli: str
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :return: das neue DuplicateBusinessObject
    :rtype: Optional[DuplicateBusinessObject]
    """

    cache = initFieldsToCopyForTableCacheIfNeeded(server, cache);
    boMain = loadDBDuplicateBusinessObjectSimpleCond(server, "stueli", "stueli", stueli, cache=cache)
    if boMain is None:
        return None

    for so in loadDBDuplicateBusinessObjectsSimpleCond(server, "stuelipos", "stueli", stueli, cache=cache):
        boMain.addDependentBusinessObject(so, ("stueli", "stueli"))
    
    return boMain

def addSachgruppeDependentObjects(
        do : DuplicateBusinessObject, 
        server : APplusServer, 
        cache:Optional[FieldsToCopyForTableCache]=None) -> None:
    """
    Fügt Unterobjekte hinzu, die die Sachgruppenwerte kopieren.

    :param do: zu erweiterndes DuplicateBusinessObject
    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    """

    cache = initFieldsToCopyForTableCacheIfNeeded(server, cache);
    klasse = do.fields.get(sql_utils.normaliseDBfield("SACHGRUPPENKLASSE"), None)
    if (klasse == None):
        # keine Klasse gesetzt, nichts zu kopieren
        return 

    # bestimme alle Gruppen
    def loadGruppen() -> Sequence[str]:
        sql = sql_utils.SqlStatementSelect("sachgruppenklassepos", "sachgruppe")
        sql.where.addConditionFieldEq("sachgruppenklasse", klasse)
        sql.where.addConditionFieldEq("tabelle", do.table)
        return server.dbQueryAll(sql, apply=lambda r: r.sachgruppe)

    gruppen = loadGruppen();

    # Gruppe bearbeiten
    def processGruppen() -> None:
        cond = sql_utils.SqlConditionAnd()
        cond.addConditionFieldEq("tabelle", do.table)
        cond.addConditionFieldEq("instanzguid", do.getField("guid"))
        cond.addConditionFieldEq("sachgruppenklasse", klasse)
        cond.addConditionFieldIn("sachgruppe", gruppen)
        cond.addConditionFieldStringNotEmpty("wert")

        for so in loadDBDuplicateBusinessObjects(server, "sachwert", cond, cache=cache, allowUpdate=True):
            do.addDependentBusinessObject(so, ("guid", "instanzguid"))


    processGruppen()
    


def loadDBDuplicateArtikel(
        server : APplusServer, 
        artikel : str, 
        cache:Optional[FieldsToCopyForTableCache]=None,
        dupAplan:bool=True, 
        dupStueli:bool=True) -> Optional[DuplicateBusinessObject]:

    """
    Erstelle DuplicateBusinessObject für einzelnen Artikel. 
    
    :param server: Verbindung zum APP-Server, benutzt zum Nachschlagen der zu kopierenden Felder
    :type server: APplusServer
    :param artikel: Artikel, der kopiert werden soll
    :type artikel: str
    :param cache: Cache, so dass benötigte Felder nicht immer wieder neu berechnet werden müssen 
    :type cache: Optional[FieldsToCopyForTableCache]
    :param dupAplan: Arbeitsplan duplizieren?
    :type dupAplan: bool optional
    :param dupStueli: Stückliste duplizieren?
    :type dupStueli: bool optional
    :return: das neue DuplicateBusinessObject
    :rtype: DuplicateBusinessObject
    """

    cache = initFieldsToCopyForTableCacheIfNeeded(server, cache);
    boArt = loadDBDuplicateBusinessObjectSimpleCond(server, "artikel", "ARTIKEL", artikel, cache=cache)
    if boArt is None:
        return None
    addSachgruppeDependentObjects(boArt, server, cache=cache)

    if dupAplan:
        boAplan = loadDBDuplicateAPlan(server, artikel, cache=cache)
        boArt.addDependentBusinessObject(boAplan, ("artikel", "aplan"))
    
    if dupStueli:
        boStueli = loadDBDuplicateStueli(server, artikel, cache=cache)
        boArt.addDependentBusinessObject(boStueli, ("artikel", "stueli"))

    return boArt
