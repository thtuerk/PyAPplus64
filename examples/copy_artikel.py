# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

# Dieses Script demonstriert, wie mit Hilfe PyAPplus64.duplicate
# BusinessObjekte dupliziert werden können.
# Dies ist sowohl in der gleichen DB als auch in anderen DBs möglich.
# So kann z.B. ein einzelner Artikel aus Test in Prod kopiert werden.
# Ebenso ist es möglich, die Daten in einer Datei zwischenzuspeichern und
# später irgendwo anders einzuspielen.
#
# Dies ist für Administrationszwecke gedacht. Anwendungsbeispiel wäre,
# dass ein Artikel mit langem Arbeitsplan und Stückliste im Test-System erstellt wird.
# Viele der Positionen enthalten Nachauflöse-Scripte, die im Test-System 
# getestet werden. Diese vielen Scripte per Hand zu kopieren ist aufwändig
# und Fehleranfällig und kann mit solchen Admin-Scripten automatisiert werden.

import pathlib
import PyAPplus64
import applus_configs
import logging
import yaml 


def main(confFile:pathlib.Path, artikel:str, artikelNeu:str|None=None) -> None:
    # Server verbinden
    server = PyAPplus64.applus.applusFromConfigFile(confFile) 

    # DuplicateBusinessObject für Artikel erstellen
    dArt = PyAPplus64.duplicate.loadDBDuplicateArtikel(server, artikel);

    # DuplicateBusinessObject zur Demonstration in YAML konvertieren und zurück
    dArtYaml = yaml.dump(dArt);
    print(dArtYaml);
    dArt2 = yaml.load(dArtYaml, Loader=yaml.UnsafeLoader)

    # Neue Artikel-Nummer bestimmen und DuplicateBusinessObject in DB schreiben
    # Man könnte hier genauso gut einen anderen Server verwenden
    if (artikelNeu is None):
        artikelNeu = server.nextNumber("Artikel")

    if not (dArt is None):
        dArt.setFields({"artikel" : artikelNeu})
        res = dArt.insert(server);
        print(res);


if __name__ == "__main__":
    # Logger Einrichten
    logging.basicConfig(level=logging.INFO) 
    # logger = logging.getLogger("PyAPplus64.applus_db");
    # logger.setLevel(logging.ERROR)

    main(applus_configs.serverConfYamlTest, "my-artikel", artikelNeu="my-artikel-copy")

