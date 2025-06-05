from datetime import datetime, timedelta

SEASON_MAP = {
    "spring": 3,
    "summer": 6,
    "fall": 9,
    "winter": 12,
}


def calculate_date(bday, age, season):
    try:
        birthday = datetime.strptime(bday, "%Y-%m-%d")
        estimated_date = birthday + timedelta(days=age * 365.25)
        if season == "birthday":
            return estimated_date.strftime("%Y-%m-%d")
        if season == "christmas":
            return find_closest_season_date(estimated_date, 12, 25)
        season_month = SEASON_MAP[season]
        return find_closest_season_date(estimated_date, season_month, 1)
    except ValueError:
        return None


def find_closest_season_date(estimated_date, month, day):
    same_year_date = estimated_date.replace(month=month, day=day)
    previous_year_date = same_year_date.replace(year=same_year_date.year - 1)
    next_year_date = same_year_date.replace(year=same_year_date.year + 1)

    closest_season_date = min(
        [same_year_date, previous_year_date, next_year_date],
        key=lambda d: abs((d - estimated_date).days),
    )
    closest_season_date = closest_season_date.replace(day=day)
    return closest_season_date.strftime("%Y-%m-%d")
