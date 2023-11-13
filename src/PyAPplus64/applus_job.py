# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from typing import TYPE_CHECKING, Optional
from zeep import Client
import uuid

if TYPE_CHECKING:
    from .applus import APplusServer


class APplusJob:
    """
    Zugriff auf Jobs

    :param server: die Verbindung zum Server
    :type server: APplusServer

    """

    def __init__(self, server: 'APplusServer') -> None:
        self.server = server
        self._client = None

    @property
    def client(self) -> Client:
        if not self._client: 
          self._client = self.server.getAppClient("p2core", "Job")
        return self._client

    def createSOAPJob(self, bez: str) -> str:
        """
        Erzeugt einen neuen SOAP Job mit der gegebenen Bezeichnung und liefert die neue JobID.
        :param bez: die Bezeichnung des neuen Jobs
        :type bez: str
        :return: die neue JobID
        :rtype: str
        """
        jobId = str(uuid.uuid4())
        self.client.service.create(jobId, "SOAP", "0", "about:soapcall", bez)
        return jobId

    def restart(self, jobId: str) -> str:
        """
        Startet einen Job neu
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die URL des Jobs
        :rtype: str
        """
        return self.client.service.restart(jobId)

    def setResultURL(self, jobId: str, resurl: str) -> None:
        """
        Setzt die ResultURL eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :param resurl: die neue Result-URL
        :type resurl: str
        """
        self.client.service.setResultURL(jobId, resurl)

    def getResultURL(self, jobId: str) -> str:
        """
        Liefert die ResultURL eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die Result-URL
        :rtype: str
        """
        return self.client.service.getResultURL(jobId)

    def getResultURLString(self, jobId: str) -> Optional[str]:
        """
        Liefert die ResultURL eines Jobs, wobei ein evtl. Präfix "retstring://" entfernt wird und
        alle anderen Werte durch None ersetzt werden.
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die Result-URL als String
        :rtype: str
        """
        res = self.getResultURL(jobId)
        if res is None:
            return None

        if res.startswith("retstring://"):
            return res[12:]
        return None

    def setPtURL(self, jobId: str, pturl: str) -> None:
        """
        Setzt die ResultURL eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :param pturl: die neue PtURL
        :type pturl: str
        """
        self.client.service.setPtURL(jobId, pturl)

    def getPtURL(self, jobId: str) -> str:
        """
        Liefert die PtURL eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die Pt-URL
        :rtype: str
        """
        return self.client.service.getPtURL(jobId)

    def setResult(self, jobId: str, res: str) -> None:
        """
        Setzt das Result eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :param res: das neue Result
        :type res: str
        """
        self.client.service.setResult(jobId, res)

    def getResult(self, jobId: str) -> str:
        """
        Liefert das Result eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: das Result
        :rtype: str
        """
        return self.client.service.getResult(jobId)

    def setInfo(self, jobId: str, info: str) -> bool:
        """
        Setzt die Informationen zu dem Job
        :param jobId: die ID des Jobs
        :type jobId: str
        :param info: die neuen Infos
        :type info: str
        """
        return self.client.service.setInfo(jobId, info)

    def getInfo(self, jobId: str) -> str:
        """
        Liefert die Info eines Jobs
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die Info
        :rtype: str
        """
        return self.client.service.getInfo(jobId)

    def getStatus(self, jobId: str) -> str:
        """
        Liefert Informationen zum Job
        :param jobId: die ID des Jobs
        :type jobId: str
        :return: die Infos
        :rtype: str
        """
        return self.client.service.getStatus(jobId)

    def setPosition(self, jobId: str, pos: int, max: int) -> bool:
        """
        Schrittfunktion
        :param jobId: die ID des Jobs
        :type jobId: str
        :param pos: Position
        :type pos: int
        :param max: Anzahl Schritte in Anzeige
        :type max: int
        """
        return self.client.service.setPosition(jobId, pos, max)

    def start(self, jobId: str) -> bool:
        """
        Startet einen Job
        :param jobId: die ID des Jobs
        :type jobId: str
        """
        return self.client.service.start(jobId)

    def kill(self, jobId: str) -> None:
        """
        Startet einen Job
        :param jobId: die ID des Jobs
        :type jobId: str
        """
        self.client.service.start(jobId)

    def finish(self, jobId: str, status: int, resurl: str) -> bool:
        """
        Beendet den Job
        :param jobId: die ID des Jobs
        :type jobId: str
        :param status: der Status 2 (OK), 3 (Fehler)
        :type status: int
        :param resurl: die neue resurl des Jobs
        :type resurl: str
        """
        return self.client.service.finish(jobId, status, resurl)
