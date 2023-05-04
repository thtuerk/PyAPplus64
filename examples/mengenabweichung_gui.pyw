# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import PySimpleGUI as sg # type: ignore
import mengenabweichung
import datetime
import PyAPplus64
import applus_configs
import pathlib
from typing import *

def parseDate (dateS:str) -> Tuple[datetime.datetime|None, bool]:
    if dateS is None or dateS == '':
        return (None, True)
    else:
        try:
            return (datetime.datetime.strptime(dateS, '%d.%m.%Y'), True)
        except:
            sg.popup_error("Fehler beim Parsen des Datums '{}'".format(dateS))
            return (None, False)

def createFile(server:PyAPplus64.APplusServer, fileS:str, vonS:str, bisS:str)->None:    
    (von, vonOK) = parseDate(vonS)
    if not vonOK: return
    
    (bis, bisOK) = parseDate(bisS)
    if not bisOK: return

    if (fileS is None) or fileS == '': 
        sg.popup_error("Es wurde keine Ausgabedatei ausgewählt.")
        return
    else:
        file = pathlib.Path(fileS)

    c = mengenabweichung.exportVonBis(server, file.as_posix(), von, bis)
    sg.popup_ok("{} Datensätze erfolgreich in Datei '{}' geschrieben.".format(c, file))


def main(confFile : str|pathlib.Path, user:str|None=None, env:str|None=None) -> None:
    server = PyAPplus64.applusFromConfigFile(confFile, user=user, env=env) 

    layout = [
        [sg.Text(('Bitte geben Sie an, für welchen Zeitraum die '
                  'Mengenabweichungen ausgegeben werden sollen:'))],
        [sg.Text('Von (einschließlich)', size=(15,1)), sg.InputText(key='Von'),
         sg.CalendarButton("Kalender", close_when_date_chosen=True, 
                           target="Von", format='%d.%m.%Y')],
        [sg.Text('Bis (ausschließlich)', size=(15,1)), sg.InputText(key='Bis'),
         sg.CalendarButton("Kalender", close_when_date_chosen=True, 
                           target="Bis", format='%d.%m.%Y')],
        [sg.Text('Ausgabedatei', size=(15,1)), sg.InputText(key='File'),
        sg.FileSaveAs(button_text="wählen", target="File", 
                      file_types = (('Excel Files', '*.xlsx'),), 
                      default_extension = ".xlsx")],
        [sg.Button("Aktueller Monat"), sg.Button("Letzter Monat"), 
         sg.Button("Aktuelles Jahr"), sg.Button("Letztes Jahr")],
        [sg.Button("Speichern"), sg.Button("Beenden")]
    ]

    systemName = server.scripttool.getSystemName() + "/" + server.scripttool.getMandant()
    window = sg.Window("Mengenabweichung " + systemName, layout)
    now = datetime.date.today()
    (cmonth, cyear) = (now.month, now.year)
    (pyear, pmonth) = mengenabweichung.computePreviousMonthYear(cyear, cmonth);
    (nyear, nmonth) = mengenabweichung.computeNextMonthYear(cyear, cmonth);

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Beenden':
            break
        if event == 'Aktueller Monat':
            window['Von'].update(value="01.{:02d}.{:04d}".format(cmonth, cyear));
            window['Bis'].update(value="01.{:02d}.{:04d}".format(nmonth, nyear));
        if event == 'Letzter Monat':
            window['Von'].update(value="01.{:02d}.{:04d}".format(pmonth, pyear));
            window['Bis'].update(value="01.{:02d}.{:04d}".format(cmonth, cyear));
        if event == 'Aktuelles Jahr':
            window['Von'].update(value="01.01.{:04d}".format(cyear));
            window['Bis'].update(value="01.01.{:04d}".format(cyear+1));
        if event == 'Letztes Jahr':
            window['Von'].update(value="01.01.{:04d}".format(cyear-1));
            window['Bis'].update(value="01.01.{:04d}".format(cyear));
        if event == 'Speichern':
            try:
                createFile(server, values.get('File', None), 
                           values.get('Von', None), values.get('Bis', None))
            except Exception as e:
                sg.popup_error_with_traceback("Beim Erzeugen der Excel-Datei trat ein Fehler auf:", e);

    window.close()

if __name__ == "__main__":
    main(applus_configs.serverConfYamlProd)
