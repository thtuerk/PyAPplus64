# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from requests import Session  # type: ignore
from requests.auth import HTTPBasicAuth  # type: ignore # or HTTPDigestAuth, or OAuth1, etc.
from zeep import Client
from zeep.transports import Transport
from zeep.cache import SqliteCache
from typing import Optional, Dict

try:
    from requests_negotiate_sspi import HttpNegotiateAuth
    auth_negotiate_present = True
except:
    auth_negotiate_present = False

class APplusServerSettings:
    """
    Einstellungen, mit welchem APplus App- and Web-Server sich verbunden werden soll.
    """

    def __init__(self, webserver: str, appserver: str, appserverPort: int, user: str, env: Optional[str] = None, webserverUser : Optional[str] = None, webserverUserDomain : Optional[str] = None, webserverPassword : Optional[str] = None):
        self.appserver = appserver
        self.appserverPort = appserverPort
        self.user = user
        self.env = env

        self.webserver = webserver
        self.webserverUser = webserverUser
        self.webserverUserDomain = webserverUserDomain
        self.webserverPassword = webserverPassword
        try:
            if not (self.webserver[-1] == "/"):
                self.webserver = self.webserver + "/"
        except:
            pass


class APplusServerConnection:
    """Verbindung zu einem APplus APP- und Web-Server

    :param settings: die Einstellungen für die Verbindung mit dem APplus Server
    :type settings: APplusAppServerSettings
    """
    def __init__(self, settings: APplusServerSettings) -> None:
        userEnv = settings.user
        if (settings.env):
            userEnv += "|" + settings.env

        sessionApp = Session()
        sessionApp.auth = HTTPBasicAuth(userEnv, "")

        self.transportApp = Transport(cache=SqliteCache(), session=sessionApp)
        # self.transportApp = Transport(session=sessionApp)

        if auth_negotiate_present:
            sessionWeb = Session()
            sessionWeb.auth = HttpNegotiateAuth(username=settings.webserverUser, password=settings.webserverPassword, domain=settings.webserverUserDomain)

            self.transportWeb = Transport(cache=SqliteCache(), session=sessionWeb)
            # self.transportWeb = Transport(session=sessionWeb)
        else:
            self.transportWeb = self.transportApp   # führt vermutlich zu Authorization-Fehlern, diese sind aber zumindest hilfreicher als NULL-Pointer Exceptions

        self.clientCache: Dict[str, Client] = {}
        self.settings = settings
        self.appserverUrl = "http://" + settings.appserver + ":" + str(settings.appserverPort) + "/"

    def getAppClient(self, package: str, name: str) -> Client:
        """Erzeugt einen zeep - Client für den APP-Server.
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
        cacheKey = "APP:"+package+"/"+name
        try:
            return self.clientCache[cacheKey]
        except:
            fullClientUrl = self.appserverUrl + package+"/"+name + ".jws?wsdl"
            client = Client(fullClientUrl, transport=self.transportApp)
            self.clientCache[cacheKey] = client
            return client

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
        if not auth_negotiate_present:
            raise Exception("getWebClient ist nicht verfügbar, da Python-Package requests-negotiate-sspi nicht gefunden wurde")

        cacheKey = "WEB:"+url
        try:
            return self.clientCache[cacheKey]
        except:
            fullClientUrl = self.settings.webserver + url + "?wsdl"
            client = Client(fullClientUrl, transport=self.transportWeb)
            self.clientCache[cacheKey] = client
            return client
