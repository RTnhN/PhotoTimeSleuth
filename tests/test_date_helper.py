import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from PhotoTimeSleuth.Helpers.date_helper import calculate_date


def test_calculate_date_birthday():
    assert calculate_date("2000-05-10", 5, "birthday") == "2005-05-10"


def test_calculate_date_christmas():
    assert calculate_date("2010-06-15", 3, "christmas") == "2012-12-25"


def test_calculate_date_invalid_bday():
    assert calculate_date("not-a-date", 2, "summer") is None
