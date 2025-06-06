import os


class FormatError(Exception):
    pass


def _key_file_path(bday_file):
    """Return the path of the API key file based on the bday file path."""
    directory = os.path.dirname(bday_file)
    return os.path.join(directory, "openai_key.txt")


def load_names_and_bdays(bday_file):
    """Helper function to load names and birthdays from the bday file."""
    if not bday_file or not os.path.isfile(bday_file):
        return []

    names_and_bdays = []
    with open(bday_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or len(line.strip()) == 0:
                continue
            if "\t" not in line:
                raise FormatError(
                    "It looks like the bday file is not formatted correctly. \
                     Make sure each line has a tab between the name and the date."
                )
            name, bday = line.strip().split("\t")
            year, month, day = map(int, bday.split("-"))
            if year < 1900 or year > 2100:
                raise FormatError(
                    f"Invalid year in bday file. \
                      Make sure the year ({year}) is between 1900 and 2100. \
                      Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            if month < 1 or month > 12:
                raise FormatError(
                    f"Invalid month in bday file. \
                      Make sure the month ({month}) is between 1 and 12. \
                      Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            if day < 1 or day > 31:
                raise FormatError(
                    f"Invalid day in bday file. \
                      Make sure the day({day}) is between 1 and 31. \
                      Also make sure that the order is correct (e.g. YYYY-MM-DD)."
                )
            names_and_bdays.append({"name": name, "bday": bday})

    return names_and_bdays


def load_api_key(bday_file):
    """Load the stored OpenAI API key if available."""
    key_path = _key_file_path(bday_file)
    if os.path.isfile(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    return None


def save_api_key(bday_file, api_key):
    """Persist the OpenAI API key next to the birthday file."""
    key_path = _key_file_path(bday_file)
    with open(key_path, "w", encoding="utf-8") as f:
        f.write(api_key.strip())
