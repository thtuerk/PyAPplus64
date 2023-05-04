Beschreibung
============

Das Paket `PyAPplus64` enthält eine Sammlung von Python Tools für die Interaktion mit dem ERP-System APplus 6.4. 
Es sollte auch für andere APplus Versionen nützlich sein. 

Zielgruppe sind APplus-Administratoren und Anpassungs-Entwickler. `PyAPplus64` erlaubt u.a.

- einfacher Zugriff auf SOAP-Schnittstelle des APP-Servers
   + damit Zugriff auf SysConfig
   + Zugriff auf Tools wie z.B. `nextNumber` für Erzeugung der nächsten Nummer für ein Business-Object
   + ...   
- Zugriff auf APplus DB per direktem DB-Zugriff und mittels SOAP
   + automatischer Aufruf von `completeSQL`, um per AppServer SQL-Statements um z.B. Mandanten erweitern zu lassen
   + Tools für einfache Benutzung von `useXML`, d.h. für das Einfügen, Löschen und Ändern von Datensätzen
     mit Hilfe des APP-Servers. Genau wie bei Änderungen an Datensätzen über die Web-Oberfläche und im Gegensatz 
     zum direkten Zugriff über die Datenbank werden dabei evtl. zusätzliche 
     Checks ausgeführt, bestimmte Felder automatisch gesetzt oder bestimmte Aktionen angestoßen. 
- das Duplizieren von Datensätzen
   + zu kopierende Felder aus XML-Definitionen werden ausgewertet
   + Abhängige Objekte können einfach ebenfalls mit-kopiert werden
   + Änderungen wie beispielsweise Nummer des Objektes möglich
   + Unterstützung für Kopieren dyn. Attribute
   + Anlage neuer Objekte mittels APP-Server
   + Datensätze können zwischen Systemen kopiert und auch in Dateien gespeichert werden
   + Beispiel: Kopieren von Artikeln mit Arbeitsplan und Stückliste zwischen Deploy- und Prod-System
- einfaches Erstellen von Excel-Reports aus SQL-Abfragen
   + mittels Pandas und XlsxWriter
   + einfache Wrapper um andere Libraries, spart aber Zeit
- ...

In `PyAPplus64` wurden die Features (vielleicht leicht verallgemeinert)
implementiert, die ich für konkrete Aufgabenstellungen benötigte. Ich gehe davon
aus, dass im Laufe der Zeit weitere Features hinzukommen.

Warnung
-------

`PyAPplus64` erlaubt den schreibenden Zugriff auf die APplus Datenbank und beliebige 
Aufrufe von SOAP-Methoden. Unsachgemäße Nutzung kann Ihre Daten zerstören. Benutzen Sie 
`PyAPplus64` daher bitte vorsichtig. Zudem kann ich leider nicht garantieren, dass `PyAPplus64` fehlerfrei ist. 

