Abhängigkeiten
==============

pyodbc
------
Für die Datenbankverbindung wird ``pyodbc`` (``python -m pip install pyodbc``) verwendet.
Der passende ODBC Treiber, MS SQL Server 2012 Native Client, wird zusätzlich benötigt.
Dieser kann von Microsoft bezogen werden.


zeep
----
Die Soap-Library ``zeep`` wird benutzt (``python -m pip install zeep``).


requests-negotiate-sspi
-----------------------
Die Authentifzierungsmethode Negotiate Wird für Zugriffe auf ASMX-Seiten benutzt (``python -m pip install requests-negotiate-sspi``).
Leider ist dies nur unter Windows verfügbar. Alle anderen Funktionen können aber auch ohne
dieses Paket benutzt werden.


PyYaml
------

Die Library ``pyyaml`` wird für Config-Dateien benutzt (``python -m pip install pyyaml``).


Sphinx
------
Diese Dokumentation ist mit Sphinx geschrieben.
``python -m pip install sphinx``. Dokumentation ist im Unterverzeichnis
`docs` zu finden. Sie kann mittels ``make.bat html`` erzeugt werden,
dies ruft intern ``sphinx-build -M html source build`` auf. Die Dokumentation
der Python-API sollte evtl. vorher
mittels ``sphinx-apidoc -T -f ../src/PyAPplus64 -o source/generated`` erzeugt
oder aktualisiert werden. Evtl. können 2 Aufrufe von ``make.bat html`` sinnvoll
sein, falls sich die Struktur der Dokumentation ändert.
Diese Aufrufe werden von ``builddocs.sh`` automatisiert.

Die erzeugte Doku findet sich im Verzeichnis ``build/html``.


Pandas / SqlAlchemy / xlsxwriter
--------------------------------
Sollen Excel-Dateien mit Pandas erzeugt, werden, so muss Pandas, SqlAlchemy und xlsxwriter installiert sein
(`python -m pip install pandas sqlalchemy xlsxwriter`).


PySimpleGUI und andere 
----------------------
Einige Beispiele benutzen PySimpleGUI (``python -m pip install pysimplegui``)
sowie teilweise spezielle Bibliotheken etwa zum Pretty-Printing von SQL (``python -m pip install sqlparse sqlfmt``). Dies
sind aber Abhängigkeiten von Beispielen, nicht der Bibliothek selbst.
