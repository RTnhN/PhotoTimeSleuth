import os


class FormatError(Exception):
    pass


def load_names_and_bdays(bday_file):
    """Helper function to load names and birthdays from the bday file."""
    if not bday_file or not os.path.isfile(bday_file):
        return []

    names_and_bdays = []
    with open(bday_file, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            if "\t" not in line:
                raise FormatError(
                    "It looks like the bday file is not formatted correctly. Make sure each line has a tab between the name and the date."
                )
            name, bday = line.strip().split("\t")
            day, month, year = bday.split("-")
            if year < 1900 or year > 2100:
                raise FormatError(
                    "Invalid year in bday file. Make sure the year is between 1900 and 2100. Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            if month < 1 or month > 12:
                raise FormatError(
                    "Invalid month in bday file. Make sure the month is between 1 and 12. Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            if day < 1 or day > 31:
                raise FormatError(
                    "Invalid day in bday file. Make sure the day is between 1 and 31. Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            names_and_bdays.append({"name": name, "bday": bday})

    return names_and_bdays
