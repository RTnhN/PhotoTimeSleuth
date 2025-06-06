import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from PhotoTimeSleuth.Helpers.file_helper import load_names_and_bdays, FormatError


def test_load_names_and_bdays_basic(tmp_path):
    content = "# comment\nJohn\t2000-01-01\nJane\t1999-12-31\n"
    file_path = tmp_path / "bdays.txt"
    file_path.write_text(content)
    result = load_names_and_bdays(str(file_path))
    assert result == [
        {"name": "John", "bday": "2000-01-01"},
        {"name": "Jane", "bday": "1999-12-31"},
    ]


def test_load_names_and_bdays_bad_format(tmp_path):
    file_path = tmp_path / "bdays.txt"
    file_path.write_text("John 2000-01-01\n")
    with pytest.raises(FormatError):
        load_names_and_bdays(str(file_path))


def test_load_names_and_bdays_invalid_year(tmp_path):
    file_path = tmp_path / "bdays.txt"
    file_path.write_text("John\t1800-01-01\n")
    with pytest.raises(FormatError):
        load_names_and_bdays(str(file_path))
