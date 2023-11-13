# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from . import applus_db
from . import applus_job
from . import applus_server
from . import applus_sysconf
from . import applus_scripttool
from . import applus_usexml
from . import sql_utils
import yaml
import json
import urllib.parse
from zeep import Client
import pyodbc  # type: ignore
from typing import TYPE_CHECKING, Optional, Any, Callable, Dict, Sequence, Set, List

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
    def __init__(self,
                 db_settings: applus_db.APplusDBSettings,
                 server_settings: applus_server.APplusServerSettings):

        self.db_settings: applus_db.APplusDBSettings = db_settings
        """Die Einstellungen für die Datenbankverbindung"""

        self.server_settings : applus_server.APplusServerSettings = server_settings
        """Einstellung für die Verbindung zum APP- und Webserver"""

        self._db_conn_pool = list()
        """Eine Liste bestehender DB-Verbindungen"""

        self.server_conn: applus_server.APplusServerConnection = applus_server.APplusServerConnection(server_settings)
        """erlaubt den Zugriff auf den AppServer"""

        self.sysconf: applus_sysconf.APplusSysConf = applus_sysconf.APplusSysConf(self)
        """erlaubt den Zugriff auf die Sysconfig"""

        self.job: applus_job.APplusJob = applus_job.APplusJob(self)
        """erlaubt Arbeiten mit Jobs"""

        self.scripttool: applus_scripttool.APplusScriptTool = applus_scripttool.APplusScriptTool(self)
        """erlaubt den einfachen Zugriff auf Funktionen des ScriptTools"""

        self._client_table = None
        self._client_xml = None
        self._client_nummer = None
        self._client_adaptdb= None

    @property
    def client_table(self) -> Client:
        if not self._client_table:
          self._client_table = self.getAppClient("p2core", "Table")
        return self._client_table

    @property
    def client_xml(self) -> Client:
        if not self._client_xml:
          self._client_xml = self.getAppClient("p2core", "XML")
        return self._client_xml

    @property
    def client_nummer(self) -> Client:
        if not self._client_nummer:
          self._client_nummer = self.getAppClient("p2system", "Nummer")
        return self._client_nummer

    @property
    def client_adaptdb(self) -> Client:
        if not self._client_adaptdb:
          self._client_adaptdb = self.getAppClient("p2dbtools", "AdaptDB")
        return self._client_adaptdb


    def getDBConnection(self) -> pyodbc.Connection:
        """
        Liefert eine pyodbc-Connection zur APplus DB. Diese muss genutzt werden, wenn mehrere Operationen in einer Transaktion
        genutzt werden sollen. Ansonsten sind die Hilfsmethoden wie :meth:`APplusServer.dbQuery` zu bevorzugen.
        Diese Connection kann in Verbindung mit den Funktionen aus :mod:`PyAPplus64.applus_db` genutzt werden.
        Die Verbindung sollte nach Benutzung wieder freigegeben oder geschlossen werden.
        """
        if self._db_conn_pool:
            return self._db_conn_pool.pop()
        else:
            conn = self.db_settings.connect()
            self._db_conn_pool.append(conn)
            return conn

    def releaseDBConnection(self, conn : pyodbc.Connection) -> None:
        """Gibt eine DB-Connection zur Wiederverwendung frei"""
        self._db_conn_pool.append(conn)

    def reconnectDB(self) -> None:
        for conn in self._db_conn_pool:
            try:
                conn.close()
            except:
                pass
        self._db_conn_pool = list()

    def completeSQL(self, sql: sql_utils.SqlStatement, raw: bool = False) -> str:
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
            return self.client_table.service.getCompleteSQL(sql)

    def dbQueryAll(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False,
                   apply: Optional[Callable[[pyodbc.Row], Any]] = None) -> Any:
        """Führt eine SQL Query aus und liefert alle Zeilen zurück. Das SQL wird zunächst
           vom Server angepasst, so dass z.B. Mandanteninformation hinzugefügt werden."""
        sqlC = self.completeSQL(sql, raw=raw)
        conn = self.getDBConnection()
        res = applus_db.rawQueryAll(conn, sqlC, *args, apply=apply)
        self.releaseDBConnection(conn)
        return res


    def dbQuerySingleValues(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False) -> Sequence[Any]:
        """Führt eine SQL Query aus, die nur eine Spalte zurückliefern soll."""
        return self.dbQueryAll(sql, *args, raw=raw, apply=lambda r: r[0])

    def dbQuery(self, sql: sql_utils.SqlStatement, f: Callable[[pyodbc.Row], None], *args: Any, raw: bool = False) -> None:
        """Führt eine SQL Query aus und führt für jede Zeile die übergeben Funktion aus.
           Das SQL wird zunächst vom Server angepasst, so dass z.B. Mandanteninformation hinzugefügt werden."""
        sqlC = self.completeSQL(sql, raw=raw)
        conn = self.getDBConnection()
        res = applus_db.rawQuery(conn, sqlC, f, *args)
        self.releaseDBConnection(conn)
        return res


    def dbQuerySingleRow(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False) -> Optional[pyodbc.Row]:
        """Führt eine SQL Query aus, die maximal eine Zeile zurückliefern soll. Diese Zeile wird geliefert."""
        sqlC = self.completeSQL(sql, raw=raw)
        conn = self.getDBConnection()
        res = applus_db.rawQuerySingleRow(conn, sqlC, *args)
        self.releaseDBConnection(conn)
        return res

    def dbQuerySingleRowDict(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False) -> Optional[Dict[str, Any]]:
        """Führt eine SQL Query aus, die maximal eine Zeile zurückliefern soll.
           Diese Zeile wird als Dictionary geliefert."""
        row = self.dbQuerySingleRow(sql, *args, raw=raw)
        if row:
            return applus_db.row_to_dict(row)
        else:
            return None

    def dbQuerySingleValue(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False) -> Any:
        """Führt eine SQL Query aus, die maximal einen Wert zurückliefern soll.
           Dieser Wert oder None wird geliefert."""
        sqlC = self.completeSQL(sql, raw=raw)
        conn = self.getDBConnection()
        res = applus_db.rawQuerySingleValue(conn, sqlC, *args)
        self.releaseDBConnection(conn)
        return res

    def dbExecute(self, sql: sql_utils.SqlStatement, *args: Any, raw: bool = False) -> Any:
        """Führt ein SQL Statement (z.B. update oder insert) aus. Das SQL wird zunächst
           vom Server angepasst, so dass z.B. Mandanteninformation hinzugefügt werden."""
        sqlC = self.completeSQL(sql, raw=raw)
        conn = self.getDBConnection()
        res = applus_db.rawExecute(conn, sqlC, *args)
        self.releaseDBConnection(conn)
        return res

    def isDBTableKnown(self, table: str) -> bool:
        """Prüft, ob eine Tabelle im System bekannt ist"""
        sql = "select count(*) from SYS.TABLES T where T.NAME=?"
        c = self.dbQuerySingleValue(sql, table)
        return (c > 0)

    def getAppClient(self, package: str, name: str) -> Client:
        """Erzeugt einen zeep - Client für den APP-Server.
           Mittels dieses Clients kann eines WSDL Schnittstelle des APP-Servers angesprochen werden.
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
        return self.server_conn.getAppClient(package, name)

    def getWebClient(self, url: str) -> Client:
        """Erzeugt einen zeep - Client für den Web-Server.
           Mittels dieses Clients kann die von einer ASMX-Seite zur Verfügung gestellte Schnittstelle angesprochen werden.
           Als parameter wird die relative URL der ASMX-Seite erwartet. Die Base-URL automatisch ergänzt.
           Ein Beispiel für eine solche relative URL ist "masterdata/artikel.asmx".

           ACHTUNG: Als Umgebung wird die Umgebung des sich anmeldenden Nutzers verwendet. Sowohl Nutzer als auch Umgebung können sich von den für App-Clients verwendeten Werten unterscheiden. Wenn möglich, sollte ein App-Client verwendet werden.

           :param url: die relative URL der ASMX Seite, z.B. "masterdata/artikel.asmx"
           :type package: str
           :return: den Client
           :rtype: Client
           """
        return self.server_conn.getWebClient(url)

    def getTableFields(self, table: str, isComputed: Optional[bool] = None) -> Set[str]:
        """
        Liefert die Namen aller Felder einer Tabelle.

        :param table: Name der Tabelle
        :param isComputed: wenn gesetzt, werden nur die Felder geliefert, die berechnet werden oder nicht berechnet werden
        :return: Liste aller Feld-Namen
        :rtype: {str}
        """
        sql = sql_utils.SqlStatementSelect("SYS.TABLES T")
        join = sql.addInnerJoin("SYS.COLUMNS C")
        join.on.addConditionFieldsEq("T.Object_ID", "C.Object_ID")
        if not (isComputed is None):
            join.on.addConditionFieldEq("c.is_computed", isComputed)
        sql.addFields("C.NAME")

        sql.where.addConditionFieldEq("t.name", sql_utils.SqlParam())
        return sql_utils.normaliseDBfieldSet(self.dbQueryAll(sql, table, apply=lambda r: r.NAME))

    def getUniqueFieldsOfTable(self, table: str) -> Dict[str, List[str]]:
        """
        Liefert alle Spalten einer Tabelle, die eindeutig sein müssen.
        Diese werden als Dictionary gruppiert nach Index-Namen geliefert.
        Jeder Eintrag enthält eine Liste von Feldern, die zusammen eindeutig sein
        müssen.
        """
        conn = self.getDBConnection()
        res = applus_db.getUniqueFieldsOfTable(conn, table)
        self.releaseDBConnection(conn)
        return res

    def useXML(self, xml: str) -> Any:
        """Ruft ``p2core.xml.usexml`` auf. Wird meist durch ein ``UseXMLRow-Objekt`` aufgerufen."""
        return self.client_xml.service.useXML(xml)

    def mkUseXMLRowInsert(self, table: str) -> applus_usexml.UseXmlRowInsert:
        """
        Erzeugt ein Objekt zum Einfügen eines neuen DB-Eintrags.

        :param table: DB-Tabelle in die eingefügt werden soll
        :type table: str
        :return: das XmlRow-Objekt
        :rtype: applus_usexml.UseXmlRowInsert
        """

        return applus_usexml.UseXmlRowInsert(self, table)

    def mkUseXMLRowUpdate(self, table: str, id: int) -> applus_usexml.UseXmlRowUpdate:
        return applus_usexml.UseXmlRowUpdate(self, table, id)

    def mkUseXMLRowInsertOrUpdate(self, table: str) -> applus_usexml.UseXmlRowInsertOrUpdate:
        """
        Erzeugt ein Objekt zum Einfügen oder Updaten eines DB-Eintrags.

        :param table: DB-Tabelle in die eingefügt werden soll
        :type table: string
        :return: das XmlRow-Objekt
        :rtype: applus_usexml.UseXmlRowInsertOrUpdate
        """

        return applus_usexml.UseXmlRowInsertOrUpdate(self, table)

    def mkUseXMLRowDelete(self, table: str, id: int) -> applus_usexml.UseXmlRowDelete:
        return applus_usexml.UseXmlRowDelete(self, table, id)

    def execUseXMLRowDelete(self, table: str, id: int) -> None:
        delRow = self.mkUseXMLRowDelete(table, id)
        delRow.delete()

    def nextNumber(self, obj: str) -> str:
        """
        Erstellt eine neue Nummer für das Objekt und legt diese Nummer zurück.
        """
        return self.client_nummer.service.nextNumber(obj)

    def updateDatabase(self, file : str) -> str:
        """
        Führt eine DBAnpass-xml Datei aus.
        :param file: DB-Anpass Datei, die ausgeführt werden soll
        :type file: string
        :return: Infos zur Ausführung
        :rtype: str
        """
        jobId = self.job.createSOAPJob("run DBAnpass " + file);
        self.client_adaptdb.service.updateDatabase(jobId, "de", file);
        res = self.job.getResultURLString(jobId)
        if res is None: res = "FEHLER";
        if (res == "Folgende Befehle konnten nicht ausgeführt werden:\n\n"):
            return ""
        else:
            return res


    def importUdfsAndViews(self, environment : str, views : [str] = [], udfs : [str] = []) -> str:
        """
        Importiert bestimmte  Views und UDFs
        :param environment: die Umgebung, in die Importiert werden soll
        :type environment: string
        :param views: Views, die importiert werden sollen
        :type views: [string]
        :param udfs: Views, die importiert werden sollen
        :type udfs: [string]
        :return: Infos zur Ausführung
        :rtype: str
        """
        lbl="";
        files=[];
        for v in views:
            files.append({"type" : 1, "name" : v})
        for u in udfs:
            files.append({"type" : 0, "name" : u})


        jobId = self.job.createSOAPJob("importing UDFs and Views");
        self.client_adaptdb.service.importUdfsAndViews(jobId, environment, False, json.dumps(files), "de");
        res = self.job.getResultURLString(jobId)
        if res is None: res = "FEHLER";
        return res


    def makeWebLink(self, base: str, **kwargs: Any) -> str:
        if not self.server_settings.webserver:
            raise Exception("keine Webserver-BaseURL gesetzt")

        url = str(self.server_settings.webserver) + base
        firstArg = True
        for arg, argv in kwargs.items():
            if not (argv is None):
                if firstArg:
                    firstArg = False
                    url += "?"
                else:
                    url += "&"
                url += arg + "=" + urllib.parse.quote(str(argv))
        return url

    def makeWebLinkWauftragPos(self, **kwargs: Any) -> str:
        return self.makeWebLink("wp/wauftragPosRec.aspx", **kwargs)

    def makeWebLinkWauftrag(self, **kwargs: Any) -> str:
        return self.makeWebLink("wp/wauftragRec.aspx", **kwargs)

    def makeWebLinkBauftrag(self, **kwargs: Any) -> str:
        return self.makeWebLink("wp/bauftragRec.aspx", **kwargs)

    def makeWebLinkAuftrag(self, **kwargs: Any) -> str:
        return self.makeWebLink("sales/auftragRec.aspx", **kwargs)

    def makeWebLinkVKRahmen(self, **kwargs: Any) -> str:
        return self.makeWebLink("sales/vkrahmenRec.aspx", **kwargs)

    def makeWebLinkWarenaugang(self, **kwargs: Any) -> str:
        return self.makeWebLink("sales/warenausgangRec.aspx", **kwargs)

def applusFromConfigDict(yamlDict: Dict[str, Any], user: Optional[str] = None, env: Optional[str] = None) -> APplusServer:
    """Läd Einstellungen aus einer Config und erzeugt daraus ein APplus-Objekt"""
    if user is None or user == '':
        user = yamlDict["appserver"]["user"]
    if env is None or env == '':
        env = yamlDict["appserver"]["env"]
    server_settings = applus_server.APplusServerSettings(
        webserver=yamlDict.get("webserver", {}).get("baseurl", None),
        appserver=yamlDict["appserver"]["server"],
        appserverPort=yamlDict["appserver"]["port"],
        user=user,  # type: ignore
        env=env,
        webserverUser=yamlDict.get("webserver", {}).get("user", None),
        webserverUserDomain=yamlDict.get("webserver", {}).get("userDomain", None),
        webserverPassword=yamlDict.get("webserver", {}).get("password", None))
    dbparams = applus_db.APplusDBSettings(
        server=yamlDict["dbserver"]["server"],
        database=yamlDict["dbserver"]["db"],
        user=yamlDict["dbserver"]["user"],
        password=yamlDict["dbserver"]["password"])
    return APplusServer(dbparams, server_settings)


def applusFromConfigFile(yamlfile: 'FileDescriptorOrPath',
                         user: Optional[str] = None, env: Optional[str] = None) -> APplusServer:
    """Läd Einstellungen aus einer Config-Datei und erzeugt daraus ein APplus-Objekt"""
    yamlDict = {}
    with open(yamlfile, "r") as stream:
        yamlDict = yaml.safe_load(stream)

    return applusFromConfigDict(yamlDict, user=user, env=env)


def applusFromConfig(yamlString: str, user: Optional[str] = None, env: Optional[str] = None) -> APplusServer:
    """Läd Einstellungen aus einer Config-Datei und erzeugt daraus ein APplus-Objekt"""
    yamlDict = yaml.safe_load(yamlString)
    return applusFromConfigDict(yamlDict, user=user, env=env)


class APplusServerConfigDescription:
    """
    Beschreibung einer Configuration bestehend aus Config-Datei, Nutzer und Umgebung.

    :param descr: Beschreibung als String, nur für Ausgabe gedacht
    :type descr: str

    :param yamlfile: die Datei
    :type yamlfile: 'FileDescriptorOrPath'

    :param user: der Nutzer
    :type user: Optional[str]

    :param env: die Umgebung
    :type env: Optional[str]
    """
    def __init__(self,
                 descr: str,
                 yamlfile: 'FileDescriptorOrPath',
                 user:Optional[str] = None,
                 env:Optional[str] = None):
        self.descr = descr
        self.yamlfile = yamlfile
        self.user = user
        self.env = env

    def __str__(self) -> str:
        return self.descr

    def connect(self) -> APplusServer:
        return applusFromConfigFile(self.yamlfile, user=self.user, env=self.env)



