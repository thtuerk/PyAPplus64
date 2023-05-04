# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from PyAPplus64 import sql_utils
import datetime

def test_normaliseDBField1() -> None:    
    assert (sql_utils.normaliseDBfield("aAa") == "AAA")
    assert (sql_utils.normaliseDBfield("a#Aa") == "A#AA")
    assert (sql_utils.normaliseDBfield("2") == "2")

def test_normaliseDBFieldSet() -> None:    
    assert (sql_utils.normaliseDBfieldSet(set()) == set())
    assert (sql_utils.normaliseDBfieldSet({"aAa", "b", "c", "2"}) == {"2", "AAA", "B", "C"})

def test_normaliseDBFieldList() -> None:    
    assert (sql_utils.normaliseDBfieldList([]) == [])
    assert (sql_utils.normaliseDBfieldList(["aAa", "b", "c", "2"]) == ["AAA", "B", "C", "2"])

def test_SqlField1() -> None:
    assert (str(sql_utils.SqlField("abc")) == "ABC")

def test_SqlField2() -> None:
    assert (str(sql_utils.SqlField("t.abc")) == "T.ABC")

def test_SqlParam() -> None:
    assert (str(sql_utils.sqlParam) == "?")

def test_SqlDateTime() -> None:
    dt = datetime.datetime(year=2023, month=1, day=12, hour=9, minute=59, second=12, microsecond=2344)
    assert (str(sql_utils.SqlDateTime(dt)) == "2023-01-12T09:59:12.002")

def test_SqlDate() -> None:
    dt = datetime.datetime(year=2023, month=1, day=12, hour=9, minute=59, second=12, microsecond=2344)
    assert (str(sql_utils.SqlDate(dt)) == "20230112")

def test_formatSqlValueString1() -> None:
    assert(sql_utils.formatSqlValueString("") == "''");

def test_formatSqlValueString2() -> None:
    assert(sql_utils.formatSqlValueString("abc") == "'abc'");

def test_formatSqlValueString3() -> None:
    assert(sql_utils.formatSqlValueString("a b c") == "'a b c'");

def test_formatSqlValueString4() -> None:
    assert(sql_utils.formatSqlValueString("a \"b\" c") == "'a \"b\" c'");    

def test_formatSqlValueString5() -> None:
    assert(sql_utils.formatSqlValueString("a 'b'\nc") == "'a ''b''\nc'");        

def test_formatSqlValue1() -> None:
    assert(sql_utils.formatSqlValue(2) == "2");        

def test_formatSqlValue2() -> None:
    assert(sql_utils.formatSqlValue(2.4) == "2.4");        

def test_formatSqlValue3() -> None:
    assert(sql_utils.formatSqlValue("AA") == "'AA'");        

def test_formatSqlValue4() -> None:
    assert(sql_utils.formatSqlValue(sql_utils.SqlField("aa")) == "AA");        

def test_formatSqlValue5() -> None:
    assert(sql_utils.formatSqlValue(0) == "0");        

def test_formatSqlValue6() -> None:
    dt = datetime.datetime(year=2023, month=1, day=12, hour=9, minute=59, second=12, microsecond=2344)
    assert(sql_utils.formatSqlValue(sql_utils.SqlDateTime(dt)) == "'2023-01-12T09:59:12.002'");        

def test_SqlConditionTrue() -> None:
    assert(str(sql_utils.SqlConditionTrue()) == "(1=1)");            

def test_SqlConditionFalse() -> None:
    assert(str(sql_utils.SqlConditionFalse()) == "(1=0)");                

def test_SqlConditionBool1() -> None:
    assert(str(sql_utils.SqlConditionBool(True)) == "(1=1)");            

def test_SqlConditionBool2() -> None:
    assert(str(sql_utils.SqlConditionBool(False)) == "(1=0)");            

def test_SqlConditionIsNull() -> None:
    cond = sql_utils.SqlConditionIsNull("AA");
    assert(str(cond) == "('AA' is null)");                

def test_SqlConditionIsNotNull() -> None:
    cond = sql_utils.SqlConditionIsNotNull("AA");
    assert(str(cond) == "('AA' is not null)");                

def test_SqlConditionNot() -> None:
    cond1 = sql_utils.SqlConditionIsNull("AA");
    cond = sql_utils.SqlConditionNot(cond1);
    assert(str(cond) == "(not ('AA' is null))");                

def test_SqlConditionStringStartsWith() -> None:
    cond = sql_utils.SqlConditionStringStartsWith("f", "a'an")
    assert(str(cond) == "(left(F, 4) = 'a''an')");                

def test_SqlConditionIn1() -> None:
    cond = sql_utils.SqlConditionIn(sql_utils.SqlField("f"), [])
    assert(str(cond) == "(1=0)");                

def test_SqlConditionIn2() -> None:
    cond = sql_utils.SqlConditionIn(sql_utils.SqlField("f"), ["a"])
    assert(str(cond) == "(F = 'a')");                

def test_SqlConditionIn3() -> None:
    cond = sql_utils.SqlConditionIn(sql_utils.SqlField("f"), ["a", "a'A", "b", "c"])
    assert(str(cond) == "(F in ('a', 'a''A', 'b', 'c'))");                

def test_SqlConditionStringNotEmpty1() -> None:
    cond = sql_utils.SqlConditionFieldStringNotEmpty("f")
    assert(str(cond) == "(F is not null and F != '')");                

def test_SqlConditionEq1() -> None:
    cond = sql_utils.SqlConditionEq("f1", None)
    assert(str(cond) == "('f1' is null)");                

def test_SqlConditionEq2() -> None:
    cond = sql_utils.SqlConditionEq(None, "f1")
    assert(str(cond) == "('f1' is null)");                

def test_SqlConditionEq3() -> None:
    cond = sql_utils.SqlConditionEq(sql_utils.SqlField("f1"), sql_utils.SqlField("f2"))
    assert(str(cond) == "(F1 = F2)");                

def test_SqlConditionEq4() -> None:
    cond = sql_utils.SqlConditionEq(sql_utils.SqlField("f1"), "aa'a")
    assert(str(cond) == "(F1 = 'aa''a')");                

def test_SqlConditionEq5() -> None:
    cond = sql_utils.SqlConditionEq(sql_utils.SqlField("f1"), 2)
    assert(str(cond) == "(F1 = 2)");                

def test_SqlConditionEq6() -> None:
    cond = sql_utils.SqlConditionEq(sql_utils.SqlField("f1"), True)
    assert(str(cond) == "(F1 = 1)");                

def test_SqlConditionEq7() -> None:
    cond = sql_utils.SqlConditionEq(sql_utils.SqlField("f1"), False)
    assert(str(cond) == "(F1 = 0 OR F1 is null)");                

def test_SqlConditionEq8() -> None:
    cond = sql_utils.SqlConditionEq(True, sql_utils.SqlField("f1"))
    assert(str(cond) == "(F1 = 1)");                

def test_SqlConditionEq9() -> None:
    cond = sql_utils.SqlConditionEq(False, sql_utils.SqlField("f1"))
    assert(str(cond) == "(F1 = 0 OR F1 is null)");                

def test_SqlConditionEq10() -> None:
    cond = sql_utils.SqlConditionEq(False, True)
    assert(str(cond) == "(1=0)");                

def test_SqlConditionEq11() -> None:
    cond = sql_utils.SqlConditionEq(True, True)
    assert(str(cond) == "(1=1)");                

def test_SqlConditionFieldEq1() -> None:
    cond = sql_utils.SqlConditionFieldEq("f1", None)
    assert(str(cond) == "(F1 is null)");                

def test_SqlConditionFieldEq2() -> None:
    cond = sql_utils.SqlConditionFieldEq("f1", sql_utils.SqlField("f2"))
    assert(str(cond) == "(F1 = F2)");                

def test_SqlConditionFieldEq3() -> None:
    cond = sql_utils.SqlConditionFieldEq("f1", "aa'a")
    assert(str(cond) == "(F1 = 'aa''a')");                

def test_SqlConditionFieldEq4() -> None:
    cond = sql_utils.SqlConditionFieldEq("f1", 2)
    assert(str(cond) == "(F1 = 2)");                

def test_SqlConditionFieldEq5() -> None:
    cond = sql_utils.SqlConditionFieldEq("f1", sql_utils.sqlParam)
    assert(str(cond) == "(F1 = ?)");                

def test_SqlConditionLt1() -> None:
    cond = sql_utils.SqlConditionLt(sql_utils.SqlField("f"), sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F < '20221212')");                

def test_SqlConditionLt2() -> None:
    cond = sql_utils.SqlConditionLt(2, sql_utils.SqlField("f"))
    assert(str(cond) == "(2 < F)");                

def test_SqlConditionGt1() -> None:
    cond = sql_utils.SqlConditionGt(sql_utils.SqlField("f"), sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F > '20221212')");                

def test_SqlConditionGt2() -> None:
    cond = sql_utils.SqlConditionGt(2, sql_utils.SqlField("f"))
    assert(str(cond) == "(2 > F)");                

def test_SqlConditionLe1() -> None:
    cond = sql_utils.SqlConditionLe(sql_utils.SqlField("f"), sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F <= '20221212')");                

def test_SqlConditionLe2() -> None:
    cond = sql_utils.SqlConditionLe(2, sql_utils.SqlField("f"))
    assert(str(cond) == "(2 <= F)");                

def test_SqlConditionGe1() -> None:
    cond = sql_utils.SqlConditionGe(sql_utils.SqlField("f"), sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F >= '20221212')");                

def test_SqlConditionGe2() -> None:
    cond = sql_utils.SqlConditionGe(2, sql_utils.SqlField("f"))
    assert(str(cond) == "(2 >= F)");                

def test_SqlConditionFieldLt1() -> None:
    cond = sql_utils.SqlConditionFieldLt("f", sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F < '20221212')");                

def test_SqlConditionFieldLe1() -> None:
    cond = sql_utils.SqlConditionFieldLe("f", sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F <= '20221212')");                

def test_SqlConditionFieldGt1() -> None:
    cond = sql_utils.SqlConditionFieldGt("f", sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F > '20221212')");                

def test_SqlConditionFieldGe1() -> None:
    cond = sql_utils.SqlConditionFieldGe("f", sql_utils.SqlDate(datetime.date(year=2022, month=12, day=12)))
    assert(str(cond) == "(F >= '20221212')");                


def test_SqlConditionAnd1() -> None:
    conj = sql_utils.SqlConditionAnd();
    assert(str(conj) == "(1=1)");                

def test_SqlConditionAnd2() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    conj = sql_utils.SqlConditionAnd();
    conj.addCondition(cond1)
    assert(str(conj) == "cond1");     

def test_SqlConditionAnd3() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    cond2 = sql_utils.SqlConditionPrepared("cond2");
    conj = sql_utils.SqlConditionAnd();
    conj.addCondition(cond1)
    conj.addCondition(cond2)
    assert(str(conj) == "(cond1 AND cond2)");     

def test_SqlConditionAnd4() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    cond2 = sql_utils.SqlConditionPrepared("cond2");
    cond3 = sql_utils.SqlConditionPrepared("cond3");
    conj = sql_utils.SqlConditionAnd();
    conj.addCondition(cond1)
    conj.addCondition(cond2)
    conj.addCondition(cond3)
    assert(str(conj) == "(cond1 AND cond2 AND cond3)");     


def test_SqlConditionOr1() -> None:
    conj = sql_utils.SqlConditionOr();
    assert(str(conj) == "(1=0)");                

def test_SqlConditionOr2() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    conj = sql_utils.SqlConditionOr();
    conj.addCondition(cond1)
    assert(str(conj) == "cond1");     

def test_SqlConditionOr3() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    cond2 = sql_utils.SqlConditionPrepared("cond2");
    conj = sql_utils.SqlConditionOr();
    conj.addCondition(cond1)
    conj.addCondition(cond2)
    assert(str(conj) == "(cond1 OR cond2)");     

def test_SqlConditionOr4() -> None:
    cond1 = sql_utils.SqlConditionPrepared("cond1");
    cond2 = sql_utils.SqlConditionPrepared("cond2");
    cond3 = sql_utils.SqlConditionPrepared("cond3");
    conj = sql_utils.SqlConditionOr();
    conj.addCondition(cond1)
    conj.addCondition(cond2)
    conj.addCondition(cond3)
    assert(str(conj) == "(cond1 OR cond2 OR cond3)");     

def test_SqlStatementSelect1() -> None:
    sql = sql_utils.SqlStatementSelect("tabelle t")
    assert (str(sql) == "SELECT * FROM tabelle t")

    sql.setTop(10)
    assert (str(sql) == "SELECT TOP 10 * FROM tabelle t")

    sql.addFields("f1")
    assert (str(sql) == "SELECT TOP 10 f1 FROM tabelle t")

    sql.addFields("f2", "f3")
    assert (str(sql) == "SELECT TOP 10 f1, f2, f3 FROM tabelle t")

    sql.addFieldsTable("t", "f4", "f5")
    assert (str(sql) == "SELECT TOP 10 f1, f2, f3, t.f4, t.f5 FROM tabelle t")

    sql.having.addConditionFieldGe("f1", 5)
    assert (str(sql) == "SELECT TOP 10 f1, f2, f3, t.f4, t.f5 FROM tabelle t")

    sql.addGroupBy("f1", "f2")
    assert (str(sql) == "SELECT TOP 10 f1, f2, f3, t.f4, t.f5 FROM tabelle t GROUP BY f1, f2 HAVING (F1 >= 5)")

    j = sql.addInnerJoin("tabelle2 t2")
    j.on.addConditionFieldsEq("t.f1", "t2.F1")
    assert (str(sql) == "SELECT TOP 10 f1, f2, f3, t.f4, t.f5 FROM tabelle t INNER JOIN tabelle2 t2 ON (T.F1 = T2.F1) GROUP BY f1, f2 HAVING (F1 >= 5)")


def test_SqlStatementSelect2() -> None:
    sql = sql_utils.SqlStatementSelect("t1")
    sql.addJoin("left join t2 on cond2")
    assert (str(sql) == "SELECT * FROM t1 left join t2 on cond2")

    sql.addJoin("left join t3 on cond3")
    assert (str(sql) == "SELECT * FROM t1 left join t2 on cond2 left join t3 on cond3")

def test_SqlStatementSelect4() -> None:
    sql = sql_utils.SqlStatementSelect("t")
    sql.where.addCondition("cond1")
    assert (str(sql) == "SELECT * FROM t WHERE (cond1)")

    sql.where.addCondition("cond2")
    assert (str(sql) == "SELECT * FROM t WHERE ((cond1) AND (cond2))")

def test_SqlStatementSelect5() -> None:
    sql = sql_utils.SqlStatementSelect("t")
    cond = sql_utils.SqlConditionOr();
    sql.where.addCondition(cond)
    cond.addCondition("cond1")
    assert (str(sql) == "SELECT * FROM t WHERE (cond1)")

    cond.addCondition("cond2")
    assert (str(sql) == "SELECT * FROM t WHERE ((cond1) OR (cond2))")

def test_SqlStatementSelect6() -> None:
    sql = sql_utils.SqlStatementSelect("t")
    sql.where = sql_utils.SqlConditionOr();
    sql.where.addCondition("cond1")
    assert (str(sql) == "SELECT * FROM t WHERE (cond1)")

    sql.where.addCondition("cond2")
    assert (str(sql) == "SELECT * FROM t WHERE ((cond1) OR (cond2))")
