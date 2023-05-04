# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

from . import applus_db
from . import applus_server
from . import applus_sysconf
from . import applus_scripttool
from . import applus_usexml
from . import sql_utils
import yaml
import urllib.parse
from zeep import Client
import pyodbc # type: ignore
from typing import *

if TYPE_CHECKING:
    from _typeshed import FileDescriptorOrPath



class APplusServer:
    """
    Verbindung zu einem APplus DB und App Server mit Hilfsfunktionen für den komfortablen Zugriff.
    
    :param db_settings: die Einstellungen für die Verbindung mit der Datenbank
    :type db_settings: APplusDBSettings
    :param server_settings: die Einstellungen für die Verbindung mit dem APplus App Server
    :type server_settings: APplusAppServerSettings
    :param web_settings: die Einstellungen für die Verbindung mit dem APplus Web Server
    :type web_settings: APplusWebServerSettings
    """
    def __init__(self, db_settings : applus_db.APplusDBSettings, server_settings : applus_server.APplusAppServerSettings, web_settings : applus_server.APplusWebServerSettings):

        self.db_settings : applus_db.APplusDBSettings = db_settings
        """Die Einstellungen für die Datenbankverbindung"""

        self.web_settings : applus_server.APplusWebServerSettings = web_settings
        """Die Einstellungen für die Datenbankverbindung"""

        self.db_conn = db_settings.connect()        
        """
        Eine pyodbc-Connection zur APplus DB. Diese muss genutzt werden, wenn mehrere Operationen in einer Transaktion
        genutzt werden sollen. Ansonsten sind die Hilfsmethoden wie :meth:`APplusServer.dbQuery` zu bevorzugen. 
        Diese Connection kann in Verbindung mit den Funktionen aus :mod:`PyAPplus64.applus_db` genutzt werden.
        """


        self.server_conn :  applus_server.APplusServerConnection = applus_server.APplusServerConnection(server_settings);
        """erlaubt den Zugriff auf den AppServer"""
        
        self.sysconf : applus_sysconf.APplusSysConf = applus_sysconf.APplusSysConf(self);
        """erlaubt den Zugriff auf die Sysconfig"""

        self.scripttool : applus_scripttool.APplusScriptTool = applus_scripttool.APplusScriptTool(self);
        """erlaubt den einfachen Zugriff auf Funktionen des ScriptTools"""

        self.client_table = self.server_conn.getClient("p2core","Table");
        self.client_xml = self.server_conn.getClient("p2core","XML");
        self.client_nummer = self.server_conn.getClient("p2system", "Nummer")

    def reconnectDB(self) -> None:
        try:
            self.db_conn.close() 
        except:
            pass
        self.db_conn = self.db_settings.connect()

    def completeSQL(self, sql : sql_utils.SqlStatement, raw:bool=False) -> str:
        """
        Vervollständigt das SQL-Statement. Es wird z.B. der Mandant hinzugefügt.
            
        :param sql: das SQL Statement
        :type sql: sql_utils.SqlStatement
        :param raw: soll completeSQL ausgeführt werden? Falls True, wird die Eingabe zurückgeliefert
        :type raw: boolean
        :return: das vervollständigte SQL-Statement
        :rtype: str
        """
        if raw:
            return str(sql)
        else:
            return self.client_table.service.getCompleteSQL(sql);

    def dbQueryAll(self, sql : sql_utils.SqlStatement, *args:Any, raw:bool=False, 
                   apply:Optional[Callable[[pyodbc.Row],Any]]=None) -> Any:
        """Führt eine SQL Query aus und liefert alle Zeilen zurück. Das SQL wird zunächst 
           vom Server angepasst, so dass z.B. Mandanteninformation hinzugefügt werden."""
        sqlC = self.completeSQL(sql, raw=raw);
        return applus_db.rawQueryAll(self.db_conn, sqlC, *args, apply=apply)

    def dbQuerySingleValues(self, sql : sql_utils.SqlStatement, *args:Any, raw:bool=False) -> Sequence[Any]:
        """Führt eine SQL Query aus, die nur eine Spalte zurückliefern soll."""
        return self.dbQueryAll(sql, *args, raw=raw, apply=lambda r: r[0])

    def dbQuery(self, sql : sql_utils.SqlStatement, f : Callable[[pyodbc.Row], None], *args : Any, raw:bool=False) -> None:
        """Führt eine SQL Query aus und führt für jede Zeile die übergeben Funktion aus. 
           Das SQL wird zunächst vom Server angepasst, so dass z.B. Mandanteninformation hinzugefügt werden."""
        sqlC = self.completeSQL(sql, raw=raw);
        applus_db.rawQuery(self.db_conn, sqlC, f, *args)

    def dbQuerySingleRow(self, sql:sql_utils.SqlStatement, *args:Any, raw:bool=False) -> Optional[pyodbc.Row]:
        """Führt eine SQL Query aus, die maximal eine Zeile zurückliefern soll. Diese Zeile wird geliefert."""
        sqlC = self.completeSQL(sql, raw=raw);
        return applus_db.rawQuerySingleRow(self.db_conn, sqlC, *args)

    def dbQuerySingleRowDict(self, sql:sql_utils.SqlStatement, *args:Any, raw:bool=False) -> Optional[Dict[str, Any]]:
        """Führt eine SQL Query aus, die maximal eine Zeile zurückliefern soll. 
           Diese Zeile wird als Dictionary geliefert."""
        row = self.dbQuerySingleRow(sql, *args, raw=raw);
        if row:
            return applus_db.row_to_dict(row);
        else:
            return None

    def dbQuerySingleValue(self, sql:sql_utils.SqlStatement, *args:Any, raw:bool=False) -> Any:
        """Führt eine SQL Query aus, die maximal einen Wert zurückliefern soll. 
           Dieser Wert oder None wird geliefert."""
        sqlC = self.completeSQL(sql, raw=raw);
        return applus_db.rawQuerySingleValue(self.db_conn, sqlC, *args)

    def isDBTableKnown(self, table : str) -> bool:
        """Prüft, ob eine Tabelle im System bekannt ist"""
        sql = "select count(*) from SYS.TABLES T where T.NAME=?"
        c = self.dbQuerySingleValue(sql, table);
        return (c > 0)

    def getClient(self, package : str, name : str) -> Client:
        """Erzeugt einen zeep - Client.
           Mittels dieses Clients kann die WSDL Schnittstelle angesprochen werden.
           Wird als *package* "p2core" und als *name* "Table" verwendet und der 
           resultierende client "client" genannt, dann kann
           z.B. mittels "client.service.getCompleteSQL(sql)" vom AppServer ein Vervollständigen
           des SQLs angefordert werden.

           :param package: das Packet, z.B. "p2core"
           :type package: str
           :param name: der Name im Packet, z.B. "Table"
           :type package: string
           :return: den Client
           :rtype: Client
           """
        return self.server_conn.getClient(package, name);

    def getTableFields(self, table:str, isComputed:Optional[bool]=None) -> Set[str]:
        """
        Liefert die Namen aller Felder einer Tabelle.

        :param table: Name der Tabelle
        :param isComputed: wenn gesetzt, werden nur die Felder geliefert, die berechnet werden oder nicht berechnet werden
        :return: Liste aller Feld-Namen
        :rtype: {str}
        """
        sql = sql_utils.SqlStatementSelect("SYS.TABLES T")
        join = sql.addInnerJoin("SYS.COLUMNS C");
        join.on.addConditionFieldsEq("T.Object_ID", "C.Object_ID")
        if not (isComputed == None):
            join.on.addConditionFieldEq("c.is_computed", isComputed)        
        sql.addFields("C.NAME")

        sql.where.addConditionFieldEq("t.name", sql_utils.SqlParam())
        return sql_utils.normaliseDBfieldSet(self.dbQueryAll(sql, table, apply=lambda r : r.NAME));

    def getUniqueFieldsOfTable(self, table : str) -> Dict[str, List[str]]:     
        """
        Liefert alle Spalten einer Tabelle, die eindeutig sein müssen. 
        Diese werden als Dictionary gruppiert nach Index-Namen geliefert. 
        Jeder Eintrag enthält eine Liste von Feldern, die zusammen eindeutig sein 
        müssen.
        """
        return applus_db.getUniqueFieldsOfTable(self.db_conn, table)


    def useXML(self, xml : str) -> Any:
        """Ruft ``p2core.xml.usexml`` auf. Wird meist durch ein ``UseXMLRow-Objekt`` aufgerufen."""        
        return self.client_xml.service.useXML(xml);


    def mkUseXMLRowInsert(self, table : str) -> applus_usexml.UseXmlRowInsert:
        """
        Erzeugt ein Objekt zum Einfügen eines neuen DB-Eintrags.
        
        :param table: DB-Tabelle in die eingefügt werden soll
        :type table: str
        :return: das XmlRow-Objekt
        :rtype: applus_usexml.UseXmlRowInsert
        """

        return applus_usexml.UseXmlRowInsert(self, table)

    def mkUseXMLRowUpdate(self, table : str, id : int) -> applus_usexml.UseXmlRowUpdate:
        return applus_usexml.UseXmlRowUpdate(self, table, id)

    def mkUseXMLRowInsertOrUpdate(self, table : str) -> applus_usexml.UseXmlRowInsertOrUpdate:
        """
        Erzeugt ein Objekt zum Einfügen oder Updaten eines DB-Eintrags.
        
        :param table: DB-Tabelle in die eingefügt werden soll
        :type table: string
        :return: das XmlRow-Objekt
        :rtype: applus_usexml.UseXmlRowInsertOrUpdate
        """

        return applus_usexml.UseXmlRowInsertOrUpdate(self, table)


    def mkUseXMLRowDelete(self, table:str, id:int) -> applus_usexml.UseXmlRowDelete :
        return applus_usexml.UseXmlRowDelete(self, table, id)        

    def execUseXMLRowDelete(self, table:str, id:int) -> None:
        delRow = self.mkUseXMLRowDelete(table, id)
        delRow.delete();

    def nextNumber(self, obj : str) -> str:
        """
        Erstellt eine neue Nummer für das Objekt und legt diese Nummer zurück.
        """
        return self.client_nummer.service.nextNumber(obj)

    def makeWebLink(self, base : str, **kwargs : Any) -> str :
        if not self.web_settings.baseurl:
            raise Exception("keine Webserver-BaseURL gesetzt");
        
        url = str(self.web_settings.baseurl) + base;
        firstArg = True
        for arg, argv in kwargs.items():
            if not (argv == None):
                if firstArg:
                    firstArg = False;
                    url += "?"
                else:
                    url += "&"
                url += arg + "=" + urllib.parse.quote(str(argv))
        return url;

    def makeWebLinkWauftragPos(self, **kwargs : Any) -> str:
        return self.makeWebLink("wp/wauftragPosRec.aspx", **kwargs);

    def makeWebLinkWauftrag(self, **kwargs : Any) -> str :
        return self.makeWebLink("wp/wauftragRec.aspx", **kwargs);

    def makeWebLinkBauftrag(self, **kwargs : Any) -> str :
        return self.makeWebLink("wp/bauftragRec.aspx", **kwargs);



def applusFromConfigDict(yamlDict:Dict[str, Any], user:Optional[str]=None, env:Optional[str]=None) -> APplusServer:
    """Läd Einstellungen aus einer Config und erzeugt daraus ein APplus-Objekt"""
    if user is None or user=='':
        user = yamlDict["appserver"]["user"]        
    if env is None or env=='':
        env = yamlDict["appserver"]["env"]        
    app_server = applus_server.APplusAppServerSettings(
        appserver=yamlDict["appserver"]["server"], 
        appserverPort=yamlDict["appserver"]["port"], 
        user=user, # type: ignore
        env=env)
    web_server = applus_server.APplusWebServerSettings(
        baseurl=yamlDict.get("webserver", {}).get("baseurl", None)
    )
    dbparams = applus_db.APplusDBSettings(
        server=yamlDict["dbserver"]["server"], 
        database=yamlDict["dbserver"]["db"],
        user=yamlDict["dbserver"]["user"], 
        password=yamlDict["dbserver"]["password"]);
    return APplusServer(dbparams, app_server, web_server);

def applusFromConfigFile(yamlfile : 'FileDescriptorOrPath', 
                         user:Optional[str]=None, env:Optional[str]=None) -> APplusServer:
    """Läd Einstellungen aus einer Config-Datei und erzeugt daraus ein APplus-Objekt"""
    yamlDict = {}
    with open(yamlfile, "r") as stream:
        yamlDict = yaml.safe_load(stream)

    return applusFromConfigDict(yamlDict, user=user, env=env)

def applusFromConfig(yamlString : str, user:Optional[str]=None, env:Optional[str]=None) -> APplusServer:
    """Läd Einstellungen aus einer Config-Datei und erzeugt daraus ein APplus-Objekt"""
    yamlDict = yaml.safe_load(yamlString)
    return applusFromConfigDict(yamlDict, user=user, env=env)

