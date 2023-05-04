# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-

from typing import *

if TYPE_CHECKING: 
    from .applus import APplusServer


class APplusSysConf:
    """
    SysConf Zugriff mit Cache über AppServer

    :param server: die Verbindung zum Server
    :type server: APplusServer

    """
    
    def __init__(self, server : 'APplusServer') -> None:
        self.client = server.getClient("p2system", "SysConf")
        self.cache : Dict[str, type] = {}

    def clearCache(self) -> None:
        self.cache = {};

    def _getGeneral(self, ty:str, f : Callable[[str, str], Any], module:str, name:str, useCache:bool) -> Any:
        cacheKey = module + "/" + name + "/" + ty;
        if useCache and cacheKey in self.cache:
            return self.cache[cacheKey]
        else:
            v = f(module, name);
            self.cache[cacheKey] = v;
            return v;

    def getString(self, module:str, name:str, useCache:bool=True) -> str:
        return self._getGeneral("string", self.client.service.getString, module, name, useCache);

    def getInt(self, module:str, name:str, useCache:bool=True) -> int:
        return self._getGeneral("int", self.client.service.getInt, module, name, useCache);

    def getDouble(self, module:str, name:str, useCache:bool=True) -> float:
        return self._getGeneral("double", self.client.service.getDouble, module, name, useCache);

    def getBoolean(self, module:str, name:str, useCache:bool=True) -> bool:
        return self._getGeneral("boolean", self.client.service.getBoolean, module, name, useCache);

    def getList(self, module : str, name:str, useCache:bool=True, sep:str=",") -> Optional[Sequence[str]]:
        s = self.getString(module, name, useCache=useCache);
        if (s == None or s == ""): 
            return None

        return s.split(sep);
