# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import PySimpleGUI as sg  # type: ignore
import PyAPplus64
import applus_configs
import pathlib
from typing import Tuple, Optional, Union

try:
    import sqlparse
except:
    pass    

try:
    import sqlfmt.api
except:
    pass    

def prettyPrintSQL(format, sql):
    try:
        if format == "sqlfmt":
            mode = sqlfmt.api.Mode(dialect_name="ClickHouse")
            sqlPretty = sqlfmt.api.format_string(sql, mode)
            return sqlPretty.replace("N '", "N'") # fix String Constants
        elif format == "sqlparse-2":
            return sqlparse.format(sql, reindent=True, keyword_case='upper')        
        elif format == "sqlparse":
            return sqlparse.format(sql, reindent_aligned=True, keyword_case='upper')        
        else:
            return sql
    except e:
        print (str(e))
        return sql

def main() -> None:
    monospaceFont = ("Courier New", 12)
    sysenvs = applus_configs.serverConfDescs[:];
    sysenvs.append("-");
    layout = [
        [sg.Button("Vervollständigen"), sg.Button("aus Clipboard", key="import"), sg.Button("nach Clipboard", key="export"), sg.Button("zurücksetzen", key="clear"), sg.Button("Beenden"),
         sg.Text('System/Umgebung:'), sg.Combo(sysenvs, default_value="-", key="sysenv", readonly=True), sg.Text('Formatierung:'), sg.Combo(["-", "sqlfmt", "sqlparse", "sqlparse-2"], default_value="sqlparse", key="formatieren", readonly=True)
         ],
        [sg.Text('Eingabe-SQL')],
        [sg.Multiline(key='input', size=(150, 20), font=monospaceFont)],
        [sg.Text('Ausgabe-SQL')],
        [sg.Multiline(key='output', size=(150, 20), font=monospaceFont, horizontal_scroll=True)]
    ]

    # server = PyAPplus64.applusFromConfigFile(confFile, user=user, env=env)  
    # systemName = server.scripttool.getSystemName() + "/" + server.scripttool.getMandant()
    window = sg.Window("Complete SQL", layout)
    oldSys = None
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Beenden':
            break
        elif event == 'clear':
             window['input'].update("")
             window['output'].update("")
        elif event == 'import':
            try:
                window['input'].update(window.TKroot.clipboard_get())
            except:
                window['input'].update("")
            window['output'].update("")
        elif event == 'export':
            try:
                window.TKroot.clipboard_clear()
                window.TKroot.clipboard_append(window['output'].get())             
            except:
                pass
        elif event == 'Vervollständigen':
            sqlIn = window['input'].get()
            try:
                if sqlIn:
                    sys = window['sysenv'].get()
                    if sys != oldSys:
                        oldSys = sys
                        if sys and sys != "-":
                            server = sys.connect()                                
                        else:
                            server = None
                    if server:
                        sqlOut = server.completeSQL(sqlIn)
                    else:
                        sqlOut = sqlIn                       
                    sqlOut = prettyPrintSQL(window['formatieren'].get(), sqlOut)
                else:
                    sqlOut = ""
            except Exception as e:
                sqlOut = "ERROR: " + str(e)
                sg.popup_error_with_traceback("Fehler bei Vervollständigung", e)
            window['output'].update(value=sqlOut)

    window.close()


if __name__ == "__main__":
    main()
