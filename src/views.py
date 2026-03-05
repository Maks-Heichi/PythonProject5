from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from . import utils

logger = logging.getLogger(__name__)


def build_main_page_context(dt_str: str) -> Dict[str, Any]:
    """Сформировать JSON-ответ для страницы «Главная» по входной дате-времени."""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    settings = utils.load_user_settings()
    df = utils.load_operations()
    df_period = utils.filter_by_period(df, dt, period="M")

    greeting = utils.get_greeting(dt)
    cards = utils.summarize_cards(df_period)
    top = utils.top_transactions(df_period, n=5)

    currency_rates = utils.get_currency_rates(settings.currencies)
    stock_prices = utils.get_stock_prices(settings.stocks)

    return {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }


def build_events_page_context_from_df(
    df: pd.DataFrame,
    date_str: str,
    period: str = "M",
) -> Dict[str, Any]:
    """Сформировать JSON-ответ для страницы «События» по уже загруженному DataFrame."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    settings = utils.load_user_settings()

    df_period = utils.filter_by_period(df, dt, period=period)

    expenses_df = df_period[df_period[utils.AMOUNT_COLUMN] < 0].copy()
    income_df = df_period[df_period[utils.AMOUNT_COLUMN] > 0].copy()

    result: Dict[str, Any] = {}

    if not expenses_df.empty:
        expenses_df["abs_amount"] = expenses_df[utils.AMOUNT_COLUMN].abs()
        total_expenses = int(round(expenses_df["abs_amount"].sum()))

        main_expenses = (
            expenses_df.groupby(utils.CATEGORY_COLUMN)["abs_amount"].sum().sort_values(ascending=False).reset_index()
        )

        top_main = main_expenses.head(7)
        other_sum = main_expenses["abs_amount"].iloc[7:].sum()

        main_list = [
            {"category": str(row[utils.CATEGORY_COLUMN]), "amount": int(round(row["abs_amount"]))}
            for _, row in top_main.iterrows()
        ]
        if other_sum > 0:
            main_list.append({"category": "Остальное", "amount": int(round(other_sum))})

        transfers_cash = (
            expenses_df[expenses_df[utils.CATEGORY_COLUMN].isin(["Наличные", "Переводы"])]
            .groupby(utils.CATEGORY_COLUMN)["abs_amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        transfers_cash_list = [
            {"category": str(row[utils.CATEGORY_COLUMN]), "amount": int(round(row["abs_amount"]))}
            for _, row in transfers_cash.iterrows()
        ]

        result["expenses"] = {
            "total_amount": total_expenses,
            "main": main_list,
            "transfers_and_cash": transfers_cash_list,
        }
    else:
        result["expenses"] = {"total_amount": 0, "main": [], "transfers_and_cash": []}

    if not income_df.empty:
        total_income = int(round(income_df[utils.AMOUNT_COLUMN].sum()))
        main_income = (
            income_df.groupby(utils.CATEGORY_COLUMN)[utils.AMOUNT_COLUMN]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        main_income_list = [
            {"category": str(row[utils.CATEGORY_COLUMN]), "amount": int(round(row[utils.AMOUNT_COLUMN]))}
            for _, row in main_income.iterrows()
        ]
        result["income"] = {"total_amount": total_income, "main": main_income_list}
    else:
        result["income"] = {"total_amount": 0, "main": []}

    currency_rates = utils.get_currency_rates(settings.currencies)
    stock_prices = utils.get_stock_prices(settings.stocks)

    result["currency_rates"] = currency_rates
    result["stock_prices"] = stock_prices

    return result


def build_events_page_context(date_str: str, period: str = "M") -> Dict[str, Any]:
    """Обёртка для страницы «События», самостоятельно загружающая DataFrame из Excel."""
    df = utils.load_operations()
    return build_events_page_context_from_df(df, date_str=date_str, period=period)
