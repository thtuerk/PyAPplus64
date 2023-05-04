# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

import lxml.etree as ET # type: ignore
from . import sql_utils
import datetime
from typing import *

if TYPE_CHECKING: 
    from .applus import APplusServer



def _formatValueForXMLRow(v : Any) -> str:
    """Hilfsfunktion zum Formatieren eines Wertes für XML"""
    if (v is None):
        return "";
    if isinstance(v, (int, float)):
        return str(v);
    elif isinstance(v, str):
        return v;
    elif isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    elif isinstance(v, datetime.date):
        return v.strftime("%Y-%m-%d")
    elif isinstance(v, datetime.time):
        return v.strftime("%H:%M:%S.%f")[:-3]
    else:
        return str(v)


class UseXmlRow:
    """
    Klasse, die eine XML-Datei erzeugen kann, die mittels p2core.useXML 
    genutzt werden kann. Damit ist es möglich APplus BusinessObjekte zu
    erzeugen, ändern und zu löschen. Im Gegensatz zu direkten DB-Zugriffen,
    werden diese Anfragen über den APP-Server ausgeführt. Dabei werden
    die von der Weboberfläche bekannten Checks und Änderungen ausgeführt.
    Als sehr einfaches Beispiel wird z.B. INSDATE oder UPDDATE automatisch gesetzt.
    Interessanter sind automatische Änderungen und Checks.

    Bei der Benutzung wird zunächst ein Objekt erzeugt, dann evtl. 
    mittels :meth:`addField` Felder hinzugefügt und schließlich mittels 
    :meth:`exec` an den AppServer übergeben. 
    Normalerweise sollte die Klasse nicht direkt, sondern über Unterklassen
    für das Einfügen, Ändern oder Löschen benutzt werden.

    :param applus: Verbindung zu APplus 
    :type applus: APplusServer
    :param table: die Tabelle
    :type table: str
    :param cmd: cmd-attribut der row, also ob es sich um ein Update, ein Insert oder ein Delete handelt
    :type cmd: str
    """

    def __init__(self, applus : 'APplusServer', table : str, cmd : str) -> None:
        self.applus = applus
        self.table = table
        self.cmd = cmd
        self.fields : Dict[str, Any] = {}

    def __str__(self) -> str:
        return self.toprettyxml() 

    def _buildXML(self) -> ET.Element :
        """Hilfsfunktion, die das eigentliche XML baut"""
        row = ET.Element("row", cmd=self.cmd, table=self.table, nsmap={ "dt" : "urn:schemas-microsoft-com:datatypes"});

        for name, value in self.fields.items():
            child = ET.Element(name)
            child.text = _formatValueForXMLRow(value)
            row.append(child)

        return row


    def toprettyxml(self)->str:
        """
        Gibt das formatierte XML aus. Dieses kann per useXML an den AppServer übergeben werden. 
        Dies wird mittels :meth:`exec` automatisiert.
        """
        return ET.tostring(self._buildXML(), encoding = "unicode", pretty_print=True)

    def getField(self, name:str) -> Any:
        """Liefert den Wert eines gesetzten Feldes"""

        if name is None: 
            return None
        name = sql_utils.normaliseDBfield(name);

        if name in self.fields:
            return self.fields[name]
        elif name == "MANDANT":
            return self.applus.scripttool.getMandant()
        else:
            return None

    def checkFieldSet(self, name:Optional[str]) -> bool:
        """Prüft, ob ein Feld gesetzt wurde"""
        if name is None: 
            return False
        name = sql_utils.normaliseDBfield(name)
        return (name in self.fields) or (name == "MANDANT")

    def checkFieldsSet(self, *names : str) -> bool:
        """Prüft, ob alle übergebenen Felder gesetzt sind"""
        for n in names:
            if not (self.checkFieldSet(n)):
                return False
        return True

    def addField(self, name:str|None, value:Any) -> None:
        """
        Fügt ein Feld zum Row-Node hinzu.

        :param name: das Feld
        :type name: string
        :param value: Wert des Feldes
        """
        if name is None: 
            return
    
        self.fields[sql_utils.normaliseDBfield(name)] = value


    def addTimestampField(self, id:int, ts:Optional[bytes]=None) -> None:
        """
        Fügt ein Timestamp-Feld hinzu. Wird kein Timestamp übergeben, wird mittels der ID der aktuelle 
        Timestamp aus der DB geladen. Dabei kann ein Fehler auftreten.
        Ein Timestamp-Feld ist für Updates und das Löschen nötig um sicherzustellen, dass die richtige
        Version des Objekts geändert oder gelöscht wird. Wird z.B. ein Objekt aus der DB geladen, inspiziert
        und sollen dann Änderungen gespeichert werden, so sollte der Timestamp des Ladens übergeben werden.
        So wird sichergestellt, dass nicht ein anderer User zwischenzeitlich Änderungen vornahm. Ist dies
        der Fall, wird dann bei "exec" eine Exception geworfen.

        :param id: DB-id des Objektes dessen Timestamp hinzugefügt werden soll   
        :type id: string
        :param ts: Fester Timestamp der verwendet werden soll, wenn None wird der Timestamp aus der DB geladen.
        :type ts: bytes
        """
        if ts is None:
            ts = self.applus.dbQuerySingleValue("select timestamp from " + self.table + " where id = ?", id);
        if ts:
            self.addField("timestamp", ts.hex());
        else:
            raise Exception("kein Eintrag in Tabelle '" + self.table + " mit ID " + str(id) + " gefunden")


    def addTimestampIDFields(self, id:int, ts:Optional[bytes]=None) -> None:
        """
        Fügt ein Timestamp-Feld sowie ein Feld id hinzu. Wird kein Timestamp übergeben, wird mittels der ID der aktuelle 
        Timestamp aus der DB geladen. Dabei kann ein Fehler auftreten. Intern wird :meth:`addTimestampField` benutzt.

        :param id: DB-id des Objektes dessen Timestamp hinzugefügt werden soll   
        :type id: string
        :param ts: Fester Timestamp der verwendet werden soll, wenn None wird der Timestamp aus der DB geladen.
        :type ts: bytes
        """
        self.addField("id", id)
        self.addTimestampField(id, ts=ts);

    def exec(self) -> Any:
        """
        Führt die UseXmlRow mittels useXML aus. Je nach Art der Zeile wird etwas zurückgeliefert oder nicht.
        In jedem Fall kann eine Exception geworfen werden.
        """
        return self.applus.useXML(self.toprettyxml());


class UseXmlRowInsert(UseXmlRow):
    """
    Klasse, die eine XML-Datei für das Einfügen eines neuen Datensatzes erzeugen kann.

    :param applus: Verbindung zu APplus 
    :type applus: APplusServer
    :param table: die Tabelle
    :type table: string
    """

    def __init__(self, applus:'APplusServer', table:str) -> None:
        super().__init__(applus, table, "insert");
    
    def insert(self) -> int:
        """
        Führt das insert aus. Entweder wird dabei eine Exception geworfen oder die ID des neuen Eintrags zurückgegeben.
        Dies ist eine Umbenennung von :meth:`exec`.
        """
        return super().exec();


class UseXmlRowDelete(UseXmlRow):
    """
    Klasse, die eine XML-Datei für das Löschen eines neuen Datensatzes erzeugen kann.
    Die Felder `id` und `timestamp` werden automatisch gesetzt.
    Dies sind die einzigen Felder, die gesetzt werden sollten.

    :param applus: Verbindung zu APplus 
    :type applus: APplusServer
    :param table: die Tabelle
    :type table: string
    :param id: die zu löschende ID
    :type id: int
    :param ts: wenn gesetzt, wird dieser Timestamp verwendet, sonst der aktuelle aus der DB
    :type ts: bytes optional
    """

    def __init__(self, applus:'APplusServer', table:str, id:int, ts:Optional[bytes]=None) -> None:
        super().__init__(applus, table, "delete");
        self.addTimestampIDFields(id, ts=ts);

    
    def delete(self) -> None:
        """
        Führt das delete aus. Evtl. wird dabei eine Exception geworfen.
        Dies ist eine Umbenennung von :meth:`exec`.
        """
        super().exec();        


class UseXmlRowUpdate(UseXmlRow):
    """
    Klasse, die eine XML-Datei für das Ändern eines neuen Datensatzes, erzeugen kann.
    Die Felder `id` und `timestamp` werden automatisch gesetzt.

    :param applus: Verbindung zu APplus 
    :type applus: APplusServer
    :param table: die Tabelle
    :type table: string
    :param id: die ID des zu ändernden Datensatzes
    :type id: int
    :param ts: wenn gesetzt, wird dieser Timestamp verwendet, sonst der aktuelle aus der DB
    :type ts: bytes optional
    """

    def __init__(self, applus : 'APplusServer', table : str, id : int, ts:Optional[bytes]=None) -> None:
        super().__init__(applus, table, "update");
        self.addTimestampIDFields(id, ts=ts);

    
    def update(self) -> None:
        """
        Führt das update aus. Evtl. wird dabei eine Exception geworfen.
        Dies ist eine Umbenennung von :meth:`exec`.
        """
        super().exec();        



class UseXmlRowInsertOrUpdate(UseXmlRow):
    """
    Klasse, die eine XML-Datei für das Einfügen oder Ändern eines neuen Datensatzes, erzeugen kann.
    Die Methode `checkExists` erlaubt es zu prüfen, ob ein Objekt bereits existiert. Dafür werden die
    gesetzten Felder mit den Feldern aus eindeutigen Indices verglichen. Existiert ein Objekt bereits, wird
    ein Update ausgeführt, ansonsten ein Insert. Bei Updates werden die Felder `id` und `timestamp` 
    automatisch gesetzt.

    :param applus: Verbindung zu APplus 
    :type applus: APplusServer
    :param table: die Tabelle
    :type table: string
    """

    def __init__(self, applus : 'APplusServer', table : str) -> None:
        super().__init__(applus, table, "");

    
    def checkExists(self) -> int|None:
        """
        Prüft, ob der Datensatz bereits in der DB existiert. 
        Ist dies der Fall, wird die ID geliefert, sonst None
        """

        # Baue Bedingung
        cond = sql_utils.SqlConditionOr();
        for idx, fs in self.applus.getUniqueFieldsOfTable(self.table).items():
            if (self.checkFieldsSet(*fs)):
                condIdx = sql_utils.SqlConditionAnd();
                for f in fs:
                    condIdx.addConditionFieldEq(f, self.getField(f))
                cond.addCondition(condIdx)
        
        sql = sql_utils.SqlStatementSelect(self.table, "id")
        sql.where = cond
        return self.applus.dbQuerySingleValue(sql)

    def insert(self) -> int:
        """Führt ein Insert aus. Existiert das Objekt bereits, wird eine Exception geworfen."""

        r = UseXmlRowInsert(self.applus, self.table)            
        for k, v in self.fields.items():
            r.addField(k, v)
        return r.insert();

    def update(self, id:Optional[int]=None, ts:Optional[bytes]=None) -> int:
        """Führt ein Update aus. Falls ID oder Timestamp nicht übergeben werden, wird
        nach einem passenden Objekt gesucht. Existiert das Objekt nicht, wird eine Exception geworfen."""

        if id is None:
            id = self.checkExists()

        if id is None:
            raise Exception("Update nicht möglich, da kein Objekt für Update gefunden.")
        
        r = UseXmlRowUpdate(self.applus, self.table, id, ts=ts)            
        for k, v in self.fields.items():
            r.addField(k, v)
        r.update();
        return id

    def exec(self) -> int:   
        """
        Führt entweder ein Update oder ein Insert durch. Dies hängt davon ab, ob das Objekt bereits in
        der DB existiert. In jedem Fall wird die ID des erzeugten oder geänderten Objekts geliefert.
        """

        id = self.checkExists();
        if id == None:
            return self.insert()
        else:            
            return self.update(id=id)

    def updateOrInsert(self) -> int:
        """
        Führt das update oder das insert aus. Evtl. wird dabei eine Exception geworfen.
        Dies ist eine Umbenennung von :meth:`exec`.
        Es wird die ID des Eintrages geliefert
        """
        return self.exec();        
