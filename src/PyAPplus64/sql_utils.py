# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

#-*- coding: utf-8 -*-
"""
Diese Datei enthält Funktionen für den Bau von SQL Statements, besonders
SELECT-Statements. Es gibt viel ausgefeiltere Methoden für die Erstellung von
SQL Statements. APplus benötigt jedoch die Statements als Strings, die dann an
APplus für Änderungen und erst danach an die DB geschickt werden. Dies erschwert
die Nutzung von Tools wie SqlAlchemy.

Hier werden einfache Hilfsfunktionen, die auf Strings basieren, zur Verfügung
gestellt. PyODBC erlaubt Parameter (dargestellt als '?') in SQL Statements, die
dann beim Aufruf gefüllt werden. Dies funktioniert auch im Zusammenspiel mit
APplus. Oft ist es sinnvoll, solche Parameter zu verwenden.
"""

from __future__ import annotations
import datetime
from typing import *

def normaliseDBfield(f : str) -> str:
    """Normalisiert die Darstellung eines DB-Feldes"""
    return str(f).upper();

def normaliseDBfieldSet(s : Set[str]) -> Set[str]:
    """Normalisiert eine Menge von DB-Feldern"""
    return {normaliseDBfield(f) for f in s}

def normaliseDBfieldList(l : Sequence[str]) -> Sequence[str]:
    """Normalisiert eine Menge von DB-Feldern"""
    return [normaliseDBfield(f) for f in l]


class SqlField():
    """
    Wrapper um SQL Feldnamen, die die Formatierung erleichtern
    
    :param fn: der Feldname
    :type fn: str
    """
    def __init__(self, fn : str):
        self.field = normaliseDBfield(fn);

    def __str__(self) -> str:
        return self.field;

class SqlFixed():
    """
    Wrapper um Strings, die ohne Änderung in SQL übernommen werden
    
    :param s: der string
    :type s: str
    """
    def __init__(self, s : str):
        self.s = str(s);

    def __str__(self) -> str:
        return self.s;

class SqlDateTime():
    """
    Wrapper um DateTime, die die Formatierung erleichtern

    :param dt: der Zeitpunkt
    :type dt: Union[datetime.datetime, datetime.date]
    """
    def __init__(self, dt:Union[datetime.datetime, datetime.date]=datetime.datetime.now()) -> None:        
        self.value = dt;

    def __str__(self) -> str:
        # %f formatiert mit 6 Stellen, also microseconds. Es werden aber nur 
        # 3 Stellen unterstützt, daher werden 3 weggeworfen.
        return self.value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

class SqlDate():
    """
    Wrapper um DateTime, die die Formatierung erleichtern

    :param d: das Datum
    :type d: Union[datetime.datetime, datetime.date]
    """
    def __init__(self, d:Union[datetime.datetime, datetime.date]=datetime.datetime.now()) -> None:        
        self.value = d;

    def __str__(self) -> str:
        return self.value.strftime("%Y%m%d");

class SqlTime():
    """
    Wrapper um DateTime, die die Formatierung erleichtern

    :param t: die Zeit
    :type t: Union[datetime.datetime, datetime.time]
    """
    def __init__(self, t:Union[datetime.datetime, datetime.time]=datetime.datetime.now()) -> None:        
        self.value = t

    def __str__(self) -> str:
        return self.value.strftime("%H:%M:%S.%f")[:-3]

class SqlParam():
    """Hilfsklasse, für einen Parameter (?)"""
    def __init__(self) -> None:
        pass 

    def __str__(self) -> str:
        return "?"

sqlParam = SqlParam()
"""Da SqlParam keinen Zustand hat, reicht ein einzelner statischer Wert"""

def formatSqlValueString(s:str) -> str:
    """
    Formatiert einen String für ein Sql-Statement. Der String wird in "'" eingeschlossen 
    und Hochkomma im Text maskiert.

    :param s: der String
    :type s: str
    :return: der formatierte String
    :rtype: str
    """

    if (s is None): 
        return "''";

    return "'" + str(s).replace("'", "''") + "'";


SqlValue : TypeAlias = Union[str, int, float, SqlParam, SqlField, SqlFixed, SqlDate, SqlDateTime, datetime.datetime, datetime.date, datetime.time]
"""Union-Type aller unterstützter SQL-Werte"""

def formatSqlValue(v : SqlValue) -> str:
    """
    Formatiert einen Wert für SQL. Je nachdem um welchen Typ es sich handelt, werden andere Formatierungen verwendet.

    :param v: der Wert
    :type v: SqlValue
    :return: der formatierte Wert
    :rtype: str
    """

    if (v == None):
        raise Exception("formatSqlValue: null not supported");

    if isinstance(v, (int, float, SqlField)):
        return str(v);
    elif isinstance(v, str):
        return formatSqlValueString(v);
    elif isinstance(v, datetime.datetime):
        return "'" + str(SqlDateTime(v)) + "'";
    elif isinstance(v, datetime.date):
        return "'" + str(SqlDate(v)) + "'";
    elif isinstance(v, datetime.time):
        return "'" + str(SqlTime(v)) + "'";
    elif isinstance(v, (SqlDateTime, SqlDate, SqlTime)):
        return "'" + str(v) + "'";
    elif isinstance(v, (SqlParam, SqlFixed)):
        return str(v);
    else:
        raise Exception("formatSqlValue: unsupported type {}".format(type(v)));

class SqlCondition():
    """Eine abstrakte Sql-Bedingung. Unterklassen erledigen die eigentliche Arbeit."""
    
    def getCondition(self) -> str:
        """
        Liefert die Bedingung als String
        
        :return: die Bedingung 
        :rtype: str
        """ 
        raise Exception("Not implemented");

    def __str__(self) -> str:
        return self.getCondition();


class SqlConditionPrepared(SqlCondition):
    """Eine einfache Sql-Bedingung, die immer einen festen String zurückgibt."""

    def __init__(self, cond : Union[SqlCondition, str]):
        self.cond = str(cond);

    def getCondition(self) -> str:
        return self.cond;

class SqlConditionTrue(SqlConditionPrepared):
    """True-Bedingung"""

    def __init__(self) -> None:
        super().__init__("(1=1)")

class SqlConditionFalse(SqlConditionPrepared):
    """False-Bedingung"""

    def __init__(self) -> None:
        super().__init__("(1=0)")

class SqlConditionBool(SqlConditionPrepared):
    """Fixe True-oder-False Bedingung"""

    def __init__(self, b : bool):
        if b:
            super().__init__(SqlConditionTrue())
        else:
            super().__init__(SqlConditionFalse())

class SqlConditionNot(SqlCondition):
    """
    Negation einer anderen Bedingung

    :param cond: die zu negierende Bedingung
    :type cond: SqlCondition    
    """

    def __init__(self, cond : SqlCondition):
        self.cond = cond;

    def getCondition(self) -> str:
        return "(not {})".format(self.cond.getCondition());


class SqlConditionIsNull(SqlConditionPrepared):
    """
    Wert soll null sein

    :param v: das Feld
    :type v: SqlValue
    """

    def __init__(self, v : SqlValue):
        super().__init__("({} is null)".format(formatSqlValue(v)))

class SqlConditionFieldIsNull(SqlConditionIsNull):
    def __init__(self, field : str):
        super().__init__(SqlField(field))

class SqlConditionIsNotNull(SqlConditionPrepared):
    """
    Wert soll nicht null sein

    :param v: der Wert
    :type v: SqlValue
    """

    def __init__(self, v : SqlValue):
        super().__init__("({} is not null)".format(formatSqlValue(v)))

class SqlConditionFieldIsNotNull(SqlConditionIsNotNull):
    def __init__(self, field : str):
        super().__init__(SqlField(field))
    
class SqlConditionStringStartsWith(SqlConditionPrepared):
    """
    Feld soll mit einem bestimmten String beginnen

    :param field: das Feld
    :type field: str
    :param value: der Wert
    :type value: str
    """

    def __init__(self, field : str, value : str):
        cond = "";
        if value:
            cond="(left({}, {}) = {})".format(normaliseDBfield(field), len(value), formatSqlValueString(value));
        else:
            cond = "(1=1)"        
        super().__init__(cond)


class SqlConditionFieldStringNotEmpty(SqlConditionPrepared):
    """
    Feld soll nicht den leeren String oder null enthalten.
    Der Ausdruck wird wörtlich übernommen.

    :param field: das Feld
    :type field: str
    """

    def __init__(self, field : str):
        field = normaliseDBfield(field);
        cond="({} is not null and {} != '')".format(field, field);
        super().__init__(cond)


class SqlConditionIn(SqlConditionPrepared):
    """    
    Bedingung der Form 'v in ...'

    :param value: der Wert, kann unterschiedliche Typen besitzen    
    :type value: SqlValue
    :param values: die erlaubten Werte
    :type values: Sequence[SqlValue]
    """
    def __init__(self, value : SqlValue, values : Sequence[SqlValue]):
        valuesLen = len(values)
        if (valuesLen == 0):            
            cond : Union[SqlCondition, str] = SqlConditionFalse()
        elif (valuesLen == 1):
            cond = SqlConditionEq(value, values[0])
        else:
            valuesS = formatSqlValue(values[0])
            for i in range(1, valuesLen):
                valuesS += ", " + formatSqlValue(values[i])
            cond = "({} in ({}))".format(formatSqlValue(value), valuesS)
        super().__init__(cond)
 
class SqlConditionFieldIn(SqlConditionIn):
    def __init__(self, field:str, values : Sequence[SqlValue]):
        super().__init__(SqlField(field), values)


class SqlConditionEq(SqlConditionPrepared):
    """    
    Bedingung der Form 'v1 is null', 'v2 is null', 'v1 = v2', '(1=1)' oder '(0=1)'

    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    """
    def __init__(self, value1 : Optional[Union[SqlValue, bool]], value2 : Optional[Union[SqlValue, bool]]):
        cond: Union[SqlCondition, str]
        if (value1 is None) and (value2 is None):
            cond = SqlConditionTrue()
        elif (value1 is None) and not (value2 is None):
            if (isinstance(value2, bool)):
                cond = SqlConditionFalse()
            else:
                cond = SqlConditionIsNull(value2)
        elif not (value1 is None) and (value2 is None):
            if (isinstance(value1, bool)):
                cond = SqlConditionFalse()
            else:
                cond = SqlConditionIsNull(value1)
        else:
            if isinstance(value1, bool) and isinstance(value2, bool):
                cond = SqlConditionBool(value1 == value2);
            elif isinstance(value1, bool) and not isinstance(value2, bool):
                value2 = cast(SqlValue, value2)
                if value1:
                    cond = "({} = 1)".format(formatSqlValue(value2))
                else:
                    cond = "({} = 0 OR {} is null)".format(formatSqlValue(value2), formatSqlValue(value2));
            elif not isinstance(value1, bool) and isinstance(value2, bool):
                value1 = cast(SqlValue, value1)
                if value2:
                    cond = "({} = 1)".format(formatSqlValue(value1))
                else:
                    cond = "({} = 0 OR {} is null)".format(formatSqlValue(value1), formatSqlValue(value1))
            else:
                value1 = cast(SqlValue, value1)
                value2 = cast(SqlValue, value2)
                cond = "({} = {})".format(formatSqlValue(value1), formatSqlValue(value2));
        super().__init__(cond)


class SqlConditionBinComp(SqlConditionPrepared):
    """    
    Bedingung der Form 'value1 op value2'

    :param op: der Vergleichsoperator
    :type op: str
    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :type value1: SqlValue
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    :type value2: SqlValue
    """
    def __init__(self, op : str, value1 : SqlValue, value2 : SqlValue):
        if not(value1) or not(value2):
            raise Exception("SqlConditionBinComp: value not provided")

        cond = "({} {} {})".format(formatSqlValue(value1), op, formatSqlValue(value2));
        super().__init__(cond)


class SqlConditionLt(SqlConditionBinComp):
    """    
    Bedingung der Form 'value1 < value2'

    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    """
    def __init__(self, value1 : SqlValue, value2 : SqlValue):
       super().__init__("<", value1, value2)

class SqlConditionLe(SqlConditionBinComp):
    """    
    Bedingung der Form 'value1 <= value2'

    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    """
    def __init__(self, value1 : SqlValue, value2 : SqlValue):
       super().__init__("<=", value1, value2)

class SqlConditionGt(SqlConditionBinComp):
    """    
    Bedingung der Form 'value1 > value2'

    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    """
    def __init__(self, value1 : SqlValue, value2 : SqlValue):
       super().__init__(">", value1, value2)

class SqlConditionGe(SqlConditionBinComp):
    """    
    Bedingung der Form 'value1 >= value2'

    :param value1: der Wert, kann unterschiedliche Typen besitzen    
    :param value2: der Wert, kann unterschiedliche Typen besitzen    
    """
    def __init__(self, value1 : SqlValue, value2 : SqlValue):
       super().__init__(">=", value1, value2)


class SqlConditionFieldEq(SqlConditionEq):
    def __init__(self, field : str, value : Optional[Union[SqlValue, bool]]):
        super().__init__(SqlField(field), value)

class SqlConditionFieldLt(SqlConditionLt):
    def __init__(self, field : str, value : SqlValue):
        super().__init__(SqlField(field), value)

class SqlConditionFieldLe(SqlConditionLe):
    def __init__(self, field : str, value : SqlValue):
        super().__init__(SqlField(field), value)

class SqlConditionFieldGt(SqlConditionGt):
    def __init__(self, field : str, value : SqlValue):
        super().__init__(SqlField(field), value)

class SqlConditionFieldGe(SqlConditionGe):
    def __init__(self, field : str, value : SqlValue):
        super().__init__(SqlField(field), value)
  
class SqlConditionList(SqlCondition):
    """
    Eine SQL Bedingung, die sich aus einer Liste anderer Bedingungen zusammensetzen.
    Dies kann eine "AND" oder eine "OR" Liste sein.
    
    :param connector: wie werden Listenelemente verbunden (AND oder OR)
    :type connector: str 
    :param emptyCond: Rückgabewert für leere Liste
    :type emptyCond: str
    """

    def __init__(self, connector : str, emptyCond : str):
        self.connector : str = connector;
        self.emptyCond : str = emptyCond;
        self.elems : List[SqlCondition] = []
    
    def addCondition(self, cond : SqlCondition | str | None) -> None:
        if (cond is None):
            return
        if not (isinstance(cond, SqlCondition)):
            cond = SqlConditionPrepared("("+str(cond)+")");
        self.elems.append(cond);

    def addConditions(self, *conds : SqlCondition | str | None) -> None:
        for cond in conds:
            self.addCondition(cond)

    def addConditionFieldStringNotEmpty(self, field : str) -> None:
        self.addCondition(SqlConditionFieldStringNotEmpty(field));

    def addConditionFieldIn(self, field : str, values : Sequence[SqlValue]) -> None:
        self.addCondition(SqlConditionFieldIn(field, values));

    def addConditionFieldEq(self, field : str, value : Optional[Union[SqlValue, bool]]) -> None:
        self.addCondition(SqlConditionFieldEq(field, value));

    def addConditionFieldsEq(self, field1 : str, field2 : str) -> None:
        self.addCondition(SqlConditionEq(SqlField(field1), SqlField(field2)));

    def addConditionEq(self, value1 : Optional[Union[SqlValue, bool]], value2 : Optional[Union[SqlValue, bool]]) -> None:
        self.addCondition(SqlConditionEq(value1, value2));

    def addConditionGe(self, value1 : SqlValue, value2 : SqlValue) -> None:
        self.addCondition(SqlConditionGe(value1, value2));

    def addConditionFieldGe(self, field : str, value : SqlValue) -> None:
        self.addCondition(SqlConditionGe(SqlField(field), value));

    def addConditionFieldsGe(self, field1 : str, field2 : str) -> None:
        self.addCondition(SqlConditionGe(SqlField(field1), SqlField(field2)));

    def addConditionLe(self, value1 : SqlValue, value2 : SqlValue) -> None:
        self.addCondition(SqlConditionLe(value1, value2));

    def addConditionFieldLe(self, field : str, value : SqlValue) -> None:
        self.addCondition(SqlConditionLe(SqlField(field), value));

    def addConditionFieldsLe(self, field1 : str, field2 : str) -> None:
        self.addCondition(SqlConditionLe(SqlField(field1), SqlField(field2)));

    def addConditionGt(self, value1 : SqlValue, value2 : SqlValue) -> None:
        self.addCondition(SqlConditionGt(value1, value2));

    def addConditionFieldGt(self, field : str, value : SqlValue) -> None:
        self.addCondition(SqlConditionGt(SqlField(field), value));

    def addConditionFieldsGt(self, field1 : str, field2 : str) -> None:
        self.addCondition(SqlConditionGt(SqlField(field1), SqlField(field2)));

    def addConditionLt(self, value1 : SqlValue, value2 : SqlValue) -> None:
        self.addCondition(SqlConditionLt(value1, value2));

    def addConditionFieldLt(self, field : str, value : SqlValue) -> None:
        self.addCondition(SqlConditionLt(SqlField(field), value));

    def addConditionFieldsLt(self, field1 : str, field2 : str) -> None:
        self.addCondition(SqlConditionLt(SqlField(field1), SqlField(field2)));

    def addConditionFieldIsNull(self, field : str) -> None:
        self.addCondition(SqlConditionFieldIsNull(field));

    def addConditionFieldIsNotNull(self, field : str) -> None:
        self.addCondition(SqlConditionFieldIsNotNull(field));

    def isEmpty(self) -> bool:
        return not(self.elems);

    def getCondition(self) -> str:
        match (len(self.elems)):
            case 0:
                return self.emptyCond;
            case 1:
                return self.elems[0].getCondition();
            case l:
                res = "(" + self.elems[0].getCondition();
                for i in range(1, l):
                    res += " {} {}".format(self.connector, self.elems[i].getCondition())
                res += ")";
                return res;


class SqlConditionDateTimeFieldInRange(SqlConditionPrepared):
    """    
    Liegt Datetime in einem bestimmten Zeitraum?

    :param field: das Feld
    :type field: str
    :param datetimeVon: der untere Wert (einschließlich), None erlaubt beliebige Zeiten
    :param datetimeBis: der obere Wert (ausschließlich), None erlaubt beliebige Zeiten
    """
    def __init__(self, field : str, datetimeVon : datetime.datetime|None, datetimeBis : datetime.datetime|None):
        cond = SqlConditionAnd()
        if not (datetimeVon is None):
            cond.addConditionFieldGe(field, datetimeVon)
        if not (datetimeBis is None):
            cond.addConditionFieldLt(field, datetimeBis)
        super().__init__(str(cond))

class SqlConditionDateTimeFieldInMonth(SqlConditionPrepared):
    """    
    Liegt Datetime in einem bestimmten Monat?

    :param field: das Feld
    :type field: string
    :param year: das Jahr
    :param month: der Monat
    """
    def __init__(self, field : str, year : int, month : int):
        if month == 12:
            nyear=year+1
            nmonth=1;
        else:
            nyear=year
            nmonth=month+1;
        cond = SqlConditionDateTimeFieldInRange(field, 
                  datetime.datetime(year=year, month=month, day=1), 
                  datetime.datetime(year=nyear, month=nmonth, day=1))
        super().__init__(str(cond))

class SqlConditionDateTimeFieldInYear(SqlConditionPrepared):
    """    
    Liegt Datetime in einem bestimmten Jahr?

    :param field: das Feld
    :type field: str
    :param year: das Jahr
    """
    def __init__(self, field : str, year :int) -> None:
        nyear=year+1
        cond = SqlConditionDateTimeFieldInRange(field, 
                  datetime.datetime(year=year, month=1, day=1), 
                  datetime.datetime(year=nyear, month=1, day=1))
        super().__init__(str(cond))

class SqlConditionDateTimeFieldInDay(SqlConditionPrepared):
    """    
    Liegt Datetime in einem bestimmten Monat?

    :param field: das Feld
    :type field: str
    :param year: das Jahr
    :param month: der Monat
    :param day: der Tag
    """
    def __init__(self, field : str, year : int, month : int, day : int) -> None:
        d = datetime.datetime(year=year, month=month, day=day)
        cond = SqlConditionDateTimeFieldInRange(field, 
                d,
                d + datetime.timedelta(days=1))
        super().__init__(str(cond))

class SqlConditionAnd(SqlConditionList):
    def __init__(self, *conds : Union[SqlCondition, str]) -> None:
        super().__init__("AND", "(1=1)")
        self.addConditions(*conds)

class SqlConditionOr(SqlConditionList):
    def __init__(self, *conds : Union[SqlCondition, str]) -> None:
        super().__init__("OR", "(1=0)")
        self.addConditions(*conds)


class SqlJoin():
    """
    Ein abstrakter Sql-Join

    :param joinType: Art des Joins, wird in SQL übernommen, z.B. "LEFT JOIN".
    :type joinType: str
    :param table: die Tabelle, die gejoint werden soll
    :type table: str
    :param conds: Bedingungen, die bereits hinzugefügt werden soll. Weitere können über Attribut `on` hinzugefügt werden.
    
    """
    
    def __init__(self, joinType : str, table : str, *conds : Union[SqlCondition, str]) -> None:       
        self.joinType = joinType
        self.table = table

        self.on : SqlConditionAnd = SqlConditionAnd(*conds)
        """Bedingung des Joins, kann noch nachträglich erweitert werden"""
        
    def getJoin(self) -> str:
        """
        Liefert den Join als String       
        """ 
        return self.joinType + " " + self.table + " ON " + self.on.getCondition();

    def __str__(self) -> str:
        return self.getJoin();


class SqlInnerJoin(SqlJoin):
    """
    Ein Inner-Join.

    :param table: die Tabelle, die gejoint werden soll
    :type table: str
    :param conds: Bedingungen, die bereits hinzugefügt werden soll. Weitere können über Attribut `on` hinzugefügt werden.
    """

    def __init__(self, table : str, *conds : Union[SqlCondition, str]) -> None:
        super().__init__("INNER JOIN", table, *conds)

class SqlLeftJoin(SqlJoin):
    """
    Ein Left-Join.

    :param table: die Tabelle, die gejoint werden soll
    :type table: str
    :param conds: Bedingungen, die bereits hinzugefügt werden soll. Weitere können über Attribut `on` hinzugefügt werden.
    """
    def __init__(self, table : str, *conds : Union[SqlCondition, str]) -> None:
        super().__init__("LEFT JOIN", table, *conds)

class SqlStatementSelect():
    """
    Klasse, um einfache Select-Statements zu bauen.

    :param table: die Haupt-Tabelle
    :type table: str
    :param fields: kein oder mehrere Felder, die selektiert werden sollen    
    """

    def __init__(self, table : str, *fields : str) -> None:
        self.table : str = table
        """die Tabelle"""
        
        self.top : int = 0
        """wie viele Datensätze auswählen? 0 für alle"""

        self.where : SqlConditionList = SqlConditionAnd();
        """die Bedingung, Default ist True"""

        self.fields : List[str] = []        
        """Liste von auszuwählenden Feldern"""
        self.addFields(*fields)

        self.joins : List[SqlJoin|str] = []
        """Joins mit extra Tabellen"""

        self.groupBy : List[str] = [];
        """die Bedingung, Default ist True"""

        self.having : SqlConditionList = SqlConditionAnd();
        """die Bedingung having, Default ist True"""

        self.order : Optional[str] = None
        """Sortierung"""

    def __str__(self) -> str:
        return self.getSql();

    def addFields(self, *fields : str) -> None:
        """Fügt ein oder mehrere Felder, also auszuwählende Werte zu einem SQL-Statement hinzu."""
        for f in fields:
            if not (f == None):
                self.fields.append(f)

    def addGroupBy(self, *fields : str) -> None:
        """Fügt ein oder mehrere GroupBy Felder zu einem SQL-Statement hinzu."""
        for f in fields:
            if not (f == None):
                self.groupBy.append(f)

    def setTop(self, t : int) -> None:
        """Wie viele Datensätze sollen maximal zurückgeliefert werden? 0 für alle"""
        self.top = t

    def addFieldsTable(self, table : str, *fields : str) -> None:
        """
        Fügt ein oder mehrere Felder, die zu einer Tabelle gehören zu einem SQL-Statement hinzu.
        Felder sind Strings. Vor jeden dieser Strings wird die Tabelle mit einem Punkt getrennt gesetzt.
        Dies kann im Vergleich zu 'addFields' Schreibarbeit erleitern.
        """
        for f in fields:
            if not (f == None):
                self.fields.append(table + "." + str(f))

    def addJoin(self, j : SqlJoin|str) -> None:
        """Fügt ein Join zum SQL-Statement hinzu. Beispiel: 'LEFT JOIN personal p ON t.UPDUSER = p.PERSONAL'"""
        self.joins.append(j)

    def addLeftJoin(self, table : str, *conds : Union[SqlCondition, str]) -> SqlLeftJoin:
        j = SqlLeftJoin(table, *conds)
        self.addJoin(j)
        return j

    def addInnerJoin(self, table : str, *conds : Union[SqlCondition, str]) ->  SqlInnerJoin:
        j = SqlInnerJoin(table, *conds)
        self.addJoin(j)
        return j

    def getSql(self) -> str:
        """Liefert das SQL-SELECT-Statement als String"""
        def getFields() -> str:
            match (len(self.fields)):
                case 0:
                    return "*";
                case 1:
                    return str(self.fields[0]);
                case l:
                    res = str(self.fields[0]);
                    for i in range(1, l):
                        res += ", " + str(self.fields[i]);
                    return res;

        def getGroupBy() -> str:
            match (len(self.groupBy)):
                case 0:
                    return "";
                case l:
                    res = " GROUP BY " + str(self.fields[0])
                    for i in range(1, l):
                        res += ", " + str(self.fields[i]);
                    if not (self.having.isEmpty()): 
                        res += " HAVING " + str(self.having)                    
                    return res;

        def getJoins() -> str:
            match (len(self.joins)):
                case 0:
                    return ""
                case l:
                    res = "";
                    for i in range(0, l):
                        res += " " + str(self.joins[i])
                    return res

        def getWhere() -> str:
            if self.where.isEmpty(): 
                return ""
            else:
                return " WHERE " + str(self.where)

        def getOrder() -> str:
            if self.order == None:
                return ""
            else:
                return " ORDER BY " + str(self.order)
        
        def getTop() -> str:
            if self.top <= 0:
                return ""
            else:
                return "TOP " + str(self.top) + " "

        return "SELECT " + getTop() + getFields() + " FROM " + self.table + getJoins() + getWhere() + getGroupBy() + getOrder();


SqlStatement : TypeAlias = Union [SqlStatementSelect, str]

