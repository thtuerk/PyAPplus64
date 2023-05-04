Beispiele
=========

Im Verzeichnis ``examples`` finden sich Python Dateien, die die Verwendung von `PyAPplus64` demonstrieren. 


Config-Dateien
--------------
Viele Scripte teilen sich Einstellungen. Beispielsweise greifen fast alle Scripte irgendwie auf APplus zu und benötigen Informationen,
mit welchem APP-Server, welchem Web-Server und welcher Datenbank sie sich verbinden sollen. Solche Informationen, insbesondere die Passwörter, werden nicht in  
jedem Script gespeichert, sondern nur in den Config-Dateien. Es bietet sich wohl meist an, 3 Konfigdateien zu erstellen, je eine für 
das Deploy-, das Test- und das Prod-System. Ein Beispiel ist im Unterverzeichnis ``examples/applus-server.yaml`` zu finden.

.. literalinclude:: ../../examples/applus-server.yaml
   :language: yaml
   :linenos:
   
Damit nicht in jedem Script immer wieder neu die Konfig-Dateien ausgewählt werden müssen, werden die Konfigs für 
das Prod-, Test- und Deploy-System in ``examples/applus_configs.py`` hinterlegt. Diese wird in allen Scripten importiert,
so dass das Config-Verzeichnis und die darin enthaltenen Configs einfach zur Verfügung stehen.

.. literalinclude:: ../../examples/applus_configs.py
   :language: python
   :linenos:

   
``check_dokumente.py``
-----------------------
Einfaches Beispiel für lesenden und schreibenden Zugriff auf APplus Datenbank.

.. literalinclude:: ../../examples/check_dokumente.py
   :language: python
   :lines: 6-
   :linenos:


``adhoc_report.py``
-------------------
Sehr einfaches Beispiel zur Erstellung einer Excel-Tabelle aus einer SQL-Abfrage.

.. literalinclude:: ../../examples/adhoc_report.py
   :language: python
   :lines: 7-
   :linenos:


``mengenabweichung.py``
-----------------------
Etwas komplizierteres Beispiel zur Erstellung einer Excel-Datei aus SQL-Abfragen.

.. literalinclude:: ../../examples/mengenabweichung.py
   :language: python
   :lines: 9-
   :linenos:

``mengenabweichung_gui.py``
---------------------------
Beispiel für eine sehr einfache GUI, die die Eingabe einfacher Parameter erlaubt.
Die GUI wird um die Erzeugung von Excel-Dateien mit Mengenabweichungen gebaut.

.. literalinclude:: ../../examples/mengenabweichung_gui.pyw
   :language: python
   :lines: 7-
   :linenos:

``copy_artikel.py``
-----------------------
Beispiel, wie Artikel inklusive Arbeitsplan und Stückliste dupliziert werden kann.

.. literalinclude:: ../../examples/copy_artikel.py
   :language: python
   :lines: 21-
   :linenos:
