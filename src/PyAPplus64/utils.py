# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

import pathlib
import datetime
from typing import *

def checkDirExists(dir : Union[str, pathlib.Path]) -> pathlib.Path:    
    """Prüft, ob ein Verzeichnis existiert. Ist dies nicht möglich, wird eine Exception geworfen.

    :param dir: das Verzeichnis
    :type dir: Union[str, pathlib.Path]
    :return: den normalisierten Pfad
    :rtype: pathlib.Path
    """

    if not (isinstance(dir, pathlib.Path)):
        dir = pathlib.Path(str(dir))

    dir = dir.resolve()
    if not (dir.exists()):
        raise Exception("Verzeichnis '" + str(dir) + "' nicht gefunden");
        
    if not (dir.is_dir()):
        raise Exception("'" + str(dir) + "' ist kein Verzeichnis");
    return dir;


def formatDateTimeForAPplus(v : Union[datetime.datetime, datetime.date, datetime.time]) -> str:
    """Formatiert ein Datum oder eine Uhrzeit für APplus"""
    if (v == None):
        return "";
    elif isinstance(v, str):
        return v;
    elif isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    elif isinstance(v, datetime.date):
        return v.strftime("%Y-%m-%d")
    elif isinstance(v, datetime.time):
        return v.strftime("%H:%M:%S.%f")[:-3]
    else:
        return str(v)
   
def containsOnlyAllowedChars(charset : Set[str], s : str) -> bool:
    """Enthält ein String nur erlaubte Zeichen?"""
    for c in s:
        if not (c in charset): 
            return False
    return True
