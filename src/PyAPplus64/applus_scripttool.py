# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

from .applus import APplusServer
from . import sql_utils
import lxml.etree as ET # type: ignore
from typing import *

class XMLDefinition:
    """Repräsentation eines XML-Dokuments"""

    def __init__(self, root : ET.Element) -> None:
        self.root : ET.Element = root
        """das Root-Element, repräsentiert "object" aus Datei."""

    def __str__(self) -> str:
        return ET.tostring(self.root, encoding = "unicode")

    def getDuplicate(self) -> Tuple[Set[str], bool]:
        """
        Extrahiert alle Properties, die für Duplizieren konfiguriert sind.
        Zudem wird ein Flag geliefert, ob diese Properties ein oder ausgeschlossen werden sollen.
        :return: Tuple aus allen Properties und ob dies aus- (True) oder ein-(False) zuschließen sind.
        :rtype: Tuple[Set[str], bool]
        """
        res : Set[str] = set()
        excl = True;
        dupl = self.root.find("duplicate")
        if (dupl is None):
            return (res, excl);

        exclS = dupl.get("type", default="exclude")
        excl = exclS.casefold() == "exclude"

        for e in dupl.findall("{ref}property"):
            v = e.get("ref")
            if not (v is None):
                res.add(sql_utils.normaliseDBfield(str(v)))
        
        return (res, excl)


class APplusScriptTool:
    """
    Zugriff auf AppServer ScriptTool

    :param server: die Verbindung zum Server
    :type server: APplusServerConnection

    """
    
    def __init__(self, server : APplusServer) -> None:
        self.client = server.getClient("p2script", "ScriptTool")

    def getCurrentDate(self) -> str:
        return self.client.service.getCurrentDate()

    def getCurrentTime(self) -> str:
        return self.client.service.getCurrentTime()

    def getCurrentDateTime(self) -> str:
        return self.client.service.getCurrentDateTime()

    def getLoginName(self) -> str:
        return self.client.service.getLoginName()

    def getUserName(self) -> str:
        return self.client.service.getUserName()

    def getUserFullName(self) -> str:
        return self.client.service.getUserFullName()
        
    def getSystemName(self) -> str:
        return self.client.service.getSystemName()

    def getXMLDefinitionString(self, obj:str, mandant:str="") -> str:
        """
        Läd die XML-Defintion als String vom APPServer. Auch wenn kein XML-Dokument im Dateisystem gefunden wird,
        wird ein String zurückgeliefert, der einen leeren Top-"Object" Knoten enthält. Für gefundene XML-Dokumente
        gibt es zusätzlich einen Top-"MD5"-Knoten. 
        
        :param obj: das Objekt, dessen Definition zu laden ist, "Artikel" läd z.B. "ArtikelDefinition.xml"
        :type obj: str
        :param mandant: der Mandant, dessen XML-Doku geladen werden soll, wenn "" wird der Standard-Mandant verwendet
        :type mandant: str optional
        :return: das gefundene XML-Dokument als String
        :rtype: str 
        """
        return self.client.service.getXMLDefinition2(obj, "")

    def getXMLDefinition(self, obj:str, mandant:str="", checkFileExists:bool=False) -> Optional[ET.Element]:
        """
        Läd die XML-Definition als String vom APPServer. und parst das XML in ein minidom-Dokument.
        
        :param obj: das Objekt, dessen Definition zu laden ist, "Artikel" läd z.B. "ArtikelDefinition.xml"
        :type obj: str
        :param mandant: der Mandant, dessen XML-Doku geladen werden soll, wenn "" wird der Standard-Mandant verwendet
        :type mandant: str optional
        :return: das gefundene und mittels ElementTree geparste XML-Dokument
        :rtype: ET.Element
        """
        return ET.fromstring(self.getXMLDefinitionString(obj, mandant=mandant))

    def getXMLDefinitionObj(self, obj:str, mandant:str="") -> Optional[XMLDefinition]:
        """
        Benutzt getXMLDefinitionObj und liefert den Top-Level "Object" Knoten zurück, falls zusätzlich 
        ein MD5 Knoten existiert, also falls das Dokument wirklich vom Dateisystem geladen werden konnte.
        Ansonten wird None geliefert.

        :param obj: das Objekt, dess Definition zu laden ist, "Artikel" läd z.B. "ArtikelDefinition.xml"
        :type obj: str
        :param mandant: der Mandant, dessen XML-Doku geladen werden soll, wenn "" wird der Standard-Mandant verwendet
        :type mandant: str optional
        :return: das gefundene und mittels ElementTree geparste XML-Dokument
        :rtype: Optional[XMLDefinition]
        """
        e = self.getXMLDefinition(obj, mandant=mandant);
        if e is None:
            return None

        if e.find("md5") is None:
            return None;

        o = e.find("object")
        if o is None:
            return None
        else:
            return XMLDefinition(o);


    def getMandant(self) -> str:
        """
        Liefert den aktuellen Mandanten
        """
        return self.client.service.getCurrentClientProperty("MANDANTID")

    def getMandantName(self) -> str:
        """
        Liefert den Namen des aktuellen Mandanten
        """
        return self.client.service.getCurrentClientProperty("NAME")
