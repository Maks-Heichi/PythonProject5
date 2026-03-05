from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from src import utils

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def save_report(filename: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор, сохраняющий результат функции-отчёта в файл JSON."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            REPORTS_DIR.mkdir(exist_ok=True)

            if filename is None:
                name = f"{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                name = filename

            path = REPORTS_DIR / name

            try:
                with path.open("w", encoding="utf-8") as f:
                    if isinstance(result, pd.DataFrame):
                        json.dump(result.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=2)
            except OSError as exc:
                logger.error("Не удалось сохранить отчёт в %s: %s", path, exc)

            return result

        return wrapper

    return decorator


@save_report()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Траты по категории за последний месяц."""
    if date is None:
        end_date = datetime.today()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - pd.DateOffset(months=1)

    df = transactions.copy()
    if utils.DATE_COLUMN in df.columns:
        df[utils.DATE_COLUMN] = pd.to_datetime(df[utils.DATE_COLUMN])

    mask = (
        (df[utils.DATE_COLUMN] >= start_date)
        & (df[utils.DATE_COLUMN] <= end_date)
        & (df[utils.CATEGORY_COLUMN] == category)
        & (df[utils.AMOUNT_COLUMN] < 0)
    )
    filtered = df.loc[mask].copy()

    return filtered


@save_report()
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Средние траты по дням недели за последний месяц."""
    if date is None:
        end_date = datetime.today()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - pd.DateOffset(months=1)

    df = transactions.copy()
    if utils.DATE_COLUMN in df.columns:
        df[utils.DATE_COLUMN] = pd.to_datetime(df[utils.DATE_COLUMN])

    mask = (df[utils.DATE_COLUMN] >= start_date) & (df[utils.DATE_COLUMN] <= end_date) & (df[utils.AMOUNT_COLUMN] < 0)
    df = df.loc[mask].copy()
    if df.empty:
        return df

    df["weekday"] = df[utils.DATE_COLUMN].dt.day_name()
    grouped = (
        df.groupby("weekday")[utils.AMOUNT_COLUMN]
        .mean()
        .abs()
        .reset_index()
        .rename(columns={utils.AMOUNT_COLUMN: "average_spent"})
    )

    return grouped


@save_report()
def spending_by_workday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """Средние траты в рабочие и выходные дни."""
    if date is None:
        end_date = datetime.today()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    start_date = end_date - pd.DateOffset(months=1)

    df = transactions.copy()
    if utils.DATE_COLUMN in df.columns:
        df[utils.DATE_COLUMN] = pd.to_datetime(df[utils.DATE_COLUMN])

    mask = (df[utils.DATE_COLUMN] >= start_date) & (df[utils.DATE_COLUMN] <= end_date) & (df[utils.AMOUNT_COLUMN] < 0)
    df = df.loc[mask].copy()
    if df.empty:
        return df

    df["is_workday"] = df[utils.DATE_COLUMN].dt.weekday < 5

    grouped = (
        df.groupby("is_workday")[utils.AMOUNT_COLUMN]
        .mean()
        .abs()
        .reset_index()
        .rename(columns={utils.AMOUNT_COLUMN: "average_spent"})
    )

    return grouped
