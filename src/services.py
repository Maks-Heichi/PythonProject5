from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

DATE_KEY = "Дата операции"
AMOUNT_KEY = "Сумма операции"
CATEGORY_KEY = "Категория"
DESCRIPTION_KEY = "Описание"


def profitable_categories(data: Iterable[Dict[str, Any]], year: int, month: int) -> Dict[str, float]:
    """Анализ выгодных категорий повышенного кешбэка за месяц."""
    result: Dict[str, float] = {}
    for row in data:
        date_raw = row.get(DATE_KEY)
        amount = row.get(AMOUNT_KEY)
        category = row.get(CATEGORY_KEY)

        if category is None or amount is None or not isinstance(amount, (int, float)):
            continue

        try:
            date = (
                datetime.strptime(date_raw, "%Y-%m-%d")
                if isinstance(date_raw, str)
                else datetime.fromisoformat(str(date_raw))
            )
        except (TypeError, ValueError):
            continue

        if date.year != year or date.month != month:
            continue

        if amount < 0:
            cashback = abs(amount) * 0.05
        else:
            cashback = 0.0

        result[category] = result.get(category, 0.0) + cashback

    return {k: round(v, 2) for k, v in result.items()}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Инвестокопилка через округление трат."""
    total_saved = 0.0

    for tx in transactions:
        date_str = tx.get(DATE_KEY)
        amount = tx.get(AMOUNT_KEY)

        if not isinstance(date_str, str) or not isinstance(amount, (int, float)):
            continue

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        if date.strftime("%Y-%m") != month:
            continue

        if amount >= 0:
            continue

        spend = abs(amount)
        rounded = ((spend + limit - 1) // limit) * limit
        saved = rounded - spend
        total_saved += saved

    return round(total_saved, 2)


def simple_search(transactions: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """Простой поиск по описанию и категории."""
    query_lower = query.lower()
    results: List[Dict[str, Any]] = []

    for tx in transactions:
        desc = str(tx.get(DESCRIPTION_KEY, "")).lower()
        cat = str(tx.get(CATEGORY_KEY, "")).lower()
        if query_lower in desc or query_lower in cat:
            results.append(tx)

    return {"results": results}


PHONE_PATTERN = re.compile(r"(?:\+7|8)\s?\d{3}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}")


def find_phone_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Поиск транзакций с мобильными номерами в описании."""
    results = []
    for tx in transactions:
        desc = str(tx.get(DESCRIPTION_KEY, ""))
        if PHONE_PATTERN.search(desc):
            results.append(tx)
    return {"results": results}


PERSON_TRANSFER_PATTERN = re.compile(r"\b[А-ЯЁ][а-яё]+ [А-ЯЁ]\.\b")


def find_person_transfers(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Поиск переводов физическим лицам."""
    results = []
    for tx in transactions:
        category = str(tx.get(CATEGORY_KEY, ""))
        desc = str(tx.get(DESCRIPTION_KEY, ""))
        if category == "Переводы" and PERSON_TRANSFER_PATTERN.search(desc):
            results.append(tx)
    return {"results": results}
