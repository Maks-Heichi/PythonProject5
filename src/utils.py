from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

OPERATIONS_FILENAME = "operations.xlsx"

DATE_COLUMN = "Дата операции"
AMOUNT_COLUMN = "Сумма операции"
CARD_COLUMN = "Номер карты"
CATEGORY_COLUMN = "Категория"
DESCRIPTION_COLUMN = "Описание"


@dataclass(frozen=True)
class UserSettings:
    currencies: Sequence[str]
    stocks: Sequence[str]


def load_operations() -> pd.DataFrame:
    """Load operations from an Excel file into a DataFrame."""
    excel_files = list(DATA_DIR.glob("*.xls*"))
    if excel_files:
        path = excel_files[0]
    else:
        path = DATA_DIR / OPERATIONS_FILENAME

        if not path.exists():
            msg = "Файл с операциями не найден в папке data (ожидался Excel-файл)."
            logger.error(msg)
            raise FileNotFoundError(msg)

    df = pd.read_excel(path)

    if DATE_COLUMN in df.columns:
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])

    return df


def load_user_settings(path: Path | None = None) -> UserSettings:
    """Загрузить пользовательские настройки (валюты и акции) из JSON file."""
    if path is None:
        path = PROJECT_ROOT / "user_settings.json"

    if not path.exists():
        logger.warning("Файл настроек пользователя не найден, используются значения по умолчанию.")
        return UserSettings(currencies=("USD", "EUR"), stocks=("AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"))

    with path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    currencies = data.get("user_currencies", [])
    stocks = data.get("user_stocks", [])

    return UserSettings(currencies=tuple(currencies), stocks=tuple(stocks))


def filter_by_period(
    df: pd.DataFrame,
    date_to: datetime,
    period: str = "M",
) -> pd.DataFrame:
    """Filter operations by period ending at date_to."""
    if DATE_COLUMN not in df.columns:
        return df

    if period == "ALL":
        mask = df[DATE_COLUMN] <= date_to
        return df.loc[mask].copy()

    if period == "W":
        week_start = date_to - pd.to_timedelta(date_to.weekday(), unit="D")
        week_end = week_start + pd.Timedelta(days=6)
        mask = (df[DATE_COLUMN] >= week_start) & (df[DATE_COLUMN] <= week_end)
        return df.loc[mask].copy()

    if period == "M":
        month_start = date_to.replace(day=1)
        mask = (df[DATE_COLUMN] >= month_start) & (df[DATE_COLUMN] <= date_to)
        return df.loc[mask].copy()

    if period == "Y":
        year_start = date_to.replace(month=1, day=1)
        mask = (df[DATE_COLUMN] >= year_start) & (df[DATE_COLUMN] <= date_to)
        return df.loc[mask].copy()

    logger.warning("Неизвестный период '%s', возвращаются все данные.", period)
    return df.copy()


def get_greeting(dt: datetime) -> str:
    """Приветствие в зависимости от времени суток."""
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def summarize_cards(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возврат средств за покупки по каждой карте и кэшбэк."""
    if CARD_COLUMN not in df.columns or AMOUNT_COLUMN not in df.columns:
        return []

    expenses = df[df[AMOUNT_COLUMN] < 0]
    expenses = expenses.copy()
    expenses["last_digits"] = expenses[CARD_COLUMN].astype(str).str[-4:]

    grouped = expenses.groupby("last_digits")[AMOUNT_COLUMN].sum().reset_index()

    result: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        total_spent = float(abs(row[AMOUNT_COLUMN]))
        cashback = round(total_spent / 100.0, 2)
        result.append(
            {
                "last_digits": str(row["last_digits"]),
                "total_spent": round(total_spent, 2),
                "cashback": cashback,
            }
        )

    return result


def top_transactions(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """Самых крупных транзакций по сумме."""
    required = {DATE_COLUMN, AMOUNT_COLUMN, CATEGORY_COLUMN, DESCRIPTION_COLUMN}
    if not required.issubset(df.columns):
        return []

    tmp = df.copy()
    tmp["abs_amount"] = tmp[AMOUNT_COLUMN].abs()
    top = tmp.nlargest(n, "abs_amount")

    result: List[Dict[str, Any]] = []
    for _, row in top.iterrows():
        date_val = row[DATE_COLUMN]
        if isinstance(date_val, (datetime, pd.Timestamp)):
            date_str = date_val.strftime("%d.%m.%Y")
        else:
            date_str = str(date_val)
        result.append(
            {
                "date": date_str,
                "amount": float(row[AMOUNT_COLUMN]),
                "category": str(row[CATEGORY_COLUMN]),
                "description": str(row[DESCRIPTION_COLUMN]),
            }
        )
    return result


def _request_json(url: str, params: Dict[str, Any] | None = None) -> Any:
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Ошибка при запросе %s: %s", url, exc)
        return None


def get_currency_rates(codes: Iterable[str]) -> List[Dict[str, Any]]:
    """API."""
    base_url = "https://api.apilayer.com/exchangerates_data/convert?to={to}&from=RUB&amount={amount}"
    currencies = ",".join(codes)
    data = _request_json(base_url, params={"base": "RUB", "symbols": currencies})

    if not data or "rates" not in data:
        return []

    rates = data["rates"]
    result: List[Dict[str, Any]] = []
    for code in codes:
        rate = rates.get(code)
        if rate is None:
            continue
        result.append({"currency": code, "rate": round(float(1 / rate), 2)})
    return result


def get_stock_prices(tickers: Iterable[str]) -> List[Dict[str, Any]]:
    """Узнайте цены на акции с помощью API."""
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        logger.warning("ALPHAVANTAGE_API_KEY не задан, цены акций возвращаются пустыми.")
        return []

    base_url = "https://api.apilayer.com/exchangerates_data/convert?to={to}&from=RUB&amount={amount}"
    result: List[Dict[str, Any]] = []

    for ticker in tickers:
        params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key}
        data = _request_json(base_url, params=params)
        if not data:
            continue
        quote = data.get("Global Quote") or data.get("GlobalQuote")
        if not quote:
            continue
        price_str = quote.get("05. price") or quote.get("price")
        if not price_str:
            continue
        try:
            price = round(float(price_str), 2)
        except ValueError:
            continue
        result.append({"stock": ticker, "price": price})

    return result
