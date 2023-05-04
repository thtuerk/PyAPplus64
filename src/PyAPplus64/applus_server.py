# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

from requests import Session # type: ignore
from requests.auth import HTTPBasicAuth  # type: ignore # or HTTPDigestAuth, or OAuth1, etc.
from zeep import Client
from zeep.transports import Transport
from zeep.cache import SqliteCache
from typing import Optional, Dict


class APplusAppServerSettings:
    """
    Einstellungen, mit welchem APplus App-Server sich verbunden werden soll.
    """
    
    def __init__(self, appserver : str, appserverPort : int, user : str, env : Optional[str] = None):
        self.appserver = appserver
        self.appserverPort = appserverPort
        self.user = user
        self.env = env

class APplusWebServerSettings:
    """
    Einstellungen, mit welchem APplus Web-Server sich verbunden werden soll.
    """
    
    def __init__(self, baseurl:Optional[str]=None):
        self.baseurl : Optional[str] = baseurl;
        try:        
            assert (isinstance(self.baseurl, str))
            if not (self.baseurl == None) and not (self.baseurl[-1] == "/"):
                self.baseurl = self.baseurl + "/";
        except:
            pass


class APplusServerConnection:
    """Verbindung zu einem APplus APP-Server

    :param settings: die Einstellungen für die Verbindung mit dem APplus Server
    :type settings: APplusAppServerSettings
    """
    def __init__(self, settings : APplusAppServerSettings) -> None:
        userEnv = settings.user;
        if (settings.env):
            userEnv += "|" + settings.env

        session = Session()
        session.auth = HTTPBasicAuth(userEnv, "")

        self.transport = Transport(cache=SqliteCache(), session=session)
        # self.transport = Transport(session=session)
        self.clientCache : Dict[str, Client] = {}
        self.settings=settings;
        self.appserverUrl = "http://" + settings.appserver + ":" + str(settings.appserverPort) + "/";

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
        url = package+"/"+name;
        try:
            return self.clientCache[url];
        except:
            fullClientUrl = self.appserverUrl + url + ".jws?wsdl"
            client = Client(fullClientUrl, transport=self.transport)
            self.clientCache[url] = client;
            return client;
