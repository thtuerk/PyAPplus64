# Copyright (c) 2023 Thomas Tuerk (kontakt@thomas-tuerk.de)
#
# This file is part of PyAPplus64 (see https://www.thomas-tuerk.de/de/pyapplus64).
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from PyAPplus64 import applus_db
import datetime

def test_DBTableIDs1() -> None:
    ids = applus_db.DBTableIDs();
    assert (str(ids) == "{}")
    ids.add("t1", 1)
    assert (str(ids) == "{'T1': {1}}")
    ids.add("t1", 2,3,4)
    assert (str(ids) == "{'T1': {1, 2, 3, 4}}")
    assert (ids.getTable("T1") == {1, 2, 3, 4})
    assert (ids.getTable("T2") == set())
    ids.add("t2", 2,3,4)
    assert (ids.getTable("T2") == {2,3,4})
    assert (str(ids) == "{'T1': {1, 2, 3, 4}, 'T2': {2, 3, 4}}")
