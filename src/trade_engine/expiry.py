from __future__ import annotations

import datetime
from typing import Optional
from src.models.trade_context import ExpiryContext


def analyze_expiry(
    expiry_date: datetime.date | str,
    today_date: Optional[datetime.date] = None,
    current_monthly_expiry: Optional[datetime.date | str] = None,
) -> ExpiryContext:
    """
    Classifies the expiry of a NIFTY options contract.
    """
    if today_date is None:
        today_date = datetime.date.today()

    if isinstance(expiry_date, str):
        try:
            exp_date_obj = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            exp_date_obj = datetime.datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%S").date()
    else:
        exp_date_obj = expiry_date

    days_remaining = (exp_date_obj - today_date).days

    # Identify if Monthly or Weekly Expiry
    is_monthly = False
    if current_monthly_expiry:
        if isinstance(current_monthly_expiry, str):
            try:
                mon_exp_obj = datetime.datetime.strptime(current_monthly_expiry, "%Y-%m-%d").date()
            except ValueError:
                mon_exp_obj = datetime.datetime.strptime(current_monthly_expiry, "%Y-%m-%dT%H:%M:%S").date()
        else:
            mon_exp_obj = current_monthly_expiry
        is_monthly = (exp_date_obj == mon_exp_obj)
    else:
        # Standard calculation: is it the last Thursday of its calendar month?
        year = exp_date_obj.year
        month = exp_date_obj.month
        # Find last day of current month
        if month == 12:
            next_month_start = datetime.date(year + 1, 1, 1)
        else:
            next_month_start = datetime.date(year, month + 1, 1)
        last_day = next_month_start - datetime.timedelta(days=1)
        
        while last_day.weekday() != 3:  # 3 is Thursday (Mon=0, Tue=1, Wed=2, Thu=3)
            last_day -= datetime.timedelta(days=1)
        is_monthly = (exp_date_obj == last_day)

    expiry_type = "MONTHLY" if is_monthly else "WEEKLY"

    is_expiry_day = (days_remaining == 0)
    is_expiry_eve = (days_remaining == 1)
    is_far_expiry = (days_remaining > 7)

    # Classification priority:
    if is_expiry_day:
        classification = "EXPIRY_DAY"
    elif is_expiry_eve:
        classification = "EXPIRY_EVE"
    elif is_far_expiry:
        classification = "FAR_EXPIRY"
    elif is_monthly:
        classification = "MONTHLY_EXPIRY"
    else:
        classification = "WEEKLY_EXPIRY"

    return ExpiryContext(
        expiry_date=exp_date_obj.strftime("%Y-%m-%d"),
        days_remaining=max(0, days_remaining),
        expiry_type=expiry_type,
        is_expiry_day=is_expiry_day,
        is_expiry_eve=is_expiry_eve,
        is_far_expiry=is_far_expiry,
        classification=classification,
    )
