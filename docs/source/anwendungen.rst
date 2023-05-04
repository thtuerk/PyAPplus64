typische Anwendungsfälle
========================

einfache Admin-Aufgaben
-----------------------

Selten auftretende Admin-Aufgaben lassen sich gut mittels Python-Scripten automatisieren.
Es ist sehr einfach möglich, auf die DB, aber auch auf SOAP-Schnittstelle zuzugreifen.
Ich habe dies vor allem für Wartungsarbeiten an Anpassungstabellen, die für eigene Erweiterungen
entwickelt wurden, genutzt. 

Als triviales Beispiel sucht folgender Code alle `DOCUMENTS` Einträge in
Artikeln (angezeigt als `Bild` in `ArtikelRec.aspx`), für die Datei, auf die
verwiesen wird, nicht im Dateisystem existiert. Diese fehlenden Dateien werden
ausgegeben und das Feld `DOCUMENTS` gelöscht. Das Löschen erfolgt dabei über 
`useXML`, so dass die Felder `UPDDATE` und `UPDUSER` korrekt gesetzt werden.

.. literalinclude:: ../../examples/check_dokumente.py
   :language: python
   :linenos:

Man kann alle Python Bibliotheken nutzen. Als Erweiterung wäre es in obigem Script 
zum Beispiel einfach möglich, alle BMP-Bilder zu suchen, nach PNG zu konvertieren 
und den DB-Eintrag anzupassen.


Ad-hoc Reports
--------------

APplus erlaubt es mittels Jasper-Reports, flexible und schöne Reports zu erzeugen.
Dies funktioniert gut und ist für regelmäßig benutzte Reports sehr sinnvoll.

Für ad-hoc Reports, die nur sehr selten oder sogar nur einmal benutzt werden, ist die
Erstellung eines Jasper-Reports und die Einbindung in APplus jedoch zu zeitaufwändig. 
Teilweise genügen die Ergebnisse einer SQL-Abfrage, die direkt im MS SQL Server abgesetzt 
werden kann. Wird es etwas komplizierter oder sollen die Ergebnisse noch etwas verarbeitet
werden, bietet sich evtl. Python an. 

Folgendes Script erzeugt zum Beispiel eine Excel-Tabelle, mit einer Übersicht,
welche Materialen wie oft für Artikel benutzt werden:

.. literalinclude:: ../../examples/adhoc_report.py
   :language: python
   :linenos:

Dieses kurze Script nutzt Standard-Pandas Methoden zur Erzeugung der Excel-Datei. Allerdings
sind diese Methoden in den Aufrufen von `pandasReadSql` und `exportToExcel` gekapselt,
so dass der Aufruf sehr einfach ist. Zudem ist es sehr einfach, die Verbindung zur Datenbank
und zum APP-Server mittels der YAML-Konfigdatei herzustellen. Bei diesem 
Aufruf kann optional ein Nutzer und eine Umgebung übergeben werden, die die Standard-Werte aus 
der YAML-Datei überschreiben. `pandasReadSql` nutzt intern `completeSQL`, so dass 
der für die Umgebung korrekte Mandant automatisch verwendet wird.



Anbindung eigener Tools
-----------------------

Ursprünglich wurde `PyAPplus64` für die Anbindung einer APplus-Anpassung geschrieben. Dieses ist 
als Windows-Service auf einem eigenen Rechner installiert und überwacht dort ein bestimmtes Verzeichnis.
Bei Änderungen an Dateien in diesem Verzeichnis (Hinzufügen, Ändern, Löschen) werden die Dateien verarbeitet
und die Ergebnisse an APplus gemeldet. Dafür werden DB-Operationen aber auch SOAP-Calls benutzt.
Ebenso wird auf die SysConf zugegriffen.

Viele solcher Anpassungen lassen sich gut und sinnvoll im App-Server einrichten und als Job regelmäßig aufrufen. 
Im konkreten Fall wird jedoch für die Verarbeitung der Dateien viel Rechenzeit benötigt. Dies würde dadurch 
verschlimmert, dass die Dateien nicht auf der gleichen Maschine wie der App-Server liegen und somit 
viele, relativ langsame Dateizugriffe über das Netzwerk nötig wären. Hinzu kommt, dass die
Verarbeitung der Dateien dank existierender Bibliotheken in Python einfacher ist.

`PyAPplus64` kann für solche Anpassungen eine interessante Alternative zur Implementierung im App-Server 
oder zur Entwicklung eines Tools ohne spezielle Bibliotheken sein. Nach Initialisierung des Servers::

   import PyAPplus64

   server = PyAPplus64.applus.applusFromConfigFile("my-applus-server.yaml") 

bietet `P2APplus64` wie oben demonstriert einfachen lesenden und schreibenden Zugriff auf die DB. Hierbei 
werden automatisch die für die Umgebung nötigen Mandanten zu den SQL Statements hinzugefügt. Zudem ist einfach ein
Zugriff auf die Sysconf möglich::

   print (server.sysconf.getString("STAMM", "MYLAND"))
   print (server.sysconf.getList("STAMM", "EULAENDER"))

Dank der Bibliothek `zeep` ist es auch sehr einfach möglich, auf beliebige SOAP-Methoden zuzugreifen.
Beispielsweise kann auf die Sys-Config auch händisch, d.h. durch direkten Aufruf einer SOAP-Methode,
zugegriffen werden::

   client = server.server_conn.getClient("p2system", "SysConf");
   print (client.service.getString("STAMM", "MYLAND"))


