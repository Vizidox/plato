from datetime import datetime
from typing import Union

from babel import dates
from num2words import num2words


def format_dates(date_str: str, format='d MMMM yyyy') -> str:
    date = datetime.fromisoformat(date_str)
    return dates.format_datetime(date, format)


def ordinal_day_of_month_year(date_str: str) -> str:
    """

    Args:
        date_str:

    Returns:

    """
    date = datetime.fromisoformat(date_str)
    return f'{num_to_ordinal(date.day)} of {format_month(date)} {format_year(date)}'


def format_year(date: datetime) -> str:
    return dates.format_datetime(date, 'yyyy')


def format_month(date: datetime) -> str:
    return dates.format_datetime(date, 'MMMM')


def num_to_ordinal(number: Union[int, str]) -> str:
    """
    Formats a given cardinal number into an ordinal number.
    For example:
    - num_to_ordinal(1) -> 1st
    - num_to_ordinal(3) -> 3rd
    - num_to_ordinal(10) -> 10th

    Args:
        number: A cardinal number in string format

    Returns: The number in ordinal format, also as a string
    """
    return num2words(number, to='ordinal_num')
