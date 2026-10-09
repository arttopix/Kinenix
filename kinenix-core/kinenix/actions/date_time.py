import calendar
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext

# English names, independent of the machine's locale, so a flow behaves the same on every worker
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December")
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

SNAP_OPTIONS = ("start_of_month", "end_of_month", "start_of_year", "end_of_year", "start_of_week", "end_of_week")


def _now() -> datetime:
    """The current local time; tests replace it to get a fixed date."""
    return datetime.now()


def _parse(value: Any, input_format: Optional[str]) -> datetime:
    if value is None or str(value).strip().lower() in ("", "today"):
        current = _now()
        return datetime(current.year, current.month, current.day)
    if str(value).strip().lower() == "now":
        return _now().replace(microsecond=0)
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    if input_format:
        try:
            return datetime.strptime(text, input_format)
        except ValueError as exc:
            raise ValueError(f"date.calc could not read date '{text}' with input_format '{input_format}': {exc}") from exc
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"date.calc could not read date '{text}'. Use 'today', 'now', an ISO date such as "
                         f"2026-10-08, or set input_format (for example '%d/%m/%Y').") from exc


def _add_months(value: datetime, months: int) -> datetime:
    # Keeps the day where possible and clamps it to the target month: 31 March minus 1 month is 28 or 29 February
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _snap(value: datetime, snap: str) -> datetime:
    if snap == "start_of_month":
        return value.replace(day=1)
    if snap == "end_of_month":
        return value.replace(day=calendar.monthrange(value.year, value.month)[1])
    if snap == "start_of_year":
        return value.replace(month=1, day=1)
    if snap == "end_of_year":
        return value.replace(month=12, day=31)
    if snap == "start_of_week":
        return value - timedelta(days=value.weekday())
    if snap == "end_of_week":
        return value + timedelta(days=6 - value.weekday())
    raise ValueError(f"date.calc snap must be one of {', '.join(SNAP_OPTIONS)}; got '{snap}'.")


def _int_parameter(parameters: Dict[str, Any], name: str) -> int:
    value = parameters.get(name)
    if value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"date.calc parameter '{name}' must be a whole number; got '{value}'.") from exc


@register_action("date.calc")
class DateCalcAction(BaseAction):
    """
    Works out a date (today by default), optionally shifted and snapped to the start or end of a period,
    and returns its parts so later steps can use ${var.year}, ${var.month_name}, ${var.text}, and so on.
    """
    accepted_parameters = ('date', 'input_format', 'add_days', 'add_weeks', 'add_months', 'add_years',
                           'snap', 'format')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        value = _parse(parameters.get("date"), parameters.get("input_format"))

        value = _add_months(value, _int_parameter(parameters, "add_years") * 12 + _int_parameter(parameters, "add_months"))
        value += timedelta(days=_int_parameter(parameters, "add_weeks") * 7 + _int_parameter(parameters, "add_days"))

        snap = parameters.get("snap")
        if snap:
            value = _snap(value, str(snap).strip())

        output_format = parameters.get("format") or "%Y-%m-%d"
        return {
            "text": value.strftime(str(output_format)),
            "date": value.strftime("%Y-%m-%d"),
            "datetime": value.isoformat(),
            "year": value.year,
            "month": value.month,
            "day": value.day,
            "month_name": MONTH_NAMES[value.month - 1],
            "month_abbr": MONTH_NAMES[value.month - 1][:3],
            "weekday": WEEKDAY_NAMES[value.weekday()],
            "weekday_number": value.isoweekday(),
            "days_in_month": calendar.monthrange(value.year, value.month)[1],
            "hour": value.hour,
            "minute": value.minute,
        }
